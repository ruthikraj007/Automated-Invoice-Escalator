'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ShieldAlert, LayoutDashboard, Sliders, Activity, ExternalLink, Sparkles } from 'lucide-react';
import { checkBackendHealth } from '@/lib/api';

export default function Navbar() {
  const pathname = usePathname();
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    checkBackendHealth().then((res) => setIsBackendHealthy(res.healthy));
    const interval = setInterval(() => {
      checkBackendHealth().then((res) => setIsBackendHealthy(res.healthy));
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { href: '/', label: 'Overview', icon: ShieldAlert },
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/settings', label: 'Settings', icon: Sliders },
    { href: '/pricing', label: 'Pricing', icon: Sparkles },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold shadow-sm shadow-indigo-200">
              <ShieldAlert className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-slate-900 text-base leading-none tracking-tight">
                EscalatePay
              </span>
              <span className="text-[10px] text-slate-500 font-medium tracking-wide uppercase">
                Invoice Escalator
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-100 text-indigo-600'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-full border border-slate-200 text-xs">
            <span
              className={`h-2 w-2 rounded-full ${
                isBackendHealthy === null
                  ? 'bg-amber-400 animate-pulse'
                  : isBackendHealthy
                  ? 'bg-emerald-500'
                  : 'bg-rose-500'
              }`}
            />
            <span className="text-slate-600 hidden sm:inline">
              FastAPI:{' '}
              {isBackendHealthy === null
                ? 'Connecting...'
                : isBackendHealthy
                ? 'Online'
                : 'Offline'}
            </span>
          </div>

          <Link
            href="/dashboard"
            className="hidden sm:inline-flex items-center justify-center rounded-lg bg-indigo-600 px-3.5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 transition-colors"
          >
            Launch Console
          </Link>
        </div>
      </div>
    </header>
  );
}
