'use client';

import React, { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Sidebar } from '@/components/Sidebar';
import { api } from '@/lib/api';

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checkedAuth, setCheckedAuth] = useState(false);

  const isLoginPage = pathname === '/login';

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const isAuth = api.isAuthenticated();
      if (!isAuth && !isLoginPage) {
        router.push('/login');
      }
      setCheckedAuth(true);
    }
  }, [pathname, isLoginPage, router]);

  if (isLoginPage) {
    return <main className="min-h-screen w-full">{children}</main>;
  }

  return (
    <div className="min-h-screen w-full p-1 sm:p-3 md:p-5 lg:p-6 flex items-center justify-center">
      <div className="coachpro-shell w-full max-w-[1580px] rounded-[24px] sm:rounded-[30px] md:rounded-[36px] overflow-hidden flex flex-col md:flex-row min-h-[94vh]">
        <Sidebar />
        <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
