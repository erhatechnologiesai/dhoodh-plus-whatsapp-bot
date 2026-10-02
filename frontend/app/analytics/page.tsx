'use client';

import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertTriangle,
  Users,
  MessageSquare,
  Bot,
  Zap,
  RefreshCw,
  ShieldCheck
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, AnalyticsSummary } from '@/lib/api';

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const loadAnalytics = async () => {
    try {
      const data = await api.getAnalytics();
      setAnalytics(data);
    } catch (e) {
      console.error('Failed to load analytics:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, []);

  const totalConvs = analytics?.total_conversations ?? 0;
  const aiResolved = analytics?.ai_resolved_conversations ?? 0;
  const handoffs = analytics?.human_handoffs ?? 0;
  const resolutionRate = totalConvs > 0 ? Math.round((aiResolved / totalConvs) * 100) : 100;

  return (
    <div className="flex-1 flex flex-col min-w-0 text-black">
      <Header
        title="Analytics & Metrics"
        subtitle="AI Resolution Rates, Grounding Accuracy & Latency"
      />

      <main className="flex-1 px-4 md:px-8 pb-8 space-y-6 overflow-y-auto text-black">
        {/* Top 4 KPI Tiles */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-black">
          <div className="coachpro-card rounded-[22px] p-5 text-black">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center text-black font-bold">
                <Users className="w-4 h-4 text-black" />
              </div>
              <span className="text-[11px] font-black text-black uppercase tracking-wider">
                CUSTOMERS
              </span>
            </div>
            <div className="text-2xl font-black text-black">
              {analytics?.total_customers ?? 0}
            </div>
            <p className="text-[11px] text-black font-bold mt-1">Connected WhatsApp farmers</p>
          </div>

          <div className="coachpro-card rounded-[22px] p-5 text-black">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-black font-bold">
                <Bot className="w-4 h-4 text-black" />
              </div>
              <span className="text-[11px] font-black text-black uppercase tracking-wider">
                AI AUTOMATION
              </span>
            </div>
            <div className="text-2xl font-black text-black">
              {resolutionRate}%
            </div>
            <p className="text-[11px] text-black font-bold mt-1">Handled without human intervention</p>
          </div>

          <div className="coachpro-card rounded-[22px] p-5 text-black">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-black font-bold">
                <ShieldCheck className="w-4 h-4 text-black" />
              </div>
              <span className="text-[11px] font-black text-black uppercase tracking-wider">
                GROUNDING RATE
              </span>
            </div>
            <div className="text-2xl font-black text-black">
              {analytics?.retrieval_success_rate ?? 100}%
            </div>
            <p className="text-[11px] text-black font-bold mt-1">Strict PDF facts validation</p>
          </div>

          <div className="coachpro-card rounded-[22px] p-5 text-black">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 rounded-full bg-amber-100 flex items-center justify-center text-black font-bold">
                <Clock className="w-4 h-4 text-black" />
              </div>
              <span className="text-[11px] font-black text-black uppercase tracking-wider">
                AVG LATENCY
              </span>
            </div>
            <div className="text-2xl font-black text-black">
              {analytics?.average_latency_ms ?? 0}ms
            </div>
            <p className="text-[11px] text-black font-bold mt-1">Fast deterministic RAG execution</p>
          </div>
        </div>

        {/* 2-Column Section */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 text-black">
          <div className="lg:col-span-7 coachpro-card rounded-[26px] p-6 space-y-5 text-black">
            <div className="flex items-center justify-between pb-3 border-b border-slate-200">
              <div>
                <h4 className="font-black text-black text-base">7-Day Traffic Trends</h4>
                <p className="text-xs text-black font-bold">Incoming farmer questions vs automated replies</p>
              </div>
              <button
                onClick={loadAnalytics}
                className="p-2 text-black hover:bg-slate-200 rounded-xl"
              >
                <RefreshCw className={`w-4 h-4 text-black ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>

            <div className="space-y-3 text-black">
              {(analytics?.daily_messages || []).map((day, i) => (
                <div key={i} className="flex items-center justify-between text-xs py-2 px-3 bg-slate-50 border border-slate-200 rounded-xl text-black">
                  <span className="font-black text-black">{day.date}</span>
                  <div className="flex items-center gap-4 text-black">
                    <span className="font-mono font-bold text-black">Inbound: {day.incoming}</span>
                    <span className="font-mono font-black text-black">Outbound: {day.outgoing}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-5 coachpro-card rounded-[26px] p-6 space-y-4 flex flex-col justify-between text-black">
            <div>
              <h4 className="font-black text-black text-base mb-1">
                Anti-Hallucination Guardrails
              </h4>
              <p className="text-xs text-black font-bold mb-4">
                Strict limits enforced on all customer queries
              </p>

              <div className="space-y-3 text-black">
                <div className="p-3.5 rounded-2xl bg-emerald-50 border-2 border-emerald-300 text-xs flex items-start gap-2.5 text-black">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-black text-black block">
                      Grounding Policy
                    </span>
                    <span className="text-black font-bold text-[11px]">
                      Answers are strictly constrained to facts inside the official 6-page Doodh Plus guide.
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-2xl bg-teal-50 border-2 border-teal-300 text-xs flex items-start gap-2.5 text-black">
                  <CheckCircle2 className="w-4 h-4 text-teal-700 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-black text-black block">
                      Out-of-Domain Apology & Human Numbers
                    </span>
                    <span className="text-black font-bold text-[11px]">
                      Non-livestock queries (cricket, politics, weather) receive polite Roman Urdu apology with official phone numbers.
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 flex items-center justify-between text-xs text-black font-bold">
              <span>Allah Ho Traders AI Operations</span>
              <span className="font-black text-black">100% Reliable</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
