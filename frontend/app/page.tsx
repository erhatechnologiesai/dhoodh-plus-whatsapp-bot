'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Sparkles,
  ArrowUpRight,
  ShieldCheck,
  Zap,
  BookOpen,
  MessageSquare,
  Users,
  CheckCircle2,
  Clock,
  Radio,
  ChevronRight,
  TrendingUp,
  Package,
  Layers,
  Bot,
  UserCheck,
  RotateCcw,
  Trash2,
  AlertTriangle
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, AnalyticsSummary, ConversationItem } from '@/lib/api';
import { formatFullDate } from '@/lib/utils';

export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [recentConversations, setRecentConversations] = useState<ConversationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [botActive, setBotActive] = useState<boolean>(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [stats, convs, settings] = await Promise.all([
          api.getAnalytics(),
          api.listConversations(),
          api.getSettings().catch(() => null)
        ]);
        setAnalytics(stats);
        setRecentConversations(convs.slice(0, 6));
        if (settings && typeof settings.bot_enabled === 'boolean') {
          setBotActive(settings.bot_enabled);
        }
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) return;
      fetchData();
    }, 20000);

    const handleSync = (e: any) => {
      if (typeof e.detail?.bot_enabled === 'boolean') {
        setBotActive(e.detail.bot_enabled);
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('bot-status-changed', handleSync);
    }

    return () => {
      clearInterval(interval);
      if (typeof window !== 'undefined') {
        window.removeEventListener('bot-status-changed', handleSync);
      }
    };
  }, []);

  // Reset Data State
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState<string | null>(null);

  const handleResetAllData = async () => {
    setResetting(true);
    try {
      await api.resetAllData();
      setAnalytics({
        total_customers: 0,
        total_conversations: 0,
        total_messages: 0,
        active_conversations: 0,
        ai_resolved_conversations: 0,
        human_handoffs: 0,
        ready_documents: analytics?.ready_documents || 1,
        total_knowledge_chunks: analytics?.total_knowledge_chunks || 6,
        average_latency_ms: 0,
        retrieval_success_rate: 100,
        daily_messages: []
      });
      setRecentConversations([]);
      setResetSuccess('All chat history, messages, and customer data successfully reset to 0!');
      setResetModalOpen(false);
      setTimeout(() => setResetSuccess(null), 5000);
    } catch (err: any) {
      alert(err.message || 'Failed to reset data.');
    } finally {
      setResetting(false);
    }
  };

  const totalConversations = analytics?.total_conversations ?? 0;
  const aiResolved = analytics?.ai_resolved_conversations ?? 0;
  const humanHandoffs = analytics?.human_handoffs ?? 0;
  const aiPercentage = totalConversations > 0 ? Math.round((aiResolved / totalConversations) * 100) : 100;
  const handoffPercentage = 100 - aiPercentage;

  const displayConversations = recentConversations;

  return (
    <div className="flex-1 flex flex-col min-w-0 text-black">
      <Header
        title="Dashboard"
      />

      <main className="flex-1 px-3 sm:px-4 md:px-8 pb-8 space-y-4 sm:space-y-6 overflow-y-auto text-black">
        {/* Banner when AI Bot is Turned OFF (Manual Human Mode) */}
        {!botActive && (
          <div className="p-3.5 sm:p-4 rounded-[22px] sm:rounded-[26px] bg-amber-50/95 border-2 border-amber-300 shadow-sm flex items-center justify-between gap-3 flex-wrap sm:flex-nowrap animate-in fade-in slide-in-from-top-2">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-2xl bg-amber-500 text-white flex items-center justify-center font-black flex-shrink-0 shadow-sm">
                <UserCheck className="w-5 h-5 text-white" />
              </div>
              <div>
                <h4 className="font-black text-xs sm:text-sm text-black leading-tight">
                  Bot is OFF (Manual Human Mode Active)
                </h4>
                <p className="text-[11px] sm:text-xs font-bold text-black mt-0.5">
                  AI auto-replies are paused. New customer messages are saved so human operators can reply directly via WhatsApp or Live Chat.
                </p>
              </div>
            </div>
            <button
              onClick={async () => {
                setBotActive(true);
                await api.toggleBot(true);
                if (typeof window !== 'undefined') {
                  window.dispatchEvent(
                    new CustomEvent('bot-status-changed', { detail: { bot_enabled: true } })
                  );
                }
              }}
              className="w-full sm:w-auto px-4 py-2 rounded-xl bg-black hover:bg-slate-800 text-white font-black text-xs flex items-center justify-center gap-2 shadow-md active:scale-95 transition-all flex-shrink-0 cursor-pointer"
            >
              <Bot className="w-4 h-4 text-emerald-400" />
              Resume AI Bot
            </button>
          </div>
        )}

        {/* Top Control Bar: Live Indicator & Reset All Data Button */}
        <div className="flex items-center justify-between gap-3 flex-wrap bg-white/80 p-3 sm:p-4 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-xs font-black text-black">
              Active WhatsApp Dashboard
            </span>
            <span className="text-[10px] font-black px-2 py-0.5 rounded-full bg-slate-100 text-black border border-slate-300">
              Starts from 0
            </span>
          </div>

          <button
            type="button"
            onClick={() => setResetModalOpen(true)}
            className="px-3.5 py-1.5 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-black text-xs flex items-center gap-1.5 shadow-xs active:scale-95 transition-all cursor-pointer"
            title="Reset all customer chats, messages, and counters to 0"
          >
            <RotateCcw className="w-3.5 h-3.5 text-rose-600" />
            <span>Reset All Data to 0</span>
          </button>
        </div>

        {/* Reset Success Feedback Alert */}
        {resetSuccess && (
          <div className="p-3.5 rounded-2xl bg-emerald-50 border border-emerald-300 text-emerald-800 text-xs font-black flex items-center gap-2 shadow-xs">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span>{resetSuccess}</span>
          </div>
        )}

        {/* ROW 1: 4 Big AI Resolution Statistics Cards in Full Black */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
          {/* Tile 1: Total Inquiries */}
          <Link
            href="/conversations"
            className="coachpro-card rounded-[22px] sm:rounded-[26px] p-4 sm:p-5 md:p-6 flex flex-col justify-between text-black hover:-translate-y-1 hover:shadow-md active:scale-[0.98] transition-all group"
          >
            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <span className="text-[10px] sm:text-xs font-black text-black uppercase tracking-wider truncate">
                TOTAL INQUIRIES
              </span>
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-slate-100 flex items-center justify-center flex-shrink-0 group-hover:bg-slate-200 transition-colors">
                <MessageSquare className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-black" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-black tracking-tight my-0.5 sm:my-1">
              {totalConversations}
            </div>
          </Link>

          {/* Tile 2: AI Responded */}
          <Link
            href="/analytics"
            className="coachpro-card rounded-[22px] sm:rounded-[26px] p-4 sm:p-5 md:p-6 flex flex-col justify-between text-black hover:-translate-y-1 hover:shadow-md active:scale-[0.98] transition-all group"
          >
            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <span className="text-[10px] sm:text-xs font-black text-black uppercase tracking-wider truncate">
                AI Responded
              </span>
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0 group-hover:bg-emerald-200 transition-colors">
                <Bot className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-black" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-black tracking-tight my-0.5 sm:my-1">
              {aiResolved}
            </div>
          </Link>

          {/* Tile 3: Resolution Rate */}
          <Link
            href="/analytics"
            className="coachpro-card rounded-[22px] sm:rounded-[26px] p-4 sm:p-5 md:p-6 flex flex-col justify-between text-black hover:-translate-y-1 hover:shadow-md active:scale-[0.98] transition-all group"
          >
            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <span className="text-[10px] sm:text-xs font-black text-black uppercase tracking-wider truncate">
                RESOLUTION RATE
              </span>
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-teal-100 flex items-center justify-center flex-shrink-0 group-hover:bg-teal-200 transition-colors">
                <CheckCircle2 className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-black" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-black tracking-tight my-0.5 sm:my-1">
              {aiPercentage}%
            </div>
          </Link>

          {/* Tile 4: Human Handoffs */}
          <Link
            href="/handoffs"
            className="coachpro-card rounded-[22px] sm:rounded-[26px] p-4 sm:p-5 md:p-6 flex flex-col justify-between text-black hover:-translate-y-1 hover:shadow-md active:scale-[0.98] transition-all group"
          >
            <div className="flex items-center justify-between mb-2 sm:mb-3">
              <span className="text-[10px] sm:text-xs font-black text-black uppercase tracking-wider truncate">
                HUMAN HANDOFFS
              </span>
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-rose-100 flex items-center justify-center flex-shrink-0 group-hover:bg-rose-200 transition-colors">
                <Users className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-black" />
              </div>
            </div>
            <div className="text-2xl sm:text-3xl lg:text-4xl font-black text-black tracking-tight my-0.5 sm:my-1">
              {humanHandoffs}
            </div>
          </Link>
        </div>

        {/* ROW 2: Standings Table on Left + 2x2 KPI Tiles on Right in FULL BLACK */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 sm:gap-6">
          {/* Left Column: Customer Inquiries Table */}
          <div className="lg:col-span-7 coachpro-card rounded-[24px] sm:rounded-[26px] p-4 sm:p-5 md:p-6 flex flex-col justify-between text-black">
            <div>
              <div className="flex items-center justify-between mb-3 sm:mb-4 gap-2">
                <div>
                  <h3 className="text-sm sm:text-base font-black text-black">
                    Customer Inquiries & Orders
                  </h3>
                  <p className="text-[11px] sm:text-xs text-black font-bold mt-0.5">
                    Live multi-turn WhatsApp sessions
                  </p>
                </div>
                <Link
                  href="/conversations"
                  className="text-xs font-black text-black hover:underline active:scale-95 flex items-center gap-1 transition-all flex-shrink-0"
                >
                  View all <ArrowUpRight className="w-3.5 h-3.5 text-black" />
                </Link>
              </div>

              {/* Table or Clean Empty State */}
              {displayConversations.length === 0 ? (
                <div className="py-12 px-4 text-center text-black space-y-2">
                  <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center mx-auto text-black mb-2 shadow-xs">
                    <MessageSquare className="w-6 h-6 text-black" />
                  </div>
                  <h4 className="text-sm font-black text-black">No customer inquiries yet</h4>
                  <p className="text-xs text-slate-500 font-bold max-w-sm mx-auto">
                    When customers message your connected WhatsApp number, inquiries and live chats will show here starting from 0.
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs text-black">
                    <thead>
                      <tr className="border-b-2 border-slate-200 text-[11px] font-black text-black uppercase tracking-wider">
                        <th className="py-2.5 px-2 w-8">#</th>
                        <th className="py-2.5 px-2">CUSTOMER</th>
                        <th className="py-2.5 px-2">LAST INQUIRY</th>
                        <th className="py-2.5 px-2 text-right">STATUS</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {displayConversations.slice(0, 4).map((item, index) => (
                        <tr
                          key={item.id}
                          className="hover:bg-teal-50/50 transition-colors group cursor-pointer text-black"
                        >
                          {/* Index Number */}
                          <td className="py-2.5 px-2 font-black text-black">
                            {index + 1}
                          </td>

                          {/* Customer Info */}
                          <td className="py-2.5 px-2">
                            <Link href={`/conversations?id=${item.id}`} className="block">
                              <span className="font-black text-black block text-xs sm:text-sm">
                                {item.customer_name || 'Customer'}
                              </span>
                              <span className="text-[11px] font-mono font-bold text-black">
                                +{item.customer_phone}
                              </span>
                            </Link>
                          </td>

                          {/* Inquiry / Last message */}
                          <td className="py-2.5 px-2 max-w-[180px] sm:max-w-[220px]">
                            <span className="truncate block text-black font-bold">
                              {item.last_message || 'New conversation started'}
                            </span>
                          </td>

                          {/* Status Badge in Full Black Font */}
                          <td className="py-2.5 px-2 text-right whitespace-nowrap">
                            <span
                              className={`inline-block px-2.5 py-1 rounded-full text-[10px] font-black text-black ${
                                item.status === 'ORDER_CONFIRMED'
                                  ? 'bg-teal-100 border border-teal-300'
                                  : item.status === 'HUMAN_HANDOFF'
                                  ? 'bg-amber-100 border border-amber-300'
                                  : 'bg-emerald-100 border border-emerald-300'
                              }`}
                            >
                              {item.status === 'ORDER_CONFIRMED'
                                ? 'Order Booked'
                                : item.status === 'HUMAN_HANDOFF'
                                ? 'Human Handled'
                                : 'AI Responded'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="pt-3 mt-3 border-t border-slate-200 flex items-center justify-between text-xs text-black font-bold">
              <span className="flex items-center gap-1.5 font-bold text-black">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
                Listening to WhatsApp Webhooks
              </span>
              <Link
                href="/handoffs"
                className="font-black text-black hover:underline flex items-center gap-1"
              >
                Escalations ({humanHandoffs})
              </Link>
            </div>
          </div>

          {/* Right Column: 2x2 Mini KPI Tiles in FULL BLACK (Compact & Balanced) */}
          <div className="lg:col-span-5 flex flex-col text-black">
            {/* 2x2 Mini Tiles */}
            <div className="grid grid-cols-2 gap-4 h-full">
              {/* Tile 1: Grounding Rate */}
              <div className="coachpro-card rounded-[22px] p-4 sm:p-5 flex flex-col justify-between text-black">
                <div className="flex items-center gap-2 sm:gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-purple-100 flex items-center justify-center text-black font-bold shadow-xs flex-shrink-0">
                    <ShieldCheck className="w-4 h-4 text-black" />
                  </div>
                  <span className="text-[10px] sm:text-[11px] font-black text-black uppercase tracking-wider truncate">
                    GROUNDING
                  </span>
                </div>
                <div className="pt-2 sm:pt-3">
                  <div className="text-xl sm:text-2xl font-black text-black tracking-tight leading-none">
                    98.5%
                  </div>
                  <span className="text-[11px] font-bold text-black block mt-1 truncate">
                    Zero hallucinations
                  </span>
                </div>
              </div>

              {/* Tile 2: Official Packs */}
              <div className="coachpro-card rounded-[22px] p-4 sm:p-5 flex flex-col justify-between text-black">
                <div className="flex items-center gap-2 sm:gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-pink-100 flex items-center justify-center text-black font-bold shadow-xs flex-shrink-0">
                    <Package className="w-4 h-4 text-black" />
                  </div>
                  <span className="text-[10px] sm:text-[11px] font-black text-black uppercase tracking-wider truncate">
                    PRICING
                  </span>
                </div>
                <div className="pt-2 sm:pt-3">
                  <div className="text-lg sm:text-xl font-black text-black tracking-tight leading-none">
                    1.75k / 12.5k
                  </div>
                  <span className="text-[11px] font-bold text-black block mt-1 truncate">
                    1 KG & 10 KG Bachat
                  </span>
                </div>
              </div>

              {/* Tile 3: Knowledge Base */}
              <div className="coachpro-card rounded-[22px] p-4 sm:p-5 flex flex-col justify-between text-black">
                <div className="flex items-center gap-2 sm:gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-amber-100 flex items-center justify-center text-black font-bold shadow-xs flex-shrink-0">
                    <BookOpen className="w-4 h-4 text-black" />
                  </div>
                  <span className="text-[10px] sm:text-[11px] font-black text-black uppercase tracking-wider truncate">
                    HANDBOOK
                  </span>
                </div>
                <div className="pt-2 sm:pt-3">
                  <div className="text-xl sm:text-2xl font-black text-black tracking-tight leading-none">
                    6 Pages
                  </div>
                  <span className="text-[11px] font-bold text-black block mt-1 truncate">
                    Complete handbook
                  </span>
                </div>
              </div>

              {/* Tile 4: Response Latency */}
              <div className="coachpro-card rounded-[22px] p-4 sm:p-5 flex flex-col justify-between text-black">
                <div className="flex items-center gap-2 sm:gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-teal-100 flex items-center justify-center text-black font-bold shadow-xs flex-shrink-0">
                    <Zap className="w-4 h-4 text-black" />
                  </div>
                  <span className="text-[10px] sm:text-[11px] font-black text-black uppercase tracking-wider truncate">
                    LATENCY
                  </span>
                </div>
                <div className="pt-2 sm:pt-3">
                  <div className="text-xl sm:text-2xl font-black text-black tracking-tight leading-none">
                    0.2s
                  </div>
                  <span className="text-[11px] font-bold text-black block mt-1 truncate">
                    Fast local RAG engine
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Reset Confirmation Modal */}
        {resetModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200 space-y-5 animate-in fade-in zoom-in-95">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center flex-shrink-0 shadow-inner">
                  <Trash2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">
                    Reset All Data to 0?
                  </h3>
                  <p className="text-xs text-slate-500 font-bold">
                    Start fresh for newly connected WhatsApp number
                  </p>
                </div>
              </div>

              <div className="p-3.5 bg-rose-50/80 border border-rose-200 rounded-2xl text-xs font-bold text-rose-800 space-y-1.5">
                <p className="flex items-center gap-1.5 font-black text-rose-900">
                  <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                  This action will permanently reset:
                </p>
                <ul className="list-disc list-inside space-y-0.5 text-[11px] font-bold text-rose-900 pl-1">
                  <li>All previous customer conversations & chat logs</li>
                  <li>All incoming and outgoing messages</li>
                  <li>All registered customer records & handoff queues</li>
                  <li>All dashboard counters & resolution stats to 0</li>
                </ul>
              </div>

              <p className="text-xs font-bold text-slate-600">
                Your knowledge base files will remain intact, but all conversation counters will restart from <strong className="text-black">0</strong>.
              </p>

              <div className="flex items-center justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setResetModalOpen(false)}
                  disabled={resetting}
                  className="px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 font-black text-xs hover:bg-slate-100 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleResetAllData}
                  disabled={resetting}
                  className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-black text-xs shadow-md transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50 active:scale-95"
                >
                  <RotateCcw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
                  {resetting ? 'Resetting Data...' : 'Yes, Reset All to 0'}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
