'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  MessageSquare,
  BookOpen,
  Users,
  UserCheck,
  BarChart3,
  Settings,
  QrCode,
  X,
  PhoneCall,
  CheckCircle2,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useNav } from './NavContext';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Connect WhatsApp', href: '/connect', icon: QrCode },
  { name: 'Live Inbox', href: '/conversations', icon: MessageSquare },
  { name: 'Knowledge Base', href: '/knowledge', icon: BookOpen },
  { name: 'Customers', href: '/customers', icon: Users },
  { name: 'Human Handoffs', href: '/handoffs', icon: UserCheck },
  { name: 'Analytics', href: '/analytics', icon: BarChart3 },
  { name: 'AI Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isOpen, closeNav } = useNav();

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={closeNav}
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm md:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-72 md:w-64 lg:w-72 bg-white/80 md:bg-transparent backdrop-blur-2xl md:backdrop-blur-none border-r border-white/80 md:border-r md:border-slate-200/50 flex flex-col justify-between p-4 md:p-6 transition-transform duration-300 ease-in-out md:static md:translate-x-0 flex-shrink-0 select-none text-black',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div>
          {/* Brand Header: Allah Hoo Traders Official Logo & Backlink */}
          <div className="flex items-center justify-between pb-6 mb-2 border-b border-slate-200/60 md:border-none">
            <div className="flex items-center gap-3">
              {/* Allah Hoo Traders Custom Emblem Seal */}
              <Link
                href="/"
                onClick={closeNav}
                className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-emerald-900 via-teal-800 to-emerald-600 flex items-center justify-center text-white shadow-md shadow-emerald-950/25 ring-1 ring-white/70 hover:scale-105 transition-all flex-shrink-0"
              >
                <svg
                  viewBox="0 0 36 36"
                  fill="none"
                  className="w-7 h-7"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  {/* Circular Crest with Dashed Outer Ring */}
                  <circle
                    cx="18"
                    cy="18"
                    r="16"
                    stroke="rgba(255,255,255,0.4)"
                    strokeWidth="0.8"
                    strokeDasharray="2 2"
                  />
                  <circle
                    cx="18"
                    cy="18"
                    r="14"
                    stroke="#FCD34D"
                    strokeWidth="0.8"
                  />
                  {/* Golden Heritage Star on Top */}
                  <path
                    d="M18 5.8L18.9 7.8L21.1 8.1L19.5 9.7L19.9 11.9L18 10.8L16.1 11.9L16.5 9.7L14.9 8.1L17.1 7.8L18 5.8Z"
                    fill="#FCD34D"
                  />
                  {/* Bold Monogram AH */}
                  <text
                    x="18"
                    y="24"
                    textAnchor="middle"
                    fill="#FFFFFF"
                    fontSize="11"
                    fontWeight="900"
                    fontFamily="system-ui, -apple-system, BlinkMacSystemFont, sans-serif"
                    letterSpacing="0.5"
                  >
                    AH
                  </text>
                  {/* Lower Golden Curved Arc */}
                  <path
                    d="M12 26.5C14.2 28.5 21.8 28.5 24 26.5"
                    stroke="#FCD34D"
                    strokeWidth="1.2"
                    strokeLinecap="round"
                  />
                </svg>
              </Link>

              {/* Brand Typography & Erhatechnologies Backlink */}
              <div className="flex-1 min-w-0">
                <Link
                  href="/"
                  onClick={closeNav}
                  className="flex items-center gap-1.5 group"
                >
                  <span className="font-black text-black text-base sm:text-[17px] tracking-tight leading-tight block group-hover:text-teal-900 transition-colors">
                    Allah Hoo <span className="text-teal-800">Traders</span>
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse flex-shrink-0"></span>
                </Link>
                <a
                  href="https://www.erhatechnologies.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[10px] sm:text-[11px] font-bold text-black hover:text-teal-800 hover:underline mt-0.5 leading-none block transition-colors"
                >
                  powered by erha technologies
                </a>
              </div>
            </div>

            {/* Mobile Close Button */}
            <button
              onClick={closeNav}
              className="md:hidden p-2 rounded-xl text-black hover:bg-white/80 transition-colors"
            >
              <X className="w-5 h-5 text-black" />
            </button>
          </div>

          {/* Navigation Links in FULL BLACK */}
          <nav className="space-y-1.5 pt-2">
            {navigation.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={closeNav}
                  className={cn(
                    'flex items-center gap-3.5 px-4 py-3 rounded-2xl text-sm font-bold transition-all duration-200 active:scale-[0.98]',
                    isActive
                      ? 'bg-gradient-to-r from-teal-800 via-teal-700 to-emerald-600 text-white shadow-lg shadow-teal-900/20 scale-[1.02]'
                      : 'text-black hover:text-black hover:bg-white/80 hover:shadow-sm'
                  )}
                >
                  <Icon
                    className={cn(
                      'w-4 h-4 flex-shrink-0 transition-colors',
                      isActive ? 'text-white' : 'text-black'
                    )}
                  />
                  <span className={isActive ? 'text-white' : 'text-black font-bold'}>
                    {item.name}
                  </span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Bottom Support & Store Info Card - Lifted bit up with clean spacing */}
        <div className="pt-3 mt-auto mb-4 md:mb-6">
          <div className="bg-white/90 rounded-2xl p-4 border border-white shadow-sm text-black hover:shadow-md transition-all">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-black text-black uppercase tracking-wider flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                Allah Ho Traders
              </span>
              <span className="text-[10px] bg-emerald-100 text-black font-bold px-2 py-0.5 rounded-full border border-emerald-300">
                Active
              </span>
            </div>
            <p className="text-xs text-black font-bold leading-relaxed">
              Bahria Town, Lahore
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
