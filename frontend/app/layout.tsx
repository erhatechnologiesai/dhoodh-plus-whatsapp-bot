import type { Metadata } from 'next';
import './globals.css';
import { NavProvider } from '@/components/NavContext';
import { AppShell } from '@/components/AppShell';

export const metadata: Metadata = {
  title: 'Dhoodh Plus - WhatsApp AI Customer Support & Operations',
  description: 'Enterprise WhatsApp AI Customer Support Agent for Allah Ho Traders powered by Doodh Plus 6-Page Knowledge Base',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased text-slate-800">
        <NavProvider>
          <AppShell>
            {children}
          </AppShell>
        </NavProvider>
      </body>
    </html>
  );
}
