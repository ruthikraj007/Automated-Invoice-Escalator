'use client';

import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import {
  CheckCircle2,
  Shield,
  Zap,
  Lock,
  ArrowRight,
  Clock,
  Sparkles,
  Check,
} from 'lucide-react';

function PricingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isPaywalled = searchParams?.get('paywall') === 'true';
  const [loading, setLoading] = useState(false);

  const handleStartTrial = async () => {
    try {
      setLoading(true);
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        router.push('/dashboard?subscribed=true');
      }
    } catch (err) {
      console.error('Checkout error:', err);
      router.push('/dashboard?subscribed=true');
    } finally {
      setLoading(false);
    }
  };

  const features = [
    'Autonomous 6-Hour Escalation Sweeps',
    '3-Tier Graduated Email Cadence (Days 3, 7, 14)',
    'Responsive HTML Templates with dynamic variables',
    'Stripe Webhook Real-Time Payment Synchronization',
    'Immutable Audit Trail for all notifications',
    'Custom Email Subject & Body Template Editor',
    'Stripe Restricted API Key Vault',
    'Priority Deliverability via Resend',
  ];

  return (
    <div className="py-16 sm:py-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        {/* Paywall Banner if redirected */}
        {isPaywalled && (
          <div className="mb-8 rounded-xl border border-amber-200 bg-amber-50 p-4 text-amber-900 shadow-sm flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Lock className="h-5 w-5 text-amber-600 flex-shrink-0" />
              <div>
                <p className="font-semibold text-sm">Subscription Required</p>
                <p className="text-xs text-amber-700 mt-0.5">
                  The Collections & Escalation Console is exclusive to Pro Automation members. Start your 14-day free trial below to continue.
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 border border-indigo-200 px-3 py-1 text-xs font-semibold text-indigo-700 mb-4">
            <Sparkles className="h-3.5 w-3.5" />
            Simple, Transparent Pricing
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-5xl">
            Automate AR Recovery on Autopilot
          </h1>
          <p className="mt-4 text-base sm:text-lg text-slate-600">
            One simple plan. Zero debtor awkwardness. Recover delinquent revenue with graduated escalation cadences.
          </p>
        </div>

        {/* Pricing Card */}
        <div className="mt-12 max-w-lg mx-auto rounded-2xl border-2 border-indigo-600 bg-white p-8 shadow-xl shadow-indigo-100 relative">
          <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 rounded-full bg-indigo-600 px-4 py-1 text-xs font-bold text-white uppercase tracking-wider">
            Most Popular
          </div>

          <div className="flex items-center justify-between pb-6 border-b border-slate-100">
            <div>
              <h3 className="text-xl font-bold text-slate-900">Pro Automation Plan</h3>
              <p className="text-xs text-slate-500 mt-1">For growing businesses & agencies</p>
            </div>
            <div className="text-right">
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-slate-900">$29</span>
                <span className="text-sm font-semibold text-slate-500">/mo</span>
              </div>
              <span className="text-[11px] font-medium text-emerald-600">14-Day Free Trial</span>
            </div>
          </div>

          <div className="my-6">
            <button
              onClick={handleStartTrial}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-6 py-3.5 text-sm font-bold text-white shadow-md shadow-indigo-200 hover:bg-indigo-500 disabled:opacity-50 transition-all hover:-translate-y-0.5"
            >
              {loading ? 'Activating Pro Trial...' : 'Start 14-Day Free Trial'}
              <ArrowRight className="h-4 w-4" />
            </button>
            <p className="text-center text-[11px] text-slate-400 mt-2">
              No immediate charge. Cancel anytime with one click.
            </p>
          </div>

          <div className="space-y-3 pt-2">
            <p className="text-xs font-semibold text-slate-900 uppercase tracking-wide">
              Everything included:
            </p>
            {features.map((feat, i) => (
              <div key={i} className="flex items-start gap-2.5 text-xs text-slate-600">
                <Check className="h-4 w-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                <span>{feat}</span>
              </div>
            ))}
          </div>

          <div className="mt-8 rounded-lg bg-slate-50 p-4 border border-slate-200 text-xs text-slate-500 flex items-center gap-3">
            <Shield className="h-6 w-6 text-indigo-600 flex-shrink-0" />
            <span>
              Powered by Stripe Billing. Enterprise-grade 256-bit encryption for all connected payment credentials.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PricingPage() {
  return (
    <Suspense fallback={<div className="p-12 text-center text-slate-500">Loading plan options...</div>}>
      <PricingContent />
    </Suspense>
  );
}
