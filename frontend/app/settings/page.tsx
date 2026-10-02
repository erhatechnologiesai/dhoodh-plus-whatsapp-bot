'use client';

import React, { useState, useEffect } from 'react';
import {
  CheckCircle2,
  ShieldCheck,
  Save,
  Bot,
  UserCheck,
  Key,
  Lock,
  Mail,
  Eye,
  EyeOff,
  AlertCircle,
  RotateCcw,
  Trash2
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, SystemSettings } from '@/lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState<SystemSettings>({
    id: 'default',
    llm_provider: 'openai',
    llm_model: 'gpt-4o-mini',
    embedding_provider: 'openai',
    embedding_model: 'text-embedding-3-small',
    temperature: 0.2,
    top_k: 5,
    similarity_threshold: 0.35,
    system_prompt: '',
  });

  // Admin Credentials & Account Security State
  const [adminProfile, setAdminProfile] = useState<{ email: string; username: string }>({
    email: 'admin@dhoodhplus.com',
    username: 'admin'
  });
  const [currentPassword, setCurrentPassword] = useState('');
  const [newEmail, setNewEmail] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPass, setShowCurrentPass] = useState(false);
  const [showNewPass, setShowNewPass] = useState(false);
  const [credUpdating, setCredUpdating] = useState(false);
  const [credSuccess, setCredSuccess] = useState<string | null>(null);
  const [credError, setCredError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getSettings();
        setSettings(data);
      } catch (e) {
        console.error('Failed to load settings:', e);
      }
    }
    load();

    async function loadCreds() {
      try {
        const p = await api.getProfile();
        if (p && p.email) {
          setAdminProfile({ email: p.email, username: p.username || 'admin' });
          setNewEmail(p.email);
        }
      } catch (e) {
        const u = api.getAuthUser();
        if (u?.email) {
          setAdminProfile({ email: u.email, username: u.username || 'admin' });
          setNewEmail(u.email);
        }
      }
    }
    loadCreds();

    const handleSync = (e: any) => {
      if (typeof e.detail?.bot_enabled === 'boolean') {
        setSettings((prev) => ({ ...prev, bot_enabled: e.detail.bot_enabled }));
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('bot-status-changed', handleSync);
    }
    return () => {
      if (typeof window !== 'undefined') {
        window.removeEventListener('bot-status-changed', handleSync);
      }
    };
  }, []);

  const handleUpdateCredentials = async (e: React.FormEvent) => {
    e.preventDefault();
    setCredError(null);
    setCredSuccess(null);

    if (!currentPassword) {
      setCredError('Please enter your current password to authorize changes.');
      return;
    }

    if (newPassword && newPassword.length < 6) {
      setCredError('New password must be at least 6 characters long.');
      return;
    }

    if (newPassword && newPassword !== confirmPassword) {
      setCredError('New passwords do not match. Please verify.');
      return;
    }

    if (newEmail && (!newEmail.includes('@') || !newEmail.includes('.'))) {
      setCredError('Please enter a valid email address.');
      return;
    }

    if (!newPassword && newEmail === adminProfile.email) {
      setCredError('Please provide a new email or new password to update.');
      return;
    }

    setCredUpdating(true);
    try {
      const res = await api.changeCredentials(
        currentPassword,
        newEmail.trim() || undefined,
        newPassword.trim() || undefined
      );
      setCredSuccess(res.message || 'Credentials updated successfully!');
      const updatedEmail = res.email;
      if (updatedEmail) {
        setAdminProfile((prev) => ({ ...prev, email: updatedEmail }));
      }
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setCredSuccess(null), 5000);
    } catch (err: any) {
      setCredError(err.message || 'Failed to update credentials. Please check your current password.');
    } finally {
      setCredUpdating(false);
    }
  };

  const [resettingData, setResettingData] = useState(false);
  const handleResetData = async () => {
    if (!window.confirm('Are you sure you want to reset all customer chats, messages, and analytics data to 0?')) {
      return;
    }
    setResettingData(true);
    try {
      await api.resetAllData();
      alert('All customer conversations, messages, and analytics data have been successfully reset to 0.');
    } catch (err: any) {
      alert(err.message || 'Failed to reset data.');
    } finally {
      setResettingData(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 text-black">
      <Header
        title="Settings & Account Security"
        subtitle="Manage Admin Credentials, Password & WhatsApp Bot Controls"
      />

      <main className="flex-1 px-4 md:px-8 pb-8 space-y-6 overflow-y-auto text-black">
        {/* Master AI Bot ON/OFF Toggle Section */}
        <div className="coachpro-card rounded-[26px] p-5 sm:p-6 text-black flex items-center justify-between gap-4 flex-wrap sm:flex-nowrap border-2 border-slate-200">
          <div className="flex items-center gap-4">
            <div
              className={`w-12 h-12 rounded-2xl flex items-center justify-center font-bold text-white shadow-md flex-shrink-0 ${
                settings.bot_enabled !== false ? 'bg-emerald-600' : 'bg-amber-500'
              }`}
            >
              {settings.bot_enabled !== false ? (
                <Bot className="w-6 h-6 text-white" />
              ) : (
                <UserCheck className="w-6 h-6 text-white" />
              )}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-black text-black text-base">
                  Master AI WhatsApp Bot Switch
                </h3>
                <span
                  className={`text-[10px] font-black px-2.5 py-0.5 rounded-full ${
                    settings.bot_enabled !== false
                      ? 'bg-emerald-100 text-black border border-emerald-300'
                      : 'bg-amber-100 text-black border border-amber-300'
                  }`}
                >
                  {settings.bot_enabled !== false ? 'BOT ACTIVE 🟢' : 'BOT OFF (HUMAN MODE) ⏸️'}
                </span>
              </div>
              <p className="text-xs text-black font-bold mt-1">
                {settings.bot_enabled !== false
                  ? 'AI Bot is automatically answering incoming customer questions 24/7 using the official Dhoodh Plus knowledge base.'
                  : 'AI Bot is paused. Incoming WhatsApp inquiries will not receive automated responses, allowing human staff to chat freely.'}
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={async () => {
              const nextState = settings.bot_enabled === false ? true : false;
              setSettings({ ...settings, bot_enabled: nextState });
              await api.toggleBot(nextState);
              if (typeof window !== 'undefined') {
                window.dispatchEvent(
                  new CustomEvent('bot-status-changed', { detail: { bot_enabled: nextState } })
                );
              }
            }}
            className={`w-full sm:w-auto px-5 py-2.5 rounded-2xl font-black text-xs flex items-center justify-center gap-2.5 transition-all shadow-md active:scale-95 flex-shrink-0 cursor-pointer ${
              settings.bot_enabled !== false
                ? 'bg-amber-500 hover:bg-amber-600 text-white'
                : 'bg-emerald-600 hover:bg-emerald-700 text-white'
            }`}
          >
            {settings.bot_enabled !== false ? (
              <>
                <UserCheck className="w-4 h-4" />
                Turn Bot OFF (Human Mode)
              </>
            ) : (
              <>
                <Bot className="w-4 h-4" />
                Turn Bot ON (AI Auto-Reply)
              </>
            )}
          </button>
        </div>

        {/* Admin Account Security & Login Credentials Section in place of RAG grid */}
        <div className="coachpro-card rounded-[26px] p-6 sm:p-8 text-black border-2 border-slate-200 space-y-6 shadow-sm">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 border-b border-slate-200 gap-4">
            <div className="flex items-center gap-3">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-teal-800 to-emerald-600 text-white flex items-center justify-center font-bold flex-shrink-0 shadow-md">
                <Lock className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-black text-black text-lg">
                    Admin Account Security & Credentials
                  </h3>
                  <span className="text-[10px] font-black bg-emerald-100 text-black px-2.5 py-0.5 rounded-full border border-emerald-300">
                    Active Session
                  </span>
                </div>
                <p className="text-xs text-black font-bold mt-0.5">
                  Update your official login email and administrative password. Changes persist across all sessions and server reboots.
                </p>
              </div>
            </div>

            {/* Current Active Email Badge */}
            <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 rounded-2xl border border-slate-200 self-start sm:self-auto">
              <Mail className="w-4 h-4 text-black" />
              <span className="text-xs font-black text-black">
                Active Email: <span className="text-teal-800 font-mono">{adminProfile.email}</span>
              </span>
            </div>
          </div>

          {/* Feedback Alerts */}
          {credSuccess && (
            <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center gap-3 text-emerald-800 text-xs font-black">
              <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
              <span>{credSuccess}</span>
            </div>
          )}

          {credError && (
            <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-center gap-3 text-rose-800 text-xs font-black">
              <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0" />
              <span>{credError}</span>
            </div>
          )}

          {/* Credentials Update Form */}
          <form onSubmit={handleUpdateCredentials} className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Email & Current Password */}
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-black text-black mb-1.5 uppercase tracking-wide">
                    Admin Email Address
                  </label>
                  <div className="relative">
                    <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      type="email"
                      value={newEmail}
                      onChange={(e) => setNewEmail(e.target.value)}
                      placeholder="admin@dhoodhplus.com"
                      className="w-full pl-10 pr-3.5 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs font-black text-black focus:outline-none focus:border-teal-700"
                    />
                  </div>
                  <p className="text-[11px] text-slate-500 font-bold mt-1">
                    Used to sign in to the Allah Ho Traders admin portal.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-black text-black mb-1.5 uppercase tracking-wide">
                    Current Password <span className="text-rose-500 font-bold">*Required</span>
                  </label>
                  <div className="relative">
                    <Key className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      type={showCurrentPass ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      placeholder="Enter current password (default: admin123)"
                      className="w-full pl-10 pr-10 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs font-black text-black focus:outline-none focus:border-teal-700"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPass(!showCurrentPass)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
                    >
                      {showCurrentPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-500 font-bold mt-1">
                    Required to authorize updating email or password.
                  </p>
                </div>
              </div>

              {/* New Password & Confirm Password */}
              <div className="space-y-5">
                <div>
                  <label className="block text-xs font-black text-black mb-1.5 uppercase tracking-wide">
                    New Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      type={showNewPass ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      placeholder="Leave blank to keep unchanged (min 6 chars)"
                      className="w-full pl-10 pr-10 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs font-black text-black focus:outline-none focus:border-teal-700"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPass(!showNewPass)}
                      className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700"
                    >
                      {showNewPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[11px] text-slate-500 font-bold mt-1">
                    Minimum 6 characters. Leave empty if only changing email.
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-black text-black mb-1.5 uppercase tracking-wide">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                      type={showNewPass ? 'text' : 'password'}
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-type new password"
                      className="w-full pl-10 pr-3.5 py-3 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs font-black text-black focus:outline-none focus:border-teal-700"
                    />
                  </div>
                  <p className="text-[11px] text-slate-500 font-bold mt-1">
                    Must match new password exactly.
                  </p>
                </div>
              </div>
            </div>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-slate-200">
              <div className="flex items-center gap-2 text-xs text-slate-600 font-bold">
                <ShieldCheck className="w-4 h-4 text-emerald-600" />
                <span>Salted SHA-256 encrypted authentication & persistent volume storage</span>
              </div>
              <button
                type="submit"
                disabled={credUpdating}
                className="w-full sm:w-auto px-8 py-3 bg-gradient-to-r from-teal-800 to-emerald-600 hover:opacity-95 text-white font-black text-xs rounded-2xl shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 active:scale-95"
              >
                <Save className="w-4 h-4" />
                {credUpdating ? 'Updating Credentials...' : 'Save New Credentials'}
              </button>
            </div>
          </form>
        </div>

        {/* Reset System Data Section */}
        <div className="coachpro-card rounded-[26px] p-6 text-black border-2 border-rose-200 bg-rose-50/20 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center font-bold flex-shrink-0 shadow-xs">
                <Trash2 className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-black text-black text-base">
                  Reset Chat & Customer Data to 0
                </h4>
                <p className="text-xs text-slate-600 font-bold mt-0.5">
                  Clear all customer conversations, message logs, and analytics counters to start fresh from 0 with a newly connected WhatsApp number.
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={handleResetData}
              disabled={resettingData}
              className="px-5 py-2.5 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white font-black text-xs shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer flex-shrink-0 disabled:opacity-50 active:scale-95"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${resettingData ? 'animate-spin' : ''}`} />
              {resettingData ? 'Resetting Data...' : 'Reset All to 0'}
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
