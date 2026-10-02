'use client';

import React, { useState, useEffect } from 'react';
import {
  QrCode,
  Smartphone,
  CheckCircle2,
  RefreshCw,
  Send,
  Zap,
  ShieldCheck,
  Radio,
  Bot,
  Copy,
  Check,
  KeyRound,
  ArrowRight,
  Sparkles
} from 'lucide-react';
import { Header } from '@/components/Header';

interface GatewayStatus {
  status: string;
  connected: boolean;
  phone: string | null;
  qr_image: string | null;
  pairing_code: string | null;
  target_phone: string | null;
}

export default function ConnectWhatsAppPage() {
  const [gatewayStatus, setGatewayStatus] = useState<GatewayStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [phoneInput, setPhoneInput] = useState('');
  const [requestingCode, setRequestingCode] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [activeTab, setActiveTab] = useState<'qr' | 'code'>('qr');

  const [testPhone, setTestPhone] = useState('');
  const [testQuestion, setTestQuestion] = useState('Doodh Plus 10kg pack kitne ka hai aur delivery kahan tak hoti hai?');
  const [testLoading, setTestLoading] = useState(false);
  const [testResponse, setTestResponse] = useState<any>(null);
  const [resettingSession, setResettingSession] = useState(false);

  const getGatewayBase = () => {
    if (typeof window !== 'undefined') {
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:3001';
      }
      return `${window.location.origin}/gateway`;
    }
    return 'http://localhost:3001';
  };

  const fetchGatewayStatus = async () => {
    try {
      const res = await fetch(`${getGatewayBase()}/api/status`);
      if (res.ok) {
        const data = await res.json();
        setGatewayStatus(data);
      }
    } catch (e) {
      console.warn('Gateway polling error:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGatewayStatus();
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) return;
      fetchGatewayStatus();
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleResetSession = async () => {
    setResettingSession(true);
    try {
      await fetch(`${getGatewayBase()}/api/reset`, { method: 'POST' });
      setTimeout(() => fetchGatewayStatus(), 1500);
      setTimeout(() => fetchGatewayStatus(), 3500);
    } catch (e) {
      console.error('Reset failed:', e);
    } finally {
      setTimeout(() => setResettingSession(false), 2000);
    }
  };

  const handleRequestPairingCode = async (targetPhoneToUse?: string) => {
    const rawNumber = targetPhoneToUse || phoneInput;
    if (!rawNumber) return;
    setRequestingCode(true);
    setCopiedCode(false);

    let clean = rawNumber.replace(/[^0-9]/g, '');
    if (clean.startsWith('0')) {
      clean = '92' + clean.slice(1);
    }

    try {
      const res = await fetch(`${getGatewayBase()}/api/pair`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: clean })
      });
      if (res.ok) {
        await fetchGatewayStatus();
      }
    } catch (e) {
      console.error('Failed to request pairing code:', e);
    } finally {
      setRequestingCode(false);
    }
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code.replace('-', ''));
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2500);
  };

  const handleSimulateChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testQuestion) return;
    setTestLoading(true);
    setTestResponse(null);

    let clean = testPhone.replace(/[^0-9]/g, '');
    if (clean.startsWith('0')) clean = '92' + clean.slice(1);

    try {
      const res = await fetch('/api/whatsapp/connect/simulate-inbound', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: clean || (gatewayStatus?.phone ? gatewayStatus.phone : '923001234567'),
          message: testQuestion,
          sender_name: 'Customer'
        })
      });
      const data = await res.json();
      setTestResponse(data);
    } catch (err: any) {
      setTestResponse({ error: 'Failed to communicate with bot service.' });
    } finally {
      setTestLoading(false);
    }
  };

  const rawPairingCode = gatewayStatus?.pairing_code || 'R7KPKF1G';
  const formattedPairingCode = rawPairingCode.includes('-')
    ? rawPairingCode
    : `${rawPairingCode.slice(0, 4)} - ${rawPairingCode.slice(4)}`;

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-black">
      <Header
        title="Connect WhatsApp"
        subtitle="Gateway Pairing & Live Device Link"
      />

      <main className="flex-1 px-3 sm:px-6 md:px-8 pb-6 space-y-4 overflow-y-auto text-black max-w-7xl mx-auto w-full">
        {/* Top Status Bar (Compact) */}
        <div className="coachpro-card rounded-2xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-black">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-800 to-emerald-600 flex items-center justify-center text-white shadow-md shadow-teal-900/20 flex-shrink-0">
              <Smartphone className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-base font-black text-black">
                WhatsApp Device Link & Pairing
              </h3>
              {gatewayStatus?.connected && gatewayStatus.phone ? (
                <p className="text-[11px] text-black font-bold">
                  Connected Number: <strong className="text-black font-black">+{gatewayStatus.phone}</strong>
                </p>
              ) : (
                <p className="text-[11px] text-slate-500 font-medium">
                  Scan QR code or use pairing code to link your WhatsApp number
                </p>
              )}
            </div>
          </div>

          <div>
            {gatewayStatus?.connected && gatewayStatus.phone ? (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-black bg-emerald-100 text-black border border-emerald-300 shadow-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Active Link: +{gatewayStatus.phone}
              </div>
            ) : (
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-black bg-amber-100 text-black border border-amber-300 shadow-sm">
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
                Ready to Link (Scan QR Below)
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 text-black">
          {/* Main Pairing Card (Left Column - Compact) */}
          <div className="lg:col-span-7 space-y-4">
            <div className="coachpro-card rounded-2xl p-4 sm:p-5 space-y-4 text-black">
              {/* Tab Switcher: Scanner First, Code Second */}
              <div className="flex items-center gap-2 border-b border-slate-200 pb-3 flex-wrap sm:flex-nowrap">
                <button
                  onClick={() => setActiveTab('qr')}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-black transition-all active:scale-95 ${
                    activeTab === 'qr'
                      ? 'bg-gradient-to-r from-teal-800 to-emerald-600 text-white shadow-md shadow-teal-900/20'
                      : 'text-black hover:text-black bg-slate-100'
                  }`}
                >
                  <QrCode className="w-3.5 h-3.5" />
                  Live QR Code Scanner
                </button>
                <button
                  onClick={() => setActiveTab('code')}
                  className={`flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-black transition-all active:scale-95 ${
                    activeTab === 'code'
                      ? 'bg-gradient-to-r from-teal-800 to-emerald-600 text-white shadow-md shadow-teal-900/20'
                      : 'text-black hover:text-black bg-slate-100'
                  }`}
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  8-Digit Pairing Code (Phone Method)
                </button>
              </div>

              {/* 1. PRIMARY OPTION: QR Scanner */}
              {activeTab === 'qr' && (
                <div className="space-y-4 text-center py-2 text-black">
                  {gatewayStatus?.connected ? (
                    <div className="p-6 bg-emerald-50 rounded-2xl border border-emerald-200 text-black max-w-sm mx-auto">
                      <CheckCircle2 className="w-10 h-10 mx-auto text-emerald-600 mb-2" />
                      <p className="font-black text-black text-sm">WhatsApp Is Connected & Active!</p>
                      {gatewayStatus?.phone && (
                        <p className="text-xs text-black font-bold mt-1">
                          Linked with +{gatewayStatus.phone}
                        </p>
                      )}
                      <button
                        onClick={handleResetSession}
                        disabled={resettingSession}
                        className="mt-3 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-all cursor-pointer"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${resettingSession ? 'animate-spin' : ''}`} />
                        {resettingSession ? 'Disconnecting...' : 'Disconnect / Re-link Device'}
                      </button>
                    </div>
                  ) : gatewayStatus?.qr_image ? (
                    <div className="space-y-3">
                      <div className="inline-block p-3 bg-white rounded-2xl border-2 border-teal-600 shadow-md">
                        <img
                          src={gatewayStatus.qr_image}
                          alt="WhatsApp QR Code"
                          className="w-48 h-48 mx-auto rounded-xl object-contain"
                        />
                      </div>
                      <div>
                        <button
                          onClick={handleResetSession}
                          disabled={resettingSession}
                          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-black text-teal-800 bg-teal-50 hover:bg-teal-100 border border-teal-300 transition-all shadow-sm cursor-pointer"
                        >
                          <RefreshCw className={`w-3.5 h-3.5 ${resettingSession ? 'animate-spin' : ''}`} />
                          {resettingSession ? 'Refreshing QR Code...' : 'Refresh / Regenerate QR Code'}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="p-6 bg-slate-50 rounded-2xl border border-slate-200 text-black max-w-sm mx-auto space-y-3">
                      <RefreshCw className="w-8 h-8 mx-auto text-teal-700 animate-spin" />
                      <div>
                        <p className="font-black text-xs text-black">Generating Live QR Code...</p>
                        <p className="text-[11px] text-slate-600 mt-1">Starting session with WhatsApp servers...</p>
                      </div>
                      <button
                        onClick={handleResetSession}
                        disabled={resettingSession}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-black text-teal-800 bg-white hover:bg-teal-50 border border-teal-300 transition-all shadow-sm cursor-pointer"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${resettingSession ? 'animate-spin' : ''}`} />
                        {resettingSession ? 'Resetting Session...' : 'Force Generate New QR Code'}
                      </button>
                    </div>
                  )}

                  {/* QR Link Steps */}
                  <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 max-w-md mx-auto text-left">
                    <span className="text-[11px] font-black uppercase tracking-wider text-black block mb-2">
                      Scan Instructions:
                    </span>
                    <ol className="space-y-1.5 text-xs text-black font-bold">
                      <li className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px]">
                          1
                        </span>
                        <span>Open <strong>WhatsApp</strong> on your mobile.</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px]">
                          2
                        </span>
                        <span>Tap <strong>Settings</strong> or <strong>Three Dots ⋮</strong> &gt; <strong>Linked Devices</strong>.</span>
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px]">
                          3
                        </span>
                        <span>Tap <strong>Link a Device</strong> and point your camera at this QR code.</span>
                      </li>
                    </ol>
                  </div>
                </div>
              )}

              {/* 2. SECOND OPTION: Pairing Code */}
              {activeTab === 'code' && (
                <div className="space-y-4 text-black">
                  <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-center">
                    <span className="text-[11px] uppercase tracking-wider font-black text-black">
                      Your WhatsApp Pairing Code:
                    </span>

                    <div className="my-2.5 flex items-center justify-center gap-2.5">
                      <div className="font-mono text-2xl sm:text-3xl font-black text-black tracking-widest px-4 py-2 bg-white rounded-xl border-2 border-teal-600 shadow-sm">
                        {formattedPairingCode}
                      </div>
                      <button
                        onClick={() => handleCopyCode(gatewayStatus?.pairing_code || 'R7KPKF1G')}
                        className="p-2.5 bg-gradient-to-r from-teal-800 to-emerald-600 hover:opacity-95 text-white rounded-xl shadow-md transition-transform active:scale-95"
                        title="Copy Pairing Code"
                      >
                        {copiedCode ? <Check className="w-4 h-4 text-white" /> : <Copy className="w-4 h-4 text-white" />}
                      </button>
                    </div>

                    <p className="text-[11px] text-black font-bold">
                      Enter this code in WhatsApp on your mobile phone to complete connection.
                    </p>
                  </div>

                  <div className="space-y-2 text-black">
                    <h4 className="text-[11px] font-black uppercase tracking-wider text-black">
                      How to link using Pairing Code:
                    </h4>
                    <ol className="space-y-1.5 text-xs text-black font-bold">
                      <li className="flex items-start gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px] mt-0.5">
                          1
                        </span>
                        <span>Open WhatsApp on your mobile.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px] mt-0.5">
                          2
                        </span>
                        <span>Tap <strong>Settings</strong> or <strong>Three Dots ⋮</strong> &gt; <strong>Linked Devices</strong>.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px] mt-0.5">
                          3
                        </span>
                        <span>Tap <strong>Link a Device</strong> &gt; Tap <strong>Link with phone number instead</strong> at the bottom.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="w-4 h-4 rounded-full bg-black text-white font-black flex items-center justify-center flex-shrink-0 text-[10px] mt-0.5">
                          4
                        </span>
                        <span>Enter the 8-digit code shown above to connect immediately!</span>
                      </li>
                    </ol>
                  </div>

                  <div className="pt-3 border-t border-slate-200 flex items-center gap-2">
                    <input
                      type="text"
                      value={phoneInput}
                      onChange={(e) => setPhoneInput(e.target.value)}
                      placeholder="e.g. 03001234567"
                      className="flex-1 px-3 py-2 rounded-xl border-2 border-slate-300 bg-white text-xs font-black text-black focus:outline-none"
                    />
                    <button
                      onClick={() => handleRequestPairingCode()}
                      disabled={requestingCode}
                      className="px-4 py-2 rounded-xl bg-gradient-to-r from-teal-800 to-emerald-600 text-white text-xs font-black shadow-md hover:opacity-95 transition-all flex items-center gap-1.5 flex-shrink-0"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${requestingCode ? 'animate-spin' : ''}`} />
                      Generate New Code
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* AI Playground Tester (Right Column - Compact) */}
          <div className="lg:col-span-5 space-y-4 text-black">
            <div className="coachpro-card rounded-2xl p-4 sm:p-5 space-y-4 text-black">
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-lg bg-teal-100 text-black flex items-center justify-center font-black text-xs">
                    <Zap className="w-3.5 h-3.5 text-black" />
                  </div>
                  <h4 className="text-xs font-black text-black">
                    Live AI Playground Tester
                  </h4>
                </div>
                <span className="text-[10px] font-black bg-teal-100 text-black px-2 py-0.5 rounded-full border border-teal-300">
                  Instant Simulation
                </span>
              </div>

              <form onSubmit={handleSimulateChat} className="space-y-3 text-black">
                <div>
                  <label className="text-[11px] font-black text-black block mb-1">
                    Customer Message to Bot:
                  </label>
                  <textarea
                    rows={2}
                    value={testQuestion}
                    onChange={(e) => setTestQuestion(e.target.value)}
                    placeholder="e.g. ap ka product kns ah, ma b thk hoo, 10 kg pack chahiye..."
                    className="w-full p-2.5 rounded-xl border-2 border-slate-300 bg-white text-xs font-bold text-black focus:outline-none leading-relaxed resize-none"
                  />
                </div>

                <div className="flex flex-wrap gap-1">
                  {[
                    'ap ka product kns ah',
                    'ma b thk hoo',
                    'meri bakri dewwar chatti ha',
                    '10 kg pack chahiye'
                  ].map((preset) => (
                    <button
                      key={preset}
                      type="button"
                      onClick={() => setTestQuestion(preset)}
                      className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 hover:bg-teal-100 text-black font-black transition-colors"
                    >
                      {preset}
                    </button>
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={testLoading}
                  className="w-full py-2 rounded-xl bg-gradient-to-r from-teal-800 to-emerald-600 hover:opacity-95 text-white font-black text-xs shadow-md transition-all flex items-center justify-center gap-1.5"
                >
                  <Send className={`w-3.5 h-3.5 ${testLoading ? 'animate-bounce' : ''}`} />
                  {testLoading ? 'Generating...' : 'Simulate Customer Message'}
                </button>
              </form>

              {testResponse && (
                <div className="mt-3 p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5 text-black">
                  <span className="text-[10px] font-black text-black uppercase tracking-wider block">
                    Bot Response (Live Output):
                  </span>
                  <div className="text-xs text-black whitespace-pre-line leading-relaxed bg-white p-2.5 rounded-lg border border-slate-200 font-bold">
                    {testResponse.response || testResponse.ai_reply || testResponse.error}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
