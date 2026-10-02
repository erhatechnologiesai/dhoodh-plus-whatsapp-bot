const express = require('express');
const cors = require('cors');
const QRCode = require('qrcode');
const pino = require('pino');
const path = require('path');
const fs = require('fs');
const Redis = require('ioredis');
const {
  default: makeWASocket,
  useMultiFileAuthState,
  DisconnectReason,
  fetchLatestBaileysVersion,
  makeCacheableSignalKeyStore,
  downloadContentFromMessage,
  downloadMediaMessage
} = require('@whiskeysockets/baileys');

const app = express();
app.use(cors());
app.use(express.json());

const PORT = process.env.PORT || 3001;
const AUTH_DIR = process.env.AUTH_DIR || path.join(__dirname, 'auth_info_baileys');
let BACKEND_URL = process.env.BACKEND_API_URL || 'http://localhost:8000';
if (!BACKEND_URL.startsWith('http://') && !BACKEND_URL.startsWith('https://')) {
  BACKEND_URL = `http://${BACKEND_URL}`;
}
BACKEND_URL = BACKEND_URL.replace(/\/+$/, '');

// Optional Redis Client
let redis = null;
if (process.env.REDIS_URL) {
  try {
    redis = new Redis(process.env.REDIS_URL, {
      maxRetriesPerRequest: 1,
      retryStrategy: (times) => Math.min(times * 1000, 5000),
      enableOfflineQueue: false
    });
    redis.on('connect', () => console.log('[WhatsApp Gateway] Redis connected!'));
    redis.on('error', (err) => console.log('[WhatsApp Gateway] Redis notice:', err.message));
  } catch (e) {
    console.log('[WhatsApp Gateway] Redis initialization notice:', e.message);
  }
}

function updateRedisStatus(status, user) {
  if (!redis) return;
  try {
    redis.set('whatsapp:gateway:status', JSON.stringify({
      status,
      connected: status === 'connected',
      phone: user,
      updated_at: new Date().toISOString()
    }), 'EX', 120);
  } catch (e) {}
}

// State tracking & Socket Lifecycle
let sock = null;
let reconnectTimer = null;
let isStarting = false;
let isExplicitlyClosing = false;
let consecutiveReplacements = 0;

let currentQR = null;
let currentQRImage = null;
let currentPairingCode = null;
let connectionStatus = 'initializing'; // initializing, qr_ready, connecting, connected, logged_out
let connectedUser = null;
let pairPhone = '';

process.on('SIGINT', () => console.log('[WhatsApp Gateway] Received SIGINT'));
process.on('SIGTERM', () => console.log('[WhatsApp Gateway] Received SIGTERM'));
process.on('beforeExit', (code) => console.log('[WhatsApp Gateway] Process beforeExit event with code:', code));
process.on('exit', (code) => console.log('[WhatsApp Gateway] Process exit event with code:', code));

const logger = pino({ level: 'silent' });

function clearAuthFiles() {
  try {
    if (fs.existsSync(AUTH_DIR)) {
      const files = fs.readdirSync(AUTH_DIR);
      for (const file of files) {
        try {
          fs.rmSync(path.join(AUTH_DIR, file), { recursive: true, force: true });
        } catch (err) {}
      }
      console.log(`[WhatsApp Gateway] Successfully cleaned ${files.length} auth files from ${AUTH_DIR}`);
    }
  } catch (e) {
    console.error('Failed to clean auth dir files:', e.message);
  }
}

function cleanupSocket() {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  if (sock) {
    isExplicitlyClosing = true;
    try {
      sock.ev.removeAllListeners();
      if (sock.ws) {
        try { sock.ws.close(); } catch (e) {}
      }
      try { sock.end(undefined); } catch (e) {}
    } catch (e) {}
    sock = null;
    isExplicitlyClosing = false;
  }
}

function scheduleReconnect(delayMs, reason) {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  console.log(`[WhatsApp Gateway] Scheduling reconnect in ${delayMs}ms (Reason: ${reason})...`);
  connectionStatus = 'connecting';
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    startWhatsAppGateway();
  }, delayMs);
}

async function startWhatsAppGateway() {
  if (isStarting) {
    console.log('[WhatsApp Gateway] Connection initialization already in progress. Skipping redundant call.');
    return;
  }
  isStarting = true;

  try {
    cleanupSocket();

    if (!fs.existsSync(AUTH_DIR)) {
      fs.mkdirSync(AUTH_DIR, { recursive: true });
    }

    // Validate integrity of creds.json to prevent corrupted 0-byte crashes
    const credsPath = path.join(AUTH_DIR, 'creds.json');
    if (fs.existsSync(credsPath)) {
      try {
        const stats = fs.statSync(credsPath);
        if (stats.size === 0) {
          console.warn('[WhatsApp Gateway] creds.json is 0 bytes (corrupted). Purging auth directory...');
          clearAuthFiles();
        } else {
          const raw = fs.readFileSync(credsPath, 'utf8');
          JSON.parse(raw);
        }
      } catch (err) {
        console.warn('[WhatsApp Gateway] creds.json contains invalid JSON. Purging auth directory...', err.message);
        clearAuthFiles();
      }
    }

    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const { version, isLatest } = await fetchLatestBaileysVersion();

    console.log(`[WhatsApp Gateway] Starting Baileys v${version.join('.')} (Latest: ${isLatest})...`);

    const currentSocket = makeWASocket({
      version,
      logger,
      printQRInTerminal: false,
      auth: {
        creds: state.creds,
        keys: makeCacheableSignalKeyStore(state.keys, logger)
      },
      browser: ['Dhoodh Plus AI', 'Chrome', '120.0.0'],
      generateHighQualityLinkPreview: false,
      syncFullHistory: false,
      defaultQueryTimeoutMs: 60000,
      connectTimeoutMs: 60000,
      keepAliveIntervalMs: 25000,
      retryRequestDelayMs: 500
    });

    sock = currentSocket;

    currentSocket.ev.on('creds.update', saveCreds);

    currentSocket.ev.on('connection.update', async (update) => {
      // Guard: Ignore callbacks if socket was closed or replaced
      if (sock !== currentSocket || isExplicitlyClosing) return;

      const { connection, lastDisconnect, qr } = update;

      if (qr) {
        currentQR = qr;
        try {
          currentQRImage = await QRCode.toDataURL(qr);
        } catch (err) {
          console.error('[WhatsApp Gateway] QR image gen failed:', err);
        }
        connectionStatus = 'qr_ready';
        console.log('[WhatsApp Gateway] New Live QR Code Generated!');
      }

      if (connection === 'close') {
        const statusCode = lastDisconnect?.error?.output?.statusCode;
        console.log(`[WhatsApp Gateway] Connection closed (code: ${statusCode}).`);

        connectionStatus = 'connecting';
        currentQR = null;
        currentQRImage = null;
        currentPairingCode = null;
        connectedUser = null;
        updateRedisStatus('disconnected', null);

        // Notify backend about disconnect
        try {
          fetch(`${BACKEND_URL}/api/whatsapp/connect/disconnect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
          }).catch(() => {});
        } catch (disErr) {}

        // 1. User logged out or revoked session
        if (statusCode === DisconnectReason.loggedOut || statusCode === 401) {
          console.log('[WhatsApp Gateway] User logged out. Clearing auth credentials...');
          clearAuthFiles();
          consecutiveReplacements = 0;
          scheduleReconnect(1200, 'loggedOut');
          return;
        }

        // 2. Connection replaced (440)
        if (statusCode === DisconnectReason.connectionReplaced || statusCode === 440) {
          consecutiveReplacements++;
          console.warn(`[WhatsApp Gateway] Connection replaced by another session/device (Event #${consecutiveReplacements}).`);
          if (consecutiveReplacements >= 3) {
            console.warn('[WhatsApp Gateway] Backing off for 35s to prevent infinite reconnect loop...');
            scheduleReconnect(35000, 'connectionReplaced-backoff');
          } else {
            scheduleReconnect(6000, 'connectionReplaced');
          }
          return;
        }

        // 3. Restart required, timed out, or network glitch
        consecutiveReplacements = 0;
        scheduleReconnect(3000, `code-${statusCode || 'network'}`);
      } else if (connection === 'open') {
        console.log('[WhatsApp Gateway] WhatsApp connected successfully!');
        connectionStatus = 'connected';
        consecutiveReplacements = 0;
        currentQR = null;
        currentQRImage = null;
        currentPairingCode = null;
        connectedUser = currentSocket.user ? currentSocket.user.id.split(':')[0] : 'Connected';
        console.log(`[WhatsApp Gateway] Linked to phone: +${connectedUser}`);
        updateRedisStatus('connected', connectedUser);

        // Notify backend about the connection and auto-reset data if new number connects
        try {
          fetch(`${BACKEND_URL}/api/whatsapp/connect/on-connected`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: connectedUser, name: 'Official WhatsApp Device' })
          }).then(res => res.json()).then(data => {
            console.log('[WhatsApp Gateway] Backend on-connected response:', data);
          }).catch(err => {
            console.warn('[WhatsApp Gateway] Could not notify backend:', err.message);
          });
        } catch (syncErr) {}
      }
    });

    // Handle incoming messages
    currentSocket.ev.on('messages.upsert', async (chatUpdate) => {
      try {
        if (sock !== currentSocket) return;
        const messages = chatUpdate.messages;
        if (!messages || messages.length === 0) return;

        for (const m of messages) {
          if (m.key.fromMe) continue;
          if (m.key.remoteJid === 'status@broadcast') continue;

          // Redis distributed deduplication
          if (redis && m.key?.id) {
            try {
              const setOk = await redis.set(`whatsapp:gateway:dedup:${m.key.id}`, '1', 'EX', 86400, 'NX');
              if (!setOk) {
                console.log(`[WhatsApp Gateway] Duplicate message skipped by Redis cache: ${m.key.id}`);
                continue;
              }
            } catch (rErr) {}
          }

          const senderJid = m.key.remoteJid;
          const senderPhone = senderJid.split('@')[0];
          const pushName = m.pushName || 'Customer';

          // Maintain reverse mapping for proper @lid vs @s.whatsapp.net routing
          if (!global.jidMap) global.jidMap = {};
          global.jidMap[senderPhone] = senderJid;
          if (redis) {
            try { await redis.set(`whatsapp:jidmap:${senderPhone}`, senderJid, 'EX', 604800); } catch (e) {}
          }

          const text =
            m.message?.conversation ||
            m.message?.extendedTextMessage?.text ||
            '';

          const isAudio = Boolean(m.message?.audioMessage);

          if (!text && !isAudio) continue;

          // Instant typing dots indicator on WhatsApp
          try {
            await currentSocket.sendPresenceUpdate('composing', senderJid);
          } catch (pErr) {}

          // ------------------------------------------------------------------
          // A. VOICE NOTE / AUDIO MESSAGE INBOUND
          // ------------------------------------------------------------------
          if (isAudio) {
            console.log(`[Inbound WhatsApp Voice] From +${senderPhone} (${pushName}). Downloading audio note...`);
            try {
              let audioBuffer = null;
              try {
                const stream = await downloadContentFromMessage(m.message.audioMessage, 'audio');
                const chunks = [];
                for await (const chunk of stream) {
                  chunks.push(chunk);
                }
                audioBuffer = Buffer.concat(chunks);
              } catch (streamErr) {
                console.warn('[WhatsApp Gateway] Stream download fallback to downloadMediaMessage...');
                audioBuffer = await downloadMediaMessage(m, 'buffer', {}, { logger: pino({ level: 'silent' }) });
              }

              if (!audioBuffer || audioBuffer.length === 0) {
                console.error('[WhatsApp Gateway] Downloaded audio buffer was empty.');
                try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (e) {}
                continue;
              }

              console.log(`[WhatsApp Gateway] Audio downloaded (${audioBuffer.length} bytes). Transcribing via Python AI Backend...`);

              const voiceResponse = await fetch(`${BACKEND_URL}/api/whatsapp/connect/voice`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  phone: senderPhone,
                  remote_jid: senderJid,
                  sender_name: pushName,
                  audio_base64: audioBuffer.toString('base64'),
                  extension: 'ogg'
                })
              });

              if (voiceResponse.ok) {
                const data = await voiceResponse.json();
                const aiReply = data.response || data.ai_reply;
                const transcribed = data.transcribed_text;
                if (transcribed) {
                  console.log(`[Voice Note Transcribed]: "${transcribed}"`);
                }
                if (aiReply) {
                  console.log(`[Outbound AI Reply to Voice] To +${senderPhone}: "${aiReply.slice(0, 60)}..."`);
                  const typingDelay = 1000;
                  await new Promise((r) => setTimeout(r, typingDelay));
                  await currentSocket.sendPresenceUpdate('paused', senderJid);
                  await currentSocket.sendMessage(senderJid, { text: aiReply });
                } else {
                  try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (e) {}
                  console.log(`[Manual Mode Active] AI auto-reply skipped for voice note from +${senderPhone}.`);
                }
              } else {
                try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (e) {}
                console.error('[WhatsApp Gateway] Voice processing error from backend:', await voiceResponse.text());
              }
            } catch (voiceErr) {
              try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (e) {}
              console.error('[WhatsApp Gateway] Failed to handle incoming voice note:', voiceErr);
            }
            continue;
          }

          // ------------------------------------------------------------------
          // B. TEXT MESSAGE INBOUND
          // ------------------------------------------------------------------
          console.log(`[Inbound WhatsApp] From +${senderPhone} (${pushName}): "${text}"`);

          // Forward to Python AI Backend with Supabase RAG
          try {
            const response = await fetch(`${BACKEND_URL}/api/whatsapp/connect/simulate-inbound`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                phone: senderPhone,
                remote_jid: senderJid,
                message: text,
                sender_name: pushName
              })
            });

            if (response.ok) {
              const data = await response.json();
              const aiReply = data.response || data.ai_reply;
              if (aiReply) {
                console.log(`[Outbound AI Reply] To +${senderPhone}: "${aiReply.slice(0, 60)}..."`);
                const typingDelay = 1400;
                await new Promise((r) => setTimeout(r, typingDelay));
                await currentSocket.sendPresenceUpdate('paused', senderJid);
                await currentSocket.sendMessage(senderJid, { text: aiReply });
              } else {
                try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (pErr) {}
                console.log(`[Manual Mode Active] AI auto-reply skipped for +${senderPhone}. Saved for human agent.`);
              }
            } else {
              try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (pErr) {}
              console.error('[WhatsApp Gateway] Backend error:', await response.text());
            }
          } catch (backendErr) {
            try { await currentSocket.sendPresenceUpdate('paused', senderJid); } catch (pErr) {}
            console.error('[WhatsApp Gateway] Failed to query Python AI backend:', backendErr);
          }
        }
      } catch (err) {
        console.error('[WhatsApp Gateway] Error processing incoming message:', err);
      }
    });

  } catch (err) {
    console.error('[WhatsApp Gateway] Startup exception:', err.message);
    scheduleReconnect(5000, 'startup-exception');
  } finally {
    isStarting = false;
  }
}

// Request pairing code for phone number
app.post('/api/pair', async (req, res) => {
  const phone = req.body.phone || pairPhone;
  const cleanPhone = phone.replace(/[^0-9]/g, '');

  if (!sock) {
    return res.status(500).json({ error: 'Socket not initialized' });
  }

  try {
    console.log(`[WhatsApp Gateway] Requesting pairing code for +${cleanPhone}...`);
    await new Promise((r) => setTimeout(r, 1200));
    if (!sock) throw new Error('Socket was closed during pairing request');
    const code = await sock.requestPairingCode(cleanPhone);
    currentPairingCode = code;
    console.log(`[WhatsApp Gateway] Pairing Code Generated: ${code}`);
    return res.json({
      success: true,
      phone: cleanPhone,
      pairing_code: code,
      formatted_code: code ? `${code.slice(0, 4)}-${code.slice(4)}` : null,
      instruction: "WhatsApp > Linked Devices > Link with phone number instead > Enter this code"
    });
  } catch (err) {
    console.error('[WhatsApp Gateway] Failed to get pairing code:', err);
    return res.status(500).json({ error: err.message || 'Failed to request pairing code' });
  }
});

// Gateway Status API
app.get('/api/status', (req, res) => {
  res.json({
    status: connectionStatus,
    connected: connectionStatus === 'connected',
    phone: connectedUser,
    qr_image: currentQRImage,
    pairing_code: currentPairingCode,
    target_phone: pairPhone,
    redis_enabled: Boolean(redis),
    redis_connected: redis ? redis.status === 'ready' : false
  });
});

// Manual Reset / Force New QR Code API
app.post('/api/reset', async (req, res) => {
  console.log('[WhatsApp Gateway] Manual session reset requested via API. Clearing credentials...');
  cleanupSocket();
  clearAuthFiles();
  connectionStatus = 'connecting';
  currentQR = null;
  currentQRImage = null;
  currentPairingCode = null;
  connectedUser = null;
  consecutiveReplacements = 0;
  updateRedisStatus('disconnected', null);

  scheduleReconnect(500, 'manual-reset');
  return res.json({ success: true, message: 'Session reset successfully. Fresh QR code is generating...' });
});

// Send message API
app.post('/api/send', async (req, res) => {
  const { to, message } = req.body;
  if (!sock || connectionStatus !== 'connected') {
    return res.status(400).json({ error: 'WhatsApp is not connected yet.' });
  }

  let jid = String(to || '').trim();
  if (!jid.includes('@')) {
    const cleanDigits = jid.replace(/\D/g, '');
    let mapped = (global.jidMap && global.jidMap[cleanDigits]) ? global.jidMap[cleanDigits] : null;
    if (!mapped && redis) {
      try { mapped = await redis.get(`whatsapp:jidmap:${cleanDigits}`); } catch (e) {}
    }

    if (mapped) {
      jid = mapped;
    } else if (cleanDigits.length > 13) {
      // Numbers longer than 13 digits are WhatsApp Linked Device / Privacy LIDs
      jid = `${cleanDigits}@lid`;
    } else {
      jid = `${cleanDigits}@s.whatsapp.net`;
    }
  }

  try {
    const sent = await sock.sendMessage(jid, { text: message });
    return res.json({ success: true, messageId: sent.key.id, targetJid: jid });
  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
});

process.on('uncaughtException', (err) => {
  console.error('[WhatsApp Gateway] Uncaught Exception:', err?.message || err);
});

process.on('unhandledRejection', (err) => {
  console.error('[WhatsApp Gateway] Unhandled Rejection:', err?.message || err);
});

app.listen(PORT, () => {
  console.log(`[WhatsApp Gateway] HTTP Server running on http://localhost:${PORT}`);
  startWhatsAppGateway();
});

// Keep Node event loop alive indefinitely
setInterval(() => {}, 60000);
