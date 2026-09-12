import Link from 'next/link';
import {
  ShieldAlert,
  ArrowRight,
  TrendingUp,
  Clock,
  AlertTriangle,
  Mail,
  Zap,
  CheckCircle2,
  Lock,
} from 'lucide-react';

export default function LandingPage() {
  const steps = [
    {
      stage: '01',
      title: 'Gentle Payment Reminder',
      trigger: 'Day 3 Overdue',
      tone: 'Friendly & Courteous',
      desc: 'Automated courteous reminder with frictionless one-click Stripe payment link to capture simple oversights.',
      color: 'border-blue-500 bg-blue-50/50 text-blue-700',
    },
    {
      stage: '02',
      title: 'Polite Follow-up',
      trigger: 'Day 7 Overdue',
      tone: 'Formal & Direct',
      desc: 'Reminds accounting teams of overdue balance with updated statement and direct billing contact request.',
      color: 'border-amber-500 bg-amber-50/50 text-amber-700',
    },
    {
      stage: '03',
      title: 'Firm Demand & Late Fees',
      trigger: 'Day 14 Overdue',
      tone: 'Urgent & Serious',
      desc: 'Notifies client of impending late fee assessments and escalates to finance leadership.',
      color: 'border-orange-500 bg-orange-50/50 text-orange-700',
    },
    {
      stage: '04',
      title: 'Service Suspension Warning',
      trigger: 'Day 30 Overdue',
      tone: 'Critical Action',
      desc: 'Final 48-hour legal demand before automated account pause and external collections handoff.',
      color: 'border-rose-500 bg-rose-50/50 text-rose-700',
    },
  ];

  const features = [
    {
      icon: Zap,
      title: 'Stripe Webhook Sync',
      desc: 'Real-time synchronization halts reminders the second an invoice is paid—no awkward reminder after payment.',
    },
    {
      icon: Clock,
      title: 'Autonomous Cadence Sweeps',
      desc: 'APScheduler runs daily background audits to detect delinquent balances and trigger rule-based progressions.',
    },
    {
      icon: Mail,
      title: 'High-Deliverability Resend',
      desc: 'DKIM-verified transactional email delivery ensures your payment demands land directly in the primary inbox.',
    },
    {
      icon: TrendingUp,
      title: 'Accelerate Cashflow & DSO',
      desc: 'Reduce Days Sales Outstanding (DSO) by an average of 42% without hiring manual accounts receivable staff.',
    },
  ];

  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-slate-200 bg-white py-20 sm:py-28">
        <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:16px_16px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-40 pointer-events-none" />
        <div className="relative mx-auto max-w-5xl px-4 text-center sm:px-6 lg:px-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3.5 py-1 text-xs font-semibold text-indigo-700 mb-6">
            <span className="flex h-2 w-2 rounded-full bg-indigo-600 animate-ping" />
            Autonomous Accounts Receivable Engine
          </div>

          <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-6xl">
            Stop Chasing Unpaid Invoices.{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 to-violet-600">
              Automate Escalations.
            </span>
          </h1>

          <p className="mx-auto mt-6 max-w-2xl text-lg text-slate-600 leading-relaxed">
            Eliminate awkward debtor conversations. Our intelligent escalator applies graduated tone, late fee notices, and service suspensions based on customizable cadence rules.
          </p>

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-6 py-3 text-base font-semibold text-white shadow-lg shadow-indigo-200 hover:bg-indigo-500 transition-all hover:-translate-y-0.5"
            >
              Open Live Dashboard
              <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              href="/settings"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-6 py-3 text-base font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
            >
              Configure Cadence Rules
            </Link>
          </div>

          {/* Quick Stats Bar */}
          <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto pt-8 border-t border-slate-100">
            <div>
              <div className="text-2xl font-bold text-slate-900">42%</div>
              <div className="text-xs text-slate-500">Faster DSO Recovery</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">100%</div>
              <div className="text-xs text-slate-500">Autonomous Sweeps</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">4 Tiers</div>
              <div className="text-xs text-slate-500">Graduated Escalation</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-900">&lt; 30s</div>
              <div className="text-xs text-slate-500">Stripe Sync Latency</div>
            </div>
          </div>
        </div>
      </section>

      {/* Escalation Sequence Visualizer */}
      <section className="py-20 bg-slate-50 border-b border-slate-200">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-xs font-semibold tracking-wider text-indigo-600 uppercase">
              Predictable AR Workflow
            </h2>
            <p className="mt-2 text-3xl font-bold text-slate-900 sm:text-4xl">
              Multi-tiered Graduated Escalation Sequence
            </p>
            <p className="mt-4 text-slate-600 text-sm sm:text-base">
              From gentle nudges to legal notices, protect your customer relationships while guaranteeing overdue revenue is retrieved.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {steps.map((step) => (
              <div
                key={step.stage}
                className={`relative flex flex-col rounded-2xl border bg-white p-6 shadow-sm transition-all hover:shadow-md ${step.color}`}
              >
                <div className="flex items-center justify-between mb-4">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-white/80 border border-current">
                    STAGE {step.stage}
                  </span>
                  <span className="text-xs font-semibold">{step.trigger}</span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{step.title}</h3>
                <div className="text-xs font-medium text-slate-500 mb-3">Tone: {step.tone}</div>
                <p className="text-xs text-slate-600 leading-relaxed flex-1">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Grid */}
      <section className="py-20 bg-white">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feat, i) => {
              const Icon = feat.icon;
              return (
                <div key={i} className="flex flex-col">
                  <div className="h-10 w-10 flex items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 mb-4">
                    <Icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900 mb-2">{feat.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{feat.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="bg-indigo-900 py-16 text-white text-center">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold">Ready to recover overdue cash flow?</h2>
          <p className="mt-3 text-indigo-200 text-sm sm:text-base">
            Connect your Stripe account or inspect mock overdue invoices in the dashboard right now.
          </p>
          <div className="mt-6">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-sm font-bold text-indigo-900 shadow-md hover:bg-indigo-50 transition-colors"
            >
              Enter Dashboard
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
