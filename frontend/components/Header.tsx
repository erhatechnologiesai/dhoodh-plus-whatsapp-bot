'use client';

import React, { useState, useEffect, useRef } from 'react';
import {
  Bell,
  Menu,
  RefreshCw,
  ShieldCheck,
  CheckCheck,
  X,
  ArrowRight,
  MessageSquare,
  CheckCircle2,
  UserCheck,
  AlertCircle,
  Bot,
  Power,
  LogOut
} from 'lucide-react';
import Link from 'next/link';
import { api, ConversationItem } from '@/lib/api';
import { useNav } from './NavContext';

function timeAgo(dateString?: string): string {
  if (!dateString) return 'Just now';
  const diffSec = Math.floor((Date.now() - new Date(dateString).getTime()) / 1000);
  if (diffSec < 60) return 'Just now';
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return `${Math.floor(diffSec / 86400)}d ago`;
}

export function Header({
  title
}: {
  title: string;
  subtitle?: string;
}) {
  const { toggleNav } = useNav();
  const [loading, setLoading] = useState(false);
  const [notifications, setNotifications] = useState<ConversationItem[]>([]);
  const [unreadCount, setUnreadCount] = useState<number>(0);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [lastReadTimestamp, setLastReadTimestamp] = useState<number>(0);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [botActive, setBotActive] = useState<boolean>(true);
  const [togglingBot, setTogglingBot] = useState<boolean>(false);
  const [waConnected, setWaConnected] = useState<boolean>(false);
  const [waPhone, setWaPhone] = useState<string | null>(null);

  const fetchWhatsAppStatus = async () => {
    try {
      const wa = await api.getWhatsAppStatus();
      if (wa && wa.connected && wa.phone) {
        setWaConnected(true);
        setWaPhone(wa.phone);
      } else {
        setWaConnected(false);
        setWaPhone(null);
      }
    } catch {
      setWaConnected(false);
      setWaPhone(null);
    }
  };

  const fetchBotStatus = async () => {
    try {
      const s = await api.getSettings();
      if (s && typeof s.bot_enabled === 'boolean') {
        setBotActive(s.bot_enabled);
      }
    } catch {
      // Ignored
    }
  };

  const handleToggleBot = async () => {
    if (togglingBot) return;
    const nextState = !botActive;
    setBotActive(nextState);
    setTogglingBot(true);
    try {
      const res = await api.toggleBot(nextState);
      if (typeof res?.bot_enabled === 'boolean') {
        setBotActive(res.bot_enabled);
      }
      if (typeof window !== 'undefined') {
        window.dispatchEvent(
          new CustomEvent('bot-status-changed', { detail: { bot_enabled: nextState } })
        );
      }
    } catch (err) {
      console.error('Failed to toggle bot status:', err);
      setBotActive(!nextState);
    } finally {
      setTogglingBot(false);
    }
  };

  const fetchLiveNotifications = async () => {
    try {
      const convs = await api.listConversations();
      if (convs && convs.length > 0) {
        setNotifications(convs.slice(0, 8));
        const unread = convs.filter(
          (c) => new Date(c.last_message_at || c.updated_at).getTime() > lastReadTimestamp
        ).length;
        setUnreadCount(unread);
      }
    } catch {
      // Keep existing notifications on temporary network hiccup
    }
  };

  const checkStatus = async () => {
    setLoading(true);
    try {
      await api.getHealth();
      await fetchBotStatus();
      await fetchWhatsAppStatus();
      await fetchLiveNotifications();
    } catch {
      // Ignored
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(() => {
      if (typeof document !== 'undefined' && document.hidden) return;
      fetchLiveNotifications();
      fetchWhatsAppStatus();
    }, 8000);

    const handleStatusSync = (e: any) => {
      if (typeof e.detail?.bot_enabled === 'boolean') {
        setBotActive(e.detail.bot_enabled);
      }
    };
    if (typeof window !== 'undefined') {
      window.addEventListener('bot-status-changed', handleStatusSync);
    }

    return () => {
      clearInterval(interval);
      if (typeof window !== 'undefined') {
        window.removeEventListener('bot-status-changed', handleStatusSync);
      }
    };
  }, [lastReadTimestamp]);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    }
    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  const handleToggleDropdown = () => {
    setIsDropdownOpen((prev) => !prev);
  };

  const handleMarkAllRead = () => {
    setLastReadTimestamp(Date.now());
    setUnreadCount(0);
  };

  const handoffCount = notifications.filter((n) => n.status === 'HUMAN_HANDOFF').length;

  return (
    <header className="px-4 md:px-8 pt-4 md:pt-6 pb-4 flex items-center justify-between gap-3 select-none flex-wrap sm:flex-nowrap relative">
      {/* Left: Clean Big Heading in FULL BLACK */}
      <div className="flex items-center gap-3">
        <h2 className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-black text-black tracking-tight">
          {title}
        </h2>
      </div>

      {/* Right: Actions & User Pill in FULL BLACK */}
      <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        {/* Master AI Bot ON/OFF Toggle Switch */}
        <button
          onClick={handleToggleBot}
          disabled={togglingBot}
          className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 py-1.5 rounded-full border shadow-sm transition-all duration-200 active:scale-95 text-xs font-black cursor-pointer select-none ${
            botActive
              ? 'bg-emerald-50 hover:bg-emerald-100/90 border-emerald-300 text-black shadow-emerald-500/10'
              : 'bg-amber-50 hover:bg-amber-100/90 border-amber-300 text-black shadow-amber-500/10'
          }`}
          title={
            botActive
              ? 'Bot is Active: AI is auto-replying. Click to turn OFF for Manual Human Mode.'
              : 'Bot is OFF: Manual Human Mode. Click to turn AI Bot ON.'
          }
          aria-label="Toggle AI Bot"
        >
          {/* Animated Status Indicator Dot */}
          <div className="relative flex items-center justify-center">
            {botActive ? (
              <>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-ping absolute opacity-75"></span>
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-600 relative"></span>
              </>
            ) : (
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 relative"></span>
            )}
          </div>

          {/* Icon */}
          {botActive ? (
            <Bot className="w-3.5 h-3.5 text-emerald-700 flex-shrink-0" />
          ) : (
            <UserCheck className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
          )}

          {/* Label Text in SOLID BLACK font-black */}
          <span className="text-black font-black text-xs hidden sm:inline">
            {botActive ? 'AI Bot: ON' : 'AI Bot: OFF (Human Mode)'}
          </span>
          <span className="text-black font-black text-xs sm:hidden">
            {botActive ? 'Bot ON' : 'Bot OFF'}
          </span>

          {/* Smooth Toggle Slider */}
          <div
            className={`w-7 h-4 flex items-center rounded-full p-0.5 transition-colors duration-200 ${
              botActive ? 'bg-emerald-600 justify-end' : 'bg-slate-300 justify-start'
            }`}
          >
            <div className="bg-white w-3 h-3 rounded-full shadow-md transform transition-transform duration-200" />
          </div>
        </button>

        {/* WhatsApp Live Status Pill */}
        <div className="hidden lg:flex items-center gap-2">
          <Link
            href="/connect"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/90 hover:bg-white active:scale-95 border border-white shadow-sm text-xs font-bold text-black transition-all"
            title={waConnected && waPhone ? `Connected: +${waPhone}` : 'WhatsApp is disconnected. Click to scan QR code.'}
          >
            {waConnected && waPhone ? (
              <>
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                <span className="text-black font-medium">WhatsApp:</span>
                <span className="text-black font-black">+{waPhone}</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse flex-shrink-0"></span>
                <span className="text-black font-medium">WhatsApp:</span>
                <span className="text-slate-600 font-bold">Not Connected</span>
              </>
            )}
          </Link>
        </div>

        {/* Refresh Sync Button */}
        <button
          onClick={checkStatus}
          disabled={loading}
          className="w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-white/90 hover:bg-white active:scale-95 border border-white flex items-center justify-center text-black shadow-sm transition-all"
          title="Refresh live status"
        >
          <RefreshCw className={`w-4 h-4 text-black ${loading ? 'animate-spin' : ''}`} />
        </button>

        {/* Live Notification Bell with Dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={handleToggleDropdown}
            className={`w-9 h-9 sm:w-10 sm:h-10 rounded-full border border-white flex items-center justify-center text-black shadow-sm transition-all active:scale-95 ${
              isDropdownOpen ? 'bg-white ring-2 ring-emerald-500/40' : 'bg-white/90 hover:bg-white'
            }`}
            title="Notifications & Incoming Inquiries"
            aria-label="Toggle notifications"
          >
            <Bell className="w-4 h-4 text-black" />
          </button>

          {/* Dynamic Badge Counter */}
          {unreadCount > 0 ? (
            <span className="absolute -top-1 -right-1 min-w-[19px] h-[19px] px-1 rounded-full bg-rose-600 text-white font-black text-[10px] flex items-center justify-center border-2 border-white ring-1 ring-rose-400 shadow-sm animate-pulse pointer-events-none">
              {unreadCount}
            </span>
          ) : (
            <span className="absolute top-1 right-1 sm:top-1.5 sm:right-1.5 w-2 sm:w-2.5 h-2 sm:h-2.5 rounded-full bg-emerald-500 border-2 border-white ring-1 ring-emerald-300 pointer-events-none"></span>
          )}

          {/* Backdrop Overlay for Mobile screens */}
          {isDropdownOpen && (
            <div
              onClick={() => setIsDropdownOpen(false)}
              className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px] sm:hidden"
            />
          )}

          {/* Responsive Notification Popover Modal */}
          {isDropdownOpen && (
            <div className="fixed inset-x-3 top-20 sm:absolute sm:inset-x-auto sm:right-0 sm:top-12 sm:w-96 rounded-[28px] bg-white/95 backdrop-blur-2xl border border-white shadow-2xl z-50 p-4 text-black animate-in fade-in zoom-in-95 duration-150 flex flex-col max-h-[82vh] select-text">
              {/* Dropdown Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-xl bg-teal-100 flex items-center justify-center text-black shadow-xs">
                    <Bell className="w-3.5 h-3.5 text-black" />
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-black text-black leading-tight">
                      Incoming WhatsApp Queries
                    </h4>
                    <p className="text-[10px] text-black font-bold">
                      {unreadCount > 0 ? `${unreadCount} new inquiries` : 'All caught up'}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1">
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="p-1.5 rounded-lg hover:bg-slate-100 text-black active:scale-95 transition-all text-[11px] font-bold flex items-center gap-1"
                      title="Mark all as read"
                    >
                      <CheckCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="hidden sm:inline">Mark read</span>
                    </button>
                  )}
                  <button
                    onClick={() => setIsDropdownOpen(false)}
                    className="p-1.5 rounded-lg hover:bg-slate-100 text-black active:scale-95 transition-all"
                    title="Close"
                  >
                    <X className="w-4 h-4 text-black" />
                  </button>
                </div>
              </div>

              {/* Scrollable Notification Items List */}
              <div className="overflow-y-auto max-h-[340px] space-y-1.5 py-2 divide-y divide-slate-100 pr-0.5">
                {notifications.length === 0 ? (
                  <div className="py-8 text-center text-xs font-bold text-black">
                    No active notifications
                  </div>
                ) : (
                  notifications.map((item) => {
                    const isConfirmed = (item.status as string) === 'ORDER_CONFIRMED';
                    const isHandoff = item.status === 'HUMAN_HANDOFF';

                    return (
                      <Link
                        key={item.id}
                        href={isHandoff ? '/handoffs' : `/conversations?id=${item.id}`}
                        onClick={() => {
                          setIsDropdownOpen(false);
                          handleMarkAllRead();
                        }}
                        className="pt-2 first:pt-0 p-2.5 rounded-2xl hover:bg-teal-50/80 active:scale-[0.98] transition-all flex items-start gap-2.5 group text-black block"
                      >
                        {/* Status Icon Avatar */}
                        <div
                          className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 shadow-xs mt-0.5 ${
                            isConfirmed
                              ? 'bg-teal-100 text-teal-800'
                              : isHandoff
                              ? 'bg-rose-100 text-rose-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {isConfirmed ? (
                            <CheckCircle2 className="w-4 h-4" />
                          ) : isHandoff ? (
                            <UserCheck className="w-4 h-4" />
                          ) : (
                            <MessageSquare className="w-4 h-4" />
                          )}
                        </div>

                        {/* Content Body */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-1 mb-0.5">
                            <span className="font-black text-xs text-black truncate group-hover:text-teal-900 transition-colors">
                              {item.customer_name || 'Customer'}
                            </span>
                            <span className="text-[10px] font-bold text-black flex-shrink-0">
                              {timeAgo(item.last_message_at || item.updated_at)}
                            </span>
                          </div>

                          <div className="flex items-center gap-1.5 text-[10px] font-mono font-bold text-black mb-1">
                            <span>+{item.customer_phone}</span>
                            <span>•</span>
                            <span
                              className={`px-1.5 py-0.2 rounded-full text-[9px] font-black ${
                                isConfirmed
                                  ? 'bg-teal-200/70 text-black'
                                  : isHandoff
                                  ? 'bg-amber-200/80 text-black'
                                  : 'bg-emerald-200/70 text-black'
                              }`}
                            >
                              {isConfirmed ? 'Order Booked' : isHandoff ? 'Escalation' : 'AI Responded'}
                            </span>
                          </div>

                          <p className="text-xs text-black font-bold line-clamp-2 leading-snug">
                            {item.last_message || 'New customer inquiry received'}
                          </p>
                        </div>
                      </Link>
                    );
                  })
                )}
              </div>

              {/* Dropdown Footer Links */}
              <div className="pt-2.5 border-t border-slate-200 flex items-center justify-between text-xs font-black text-black">
                <Link
                  href="/conversations"
                  onClick={() => setIsDropdownOpen(false)}
                  className="hover:underline flex items-center gap-1 active:scale-95 text-black"
                >
                  Live Inbox <ArrowRight className="w-3.5 h-3.5" />
                </Link>
                <Link
                  href="/handoffs"
                  onClick={() => setIsDropdownOpen(false)}
                  className="hover:underline flex items-center gap-1 active:scale-95 text-black"
                >
                  Escalations ({handoffCount}) <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}
        </div>

        {/* User Profile Pill in FULL BLACK */}
        <div className="flex items-center gap-2 pl-1 pr-2.5 sm:pr-3 py-1 rounded-full bg-white/90 border border-white shadow-sm">
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-black text-white flex items-center justify-center font-black text-xs shadow-inner flex-shrink-0">
            AH
          </div>
          <div className="hidden sm:block text-left">
            <span className="text-xs font-black text-black leading-none block">
              Allah Ho Traders
            </span>
            <span className="text-[10px] text-black font-bold block mt-0.5">
              Official Admin
            </span>
          </div>
        </div>

        {/* Logout Button */}
        <button
          onClick={() => api.logout()}
          title="Sign Out of Admin Portal"
          className="p-1.5 sm:px-3 sm:py-1.5 rounded-full bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 font-black text-xs flex items-center gap-1.5 shadow-sm active:scale-95 transition-all flex-shrink-0 cursor-pointer"
        >
          <LogOut className="w-3.5 h-3.5 text-rose-600" />
          <span className="hidden sm:inline">Logout</span>
        </button>

        {/* Mobile Hamburger Button */}
        <button
          onClick={toggleNav}
          className="md:hidden p-2 rounded-2xl bg-white/90 border border-white text-black shadow-sm hover:bg-white active:scale-95 transition-all flex items-center justify-center w-9 h-9 flex-shrink-0"
          aria-label="Open menu"
        >
          <Menu className="w-5 h-5 text-black" />
        </button>
      </div>
    </header>
  );
}
