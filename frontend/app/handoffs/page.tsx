'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  UserCheck,
  AlertTriangle,
  MessageSquare,
  CheckCircle2,
  RefreshCw,
  Phone,
  ArrowRight
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, ConversationItem } from '@/lib/api';
import { formatFullDate } from '@/lib/utils';

export default function HumanHandoffsPage() {
  const [handoffs, setHandoffs] = useState<ConversationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadHandoffs = async () => {
    try {
      const data = await api.listConversations('HUMAN_HANDOFF');
      setHandoffs(data);
    } catch (err) {
      console.error('Failed to load handoffs:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHandoffs();
    const interval = setInterval(loadHandoffs, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await api.updateConversation(id, { status: 'ACTIVE', ai_enabled: true });
      await loadHandoffs();
    } catch (err) {
      console.error('Failed to resolve handoff:', err);
    }
  };

  return (
    <div className="flex-1 flex flex-col min-w-0 text-black">
      <Header
        title="Human Escalations"
        subtitle="Customer Support Requests Requiring Staff Attention"
      />

      <main className="flex-1 px-4 md:px-8 pb-8 space-y-6 overflow-y-auto text-black">
        <div className="coachpro-card rounded-[26px] p-6 space-y-6 text-black">
          <div className="flex items-center justify-between pb-4 border-b border-slate-200">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-2xl bg-amber-100 text-black flex items-center justify-center font-bold text-xs">
                <AlertTriangle className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <h4 className="font-black text-black text-base">
                  Active Escalation Queue
                </h4>
                <p className="text-xs text-black font-bold">
                  {handoffs.length} conversation(s) pending human response
                </p>
              </div>
            </div>

            <button
              onClick={loadHandoffs}
              disabled={loading}
              className="px-4 py-2 rounded-2xl bg-white border border-slate-200 text-xs font-black text-black hover:bg-slate-50 shadow-sm flex items-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Queue
            </button>
          </div>

          {handoffs.length === 0 ? (
            <div className="py-16 text-center text-black">
              <CheckCircle2 className="w-12 h-12 mx-auto text-emerald-600 mb-2" />
              <p className="font-black text-black text-sm">Escalation Queue Clear</p>
              <p className="text-xs text-black font-bold mt-1 max-w-sm mx-auto">
                All customer inquiries are being successfully handled by the Doodh Plus AI Assistant.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-black">
              {handoffs.map((h) => (
                <div
                  key={h.id}
                  className="bg-white rounded-[22px] p-5 border-2 border-amber-300 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between text-black"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-black text-black text-sm">
                        {h.customer_name || 'Customer'}
                      </span>
                      <span className="text-[10px] font-black bg-amber-100 text-black px-2.5 py-0.5 rounded-full border border-amber-300">
                        Staff Needed
                      </span>
                    </div>

                    <p className="text-xs font-mono text-black font-black mb-2">
                      +{h.customer_phone}
                    </p>

                    <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-xs text-black font-bold mb-4">
                      <span className="text-[10px] uppercase font-black text-black block mb-0.5">
                        Customer Request:
                      </span>
                      &ldquo;{h.last_message || 'Agent requested'}&rdquo;
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t border-slate-200 gap-2">
                    <button
                      onClick={() => handleResolve(h.id)}
                      className="px-3 py-1.5 rounded-xl bg-emerald-100 hover:bg-emerald-200 text-black text-xs font-black transition-colors border border-emerald-300"
                    >
                      Resume AI
                    </button>
                    <Link
                      href={`/conversations?id=${h.id}`}
                      className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-xl bg-gradient-to-r from-teal-800 to-emerald-600 hover:opacity-95 text-white text-xs font-black shadow-sm transition-all"
                    >
                      <MessageSquare className="w-3.5 h-3.5 text-white" />
                      Take Over Chat
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
