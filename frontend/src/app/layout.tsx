import type { Metadata } from 'next';
import './globals.css';
import Navbar from '@/components/Navbar';

export const metadata: Metadata = {
  title: 'Automated Invoice & Payment Escalator',
  description: 'Automated collection sequences, overdue invoice escalation, and Stripe payment recovery.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen flex-col bg-slate-50 antialiased">
        <Navbar />
        <main className="flex-1">{children}</main>
        <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
            <span>© 2026 EscalatePay - Automated Invoice & Payment Escalator</span>
            <span className="text-slate-400">Powered by FastAPI, Next.js, Stripe & Resend</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
