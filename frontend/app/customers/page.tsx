'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  Users,
  Search,
  MessageSquare,
  Phone,
  RefreshCw,
  ArrowUpRight
} from 'lucide-react';
import { Header } from '@/components/Header';
import { api, CustomerItem } from '@/lib/api';
import { formatFullDate } from '@/lib/utils';

export default function CustomersPage() {
  const [customers, setCustomers] = useState<CustomerItem[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  const loadCustomers = async () => {
    try {
      const data = await api.listCustomers();
      setCustomers(data);
    } catch (err) {
      console.error('Failed to load customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCustomers();
  }, []);

  const filtered = customers.filter(
    (c) =>
      (c.name || '').toLowerCase().includes(search.toLowerCase()) ||
      (c.whatsapp_number || '').includes(search)
  );

  return (
    <div className="flex-1 flex flex-col min-w-0 text-black">
      <Header
        title="Customers Directory"
        subtitle="Registered WhatsApp Contacts & Dairy Farmers"
      />

      <main className="flex-1 px-4 md:px-8 pb-8 space-y-6 overflow-y-auto text-black">
        <div className="coachpro-card rounded-[26px] p-6 space-y-6 text-black">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <div className="relative flex-1 max-w-md">
              <Search className="w-4 h-4 absolute left-3.5 top-3.5 text-black" />
              <input
                type="text"
                placeholder="Search customers by name or phone..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border-2 border-slate-300 rounded-2xl text-xs font-black text-black focus:outline-none"
              />
            </div>

            <button
              onClick={loadCustomers}
              disabled={loading}
              className="px-4 py-2 rounded-2xl bg-white border border-slate-200 text-xs font-black text-black hover:bg-slate-50 shadow-sm flex items-center justify-center gap-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Refresh Directory
            </button>
          </div>

          {filtered.length === 0 ? (
            <div className="py-12 text-center text-black">
              <Users className="w-12 h-12 mx-auto mb-2 text-black" />
              <p className="text-sm font-black text-black">No customers found.</p>
              <p className="text-xs text-black font-bold mt-1">
                New contacts are automatically registered when customers message the bot.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto text-black">
              <table className="w-full text-left text-xs text-black">
                <thead>
                  <tr className="border-b-2 border-slate-200 text-[11px] font-black text-black uppercase tracking-wider">
                    <th className="py-3 px-3">CUSTOMER</th>
                    <th className="py-3 px-3">WHATSAPP NUMBER</th>
                    <th className="py-3 px-3">FIRST SEEN</th>
                    <th className="py-3 px-3 text-right">ACTION</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 text-black">
                  {filtered.map((c) => (
                    <tr key={c.id} className="hover:bg-teal-50/50 transition-colors text-black">
                      <td className="py-3.5 px-3">
                        <div className="flex items-center gap-3">
                          <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-teal-700 to-emerald-500 text-white font-black text-xs flex items-center justify-center shadow-sm">
                            {c.name ? c.name[0].toUpperCase() : 'C'}
                          </div>
                          <div>
                            <span className="font-black text-black block text-xs sm:text-sm">
                              {c.name || 'WhatsApp Customer'}
                            </span>
                            <span className="text-[10px] text-black font-bold">
                              Verified Farmer
                            </span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 px-3 font-mono font-black text-black">
                        +{c.whatsapp_number}
                      </td>
                      <td className="py-3.5 px-3 text-black font-mono font-bold text-[11px]">
                        {formatFullDate(c.created_at)}
                      </td>
                      <td className="py-3.5 px-3 text-right">
                        <Link
                          href={`/conversations?phone=${c.whatsapp_number}`}
                          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-teal-100 hover:bg-teal-200 text-black font-black text-xs transition-colors border border-teal-300"
                        >
                          <MessageSquare className="w-3.5 h-3.5 text-black" />
                          View Chat
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
