'use client';

import React, { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import {
  Search,
  Bot,
  User,
  Send,
  UserCheck,
  Power,
  Phone,
  ArrowLeft,
  CheckCircle2,
  Clock,
  Sparkles
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, ConversationItem, MessageItem } from '@/lib/api';
import { formatDate, formatFullDate } from '@/lib/utils';

function ConversationsContent() {
  const searchParams = useSearchParams();
  const initialId = searchParams.get('id');

  const [conversations, setConversations] = useState<ConversationItem[]>([]);
  const [selectedConvId, setSelectedConvId] = useState<string | null>(initialId);
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [inputText, setInputText] = useState('');
  const [searchFilter, setSearchFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [mobileChatOpen, setMobileChatOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadConversations = async () => {
    try {
      const data = await api.listConversations();
      setConversations(data);
      if (!selectedConvId && data.length > 0) {
        setSelectedConvId(data[0].id);
      }
    } catch (e) {
      console.error('Error fetching conversations:', e);
    }
  };

  const loadMessages = async (convId: string) => {
    setLoading(true);
    try {
      const msgs = await api.getMessages(convId);
      setMessages(msgs);
    } catch (e) {
      console.error('Error fetching messages:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
    const interval = setInterval(loadConversations, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedConvId) {
      loadMessages(selectedConvId);
      const msgInterval = setInterval(() => loadMessages(selectedConvId), 4000);
      return () => clearInterval(msgInterval);
    }
  }, [selectedConvId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const activeConv = conversations.find((c) => c.id === selectedConvId);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!selectedConvId || !inputText.trim() || sending) return;

    const textToSend = inputText.trim();
    setInputText('');
    setSending(true);

    try {
      await api.sendAgentMessage(selectedConvId, textToSend, 'HUMAN');
      await loadMessages(selectedConvId);
      await loadConversations();
    } catch (err) {
      console.error('Failed to send message:', err);
    } finally {
      setSending(false);
    }
  };

  const toggleAI = async () => {
    if (!activeConv) return;
    const newAiState = !activeConv.ai_enabled;
    try {
      await api.updateConversation(activeConv.id, { ai_enabled: newAiState });
      await loadConversations();
    } catch (err) {
      console.error('Failed to toggle AI:', err);
    }
  };

  const toggleHandoff = async () => {
    if (!activeConv) return;
    const newStatus = activeConv.status === 'HUMAN_HANDOFF' ? 'ACTIVE' : 'HUMAN_HANDOFF';
    const newAi = newStatus === 'ACTIVE';
    try {
      await api.updateConversation(activeConv.id, { status: newStatus, ai_enabled: newAi });
      await loadConversations();
    } catch (err) {
      console.error('Failed to update handoff:', err);
    }
  };

  const filteredConversations = conversations.filter((c) => {
    const matchesSearch =
      (c.customer_name || '').toLowerCase().includes(searchFilter.toLowerCase()) ||
      (c.customer_phone || '').includes(searchFilter) ||
      (c.last_message || '').toLowerCase().includes(searchFilter.toLowerCase());

    if (statusFilter === 'ALL') return matchesSearch;
    return matchesSearch && c.status === statusFilter;
  });

  return (
    <div className="flex-1 flex flex-col min-w-0 h-[calc(100vh-100px)] sm:h-[calc(100vh-110px)] max-h-[860px] text-slate-900">
      <Header
        title="Live WhatsApp Inbox"
        subtitle="Customer Conversations & Live Interventions"
      />

      <div className="flex-1 px-3 sm:px-6 md:px-8 pb-3 sm:pb-5 flex min-h-0 overflow-hidden text-slate-900">
        <div className="coachpro-card w-full rounded-2xl sm:rounded-[22px] overflow-hidden flex flex-col md:flex-row h-full min-h-0 text-slate-900 border border-slate-200 shadow-sm bg-white">
          {/* Left Side: Conversations List */}
          <div
            className={`w-full md:w-72 lg:w-80 flex-shrink-0 border-r border-slate-200 flex flex-col h-full min-h-0 bg-slate-50/40 text-slate-900 ${
              mobileChatOpen ? 'hidden md:flex' : 'flex'
            }`}
          >
            {/* Search & Filter Bar */}
            <div className="p-2.5 sm:p-3 border-b border-slate-200 space-y-2 bg-white">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search by name, phone, message..."
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-teal-600 focus:bg-white transition-all"
                />
              </div>

              {/* Filter Tabs */}
              <div className="flex gap-1 text-[11px] font-bold">
                {['ALL', 'ACTIVE', 'HUMAN_HANDOFF'].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setStatusFilter(tab)}
                    className={`px-2.5 py-0.5 rounded-lg text-[10.5px] transition-all cursor-pointer ${
                      statusFilter === tab
                        ? 'bg-gradient-to-r from-teal-800 to-emerald-600 text-white shadow-xs font-bold'
                        : 'hover:bg-slate-200/70 text-slate-600'
                    }`}
                  >
                    {tab === 'HUMAN_HANDOFF' ? 'Handoffs' : tab === 'ALL' ? 'All' : 'Active'}
                  </button>
                ))}
              </div>
            </div>

            {/* Conversations Scroll View */}
            <div className="flex-1 min-h-0 overflow-y-auto divide-y divide-slate-100 text-slate-900">
              {filteredConversations.length === 0 ? (
                <div className="p-6 text-center text-slate-500 font-medium text-xs">
                  No matching conversations found.
                </div>
              ) : (
                filteredConversations.map((conv) => {
                  const isSelected = conv.id === selectedConvId;
                  return (
                    <button
                      key={conv.id}
                      onClick={() => {
                        setSelectedConvId(conv.id);
                        setMobileChatOpen(true);
                      }}
                      className={`w-full text-left p-2.5 sm:p-3 transition-all flex items-start gap-2.5 hover:bg-slate-100/60 cursor-pointer ${
                        isSelected
                          ? 'bg-teal-50/90 border-l-[3px] border-teal-700 shadow-xs'
                          : ''
                      }`}
                    >
                      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-teal-800 to-emerald-600 flex items-center justify-center text-white font-bold text-xs flex-shrink-0 shadow-xs">
                        {conv.customer_name ? conv.customer_name[0].toUpperCase() : 'C'}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <h4 className="font-bold text-xs text-slate-900 truncate">
                            {conv.customer_name || 'Customer'}
                          </h4>
                          <span className="text-[10px] text-slate-400 font-medium flex-shrink-0">
                            {formatDate(conv.last_message_at || conv.updated_at)}
                          </span>
                        </div>
                        <p className="text-[10.5px] font-mono text-slate-500 font-medium">
                          +{conv.customer_phone}
                        </p>
                        <p className="text-[11px] text-slate-600 truncate mt-0.5 font-normal">
                          {conv.last_message || 'New conversation'}
                        </p>
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Side: Active Chat View (Compact & Responsive) */}
          <div
            className={`flex-1 flex flex-col h-full min-h-0 bg-[#f8fafc] text-slate-900 ${
              mobileChatOpen ? 'flex' : 'hidden md:flex'
            }`}
          >
            {activeConv ? (
              <>
                {/* Active Chat Header */}
                <div className="px-3.5 py-2 sm:px-4 sm:py-2.5 bg-white border-b border-slate-200 flex items-center justify-between gap-2 text-slate-900 flex-shrink-0">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <button
                      onClick={() => setMobileChatOpen(false)}
                      className="md:hidden p-1.5 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
                    >
                      <ArrowLeft className="w-4 h-4 text-slate-700" />
                    </button>

                    <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-gradient-to-tr from-teal-800 to-emerald-600 flex items-center justify-center text-white font-bold text-xs flex-shrink-0 shadow-xs">
                      {activeConv.customer_name ? activeConv.customer_name[0].toUpperCase() : 'C'}
                    </div>
                    <div className="min-w-0">
                      <h4 className="font-bold text-xs sm:text-sm text-slate-900 leading-tight truncate">
                        {activeConv.customer_name || 'Customer'}
                      </h4>
                      <p className="text-[10px] sm:text-[10.5px] font-mono text-slate-500 truncate">
                        +{activeConv.customer_phone}
                      </p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <button
                      onClick={toggleAI}
                      className={`px-2.5 py-1 rounded-lg text-[10.5px] sm:text-xs font-bold transition-all flex items-center gap-1 cursor-pointer ${
                        activeConv.ai_enabled
                          ? 'bg-emerald-100 text-emerald-900 border border-emerald-300'
                          : 'bg-slate-200 text-slate-700'
                      }`}
                      title="Toggle AI automated replies"
                    >
                      <Bot className="w-3 h-3 text-current" />
                      <span>{activeConv.ai_enabled ? 'AI Active' : 'AI Paused'}</span>
                    </button>

                    <button
                      onClick={toggleHandoff}
                      className={`px-2.5 py-1 rounded-lg text-[10.5px] sm:text-xs font-bold transition-all flex items-center gap-1 cursor-pointer ${
                        activeConv.status === 'HUMAN_HANDOFF'
                          ? 'bg-rose-100 text-rose-900 border border-rose-300'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                      }`}
                      title="Mark as human escalation"
                    >
                      <UserCheck className="w-3 h-3 text-current" />
                      <span>{activeConv.status === 'HUMAN_HANDOFF' ? 'Escalated' : 'Handoff'}</span>
                    </button>
                  </div>
                </div>

                {/* Messages Body (Compact, WhatsApp-Proportioned Bubbles) */}
                <div className="flex-1 min-h-0 overflow-y-auto p-3 sm:p-4 space-y-2.5 text-slate-900">
                  {messages.length === 0 ? (
                    <div className="py-12 text-center text-slate-500 font-medium text-xs">
                      No messages recorded in this conversation yet.
                    </div>
                  ) : (
                    messages.map((m) => {
                      const isUser = m.role === 'USER';
                      const isHumanStaff = m.role === 'HUMAN';
                      return (
                        <div
                          key={m.id}
                          className={`flex flex-col ${isUser ? 'items-start' : 'items-end'}`}
                        >
                          <div
                            className={`max-w-[85%] sm:max-w-[72%] md:max-w-[62%] px-3.5 py-2 rounded-2xl text-[12px] sm:text-[12.5px] leading-relaxed shadow-xs ${
                              isUser
                                ? 'bg-white text-slate-900 rounded-tl-xs border border-slate-200/90 font-medium'
                                : isHumanStaff
                                ? 'bg-slate-800 text-white rounded-tr-xs font-normal'
                                : 'bg-gradient-to-r from-teal-800 to-emerald-700 text-white rounded-tr-xs font-normal shadow-xs'
                            }`}
                          >
                            <div className="whitespace-pre-line">{m.content}</div>
                          </div>
                          <span className="text-[9.5px] text-slate-500 font-medium mt-0.5 px-1">
                            {formatDate(m.created_at)} • {isUser ? 'Customer' : isHumanStaff ? 'Staff' : 'Dhoodh Plus AI'}
                          </span>
                        </div>
                      );
                    })
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Bar (Compact & Sleek) */}
                <form
                  onSubmit={handleSendMessage}
                  className="p-2 sm:p-2.5 bg-white border-t border-slate-200 flex items-center gap-2 flex-shrink-0"
                >
                  <input
                    type="text"
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    placeholder="Type human reply to customer on WhatsApp..."
                    className="flex-1 px-3.5 py-2 rounded-xl border border-slate-200 focus:border-teal-600 bg-slate-50 text-xs font-normal text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white transition-all"
                  />
                  <button
                    type="submit"
                    disabled={sending || !inputText.trim()}
                    className="w-8 h-8 sm:w-9 sm:h-9 flex items-center justify-center bg-gradient-to-r from-teal-800 to-emerald-600 hover:opacity-90 active:scale-95 text-white rounded-xl shadow-xs transition-all flex-shrink-0 disabled:opacity-40 cursor-pointer"
                    title="Send WhatsApp Message"
                  >
                    <Send className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                  </button>
                </form>
              </>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 p-8 text-center">
                <Bot className="w-10 h-10 text-slate-400 mb-2" />
                <p className="font-bold text-xs sm:text-sm text-slate-800">Select a conversation</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Choose a chat on the left to view messages and reply.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ConversationsPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-slate-50 flex items-center justify-center font-bold text-black">Loading conversations...</div>}>
      <ConversationsContent />
    </Suspense>
  );
}

