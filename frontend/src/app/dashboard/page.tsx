'use client';

import { useEffect, useState } from 'react';
import {
  AlertTriangle,
  TrendingUp,
  Zap,
  CheckCircle2,
  RefreshCw,
  Search,
  ExternalLink,
  Clock,
  Sparkles,
  ShieldCheck,
  X,
} from 'lucide-react';
import { MetricCard } from '@/components/MetricCard';
import { StatusBadge, EscalationTierBadge } from '@/components/StatusBadge';
import { getMetricsSummary, getTrackedInvoices, triggerEscalationRun } from '@/lib/api';
import { MetricSummary, TrackedInvoice } from '@/lib/types';
import Link from 'next/link';

export default function DashboardPage() {
  const [metrics, setMetrics] = useState<MetricSummary | null>(null);
  const [invoices, setInvoices] = useState<TrackedInvoice[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [runningEscalation, setRunningEscalation] = useState<boolean>(false);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string; submessage?: string } | null>(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState<boolean>(false);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [m, invs] = await Promise.all([
        getMetricsSummary(),
        getTrackedInvoices(),
      ]);
      setMetrics(m);
      setInvoices(invs);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const handleRunEscalation = async () => {
    try {
      setRunningEscalation(true);
      const res = await triggerEscalationRun();
      setToast({
        type: 'success',
        message: `Escalation Run Finished Successfully!`,
        submessage: `Scanned ${res.total_overdue_scanned} overdue invoices. Executed ${res.escalations_executed} tier escalations (${res.invoices_skipped} skipped).`,
      });
      await loadDashboardData();
    } catch (err: any) {
      setToast({
        type: 'error',
        message: 'Escalation Run Failed',
        submessage: err.message || 'Check backend connection.',
      });
    } finally {
      setRunningEscalation(false);
    }
  };

  // Filter and search
  const filteredInvoices = invoices.filter((inv) => {
    const matchesStatus =
      filterStatus === 'all' || inv.status.toLowerCase() === filterStatus.toLowerCase();
    const query = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      inv.customer_name.toLowerCase().includes(query) ||
      inv.customer_email.toLowerCase().includes(query) ||
      inv.stripe_invoice_id.toLowerCase().includes(query);
    return matchesStatus && matchesSearch;
  });

  const formatCurrency = (amount: number, currency: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatDate = (isoStr: string) => {
    try {
      return new Date(isoStr).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoStr;
    }
  };

  const formatDateTime = (isoStr: string | null) => {
    if (!isoStr) return 'Never reminded';
    try {
      return new Date(isoStr).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Banner: Active Plan Badge */}
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50/70 via-white to-indigo-50/40 p-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 text-sm">Pro Automation Plan</span>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                14-Day Free Trial Active
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Autonomous 6-hour sweeps active. Graduated 3-tier email cadence running.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowUpgradeModal(true)}
            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-3 py-1.5 rounded-lg border border-indigo-200 bg-white hover:bg-indigo-50 transition-colors"
          >
            Plan Details
          </button>
          <Link
            href="/settings"
            className="inline-flex items-center gap-1 text-xs font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 transition-colors"
          >
            Cadence Settings
          </Link>
        </div>
      </div>

      {/* Header & Main Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Escalation Console
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Monitor at-risk balances, automated tier escalations, and payment recovery.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-3.5 py-2 text-sm font-medium text-slate-700 shadow-sm hover:bg-slate-50 disabled:opacity-50"
            title="Refresh dashboard data"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <button
            onClick={handleRunEscalation}
            disabled={runningEscalation}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-md shadow-indigo-200 hover:bg-indigo-500 disabled:opacity-50 transition-all hover:-translate-y-0.5"
          >
            <Zap className={`h-4 w-4 ${runningEscalation ? 'animate-bounce' : ''}`} />
            {runningEscalation ? 'Running Escalations...' : 'Run Escalation Now'}
          </button>
        </div>
      </div>

      {/* Success/Error Toast Feedback Banner */}
      {toast && (
        <div
          className={`mt-6 flex items-start justify-between rounded-xl p-4 text-sm shadow-sm transition-all ${
            toast.type === 'success'
              ? 'bg-emerald-50 text-emerald-900 border border-emerald-200'
              : 'bg-rose-50 text-rose-900 border border-rose-200'
          }`}
        >
          <div className="flex items-start gap-3">
            {toast.type === 'success' ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="h-5 w-5 text-rose-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <div className="font-bold">{toast.message}</div>
              {toast.submessage && (
                <div className="text-xs opacity-90 mt-0.5">{toast.submessage}</div>
              )}
            </div>
          </div>
          <button
            onClick={() => setToast(null)}
            className="text-slate-400 hover:text-slate-700 p-1 rounded"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Metric Cards Row */}
      <div className="mt-8 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Total At-Risk"
          value={metrics ? formatCurrency(metrics.total_at_risk, metrics.currency) : '$0.00'}
          subtitle="Delinquent open balances"
          icon={AlertTriangle}
          variant="warning"
        />
        <MetricCard
          title="Recovered"
          value={metrics ? formatCurrency(metrics.recovered_revenue, metrics.currency) : '$0.00'}
          subtitle="Settled following escalations"
          icon={TrendingUp}
          variant="success"
        />
        <MetricCard
          title="Active Escalations"
          value={metrics ? metrics.active_escalations : 0}
          subtitle="In Tier 1, Tier 2, or Tier 3"
          icon={Zap}
          variant="default"
        />
        <MetricCard
          title="Resolved Invoices"
          value={metrics ? metrics.resolved_invoices : 0}
          subtitle="Fully collected & closed"
          icon={CheckCircle2}
          variant="default"
        />
      </div>

      {/* Invoices Table Card */}
      <div className="mt-10 rounded-xl border border-slate-200 bg-white shadow-sm overflow-hidden">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 border-b border-slate-200 bg-slate-50/50">
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-slate-900">Tracked Delinquent Invoices</h2>
            <span className="rounded-full bg-slate-200 px-2 py-0.5 text-xs font-semibold text-slate-700">
              {filteredInvoices.length}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3">
            {/* Status Filter */}
            <div className="flex items-center gap-1 rounded-lg bg-slate-200/70 p-1 text-xs font-medium w-full sm:w-auto justify-center">
              {['all', 'open', 'paid'].map((st) => (
                <button
                  key={st}
                  onClick={() => setFilterStatus(st)}
                  className={`rounded-md px-3 py-1 capitalize transition-colors ${
                    filterStatus === st
                      ? 'bg-white text-slate-900 font-semibold shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {st === 'all' ? 'All' : st}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative w-full sm:w-64">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search name, email, ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-slate-300 pl-9 pr-3 py-1.5 text-xs focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>
          </div>
        </div>

        {/* Invoices Data Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
            <thead className="bg-slate-100/70 text-[11px] font-bold uppercase tracking-wider text-slate-600">
              <tr>
                <th scope="col" className="px-6 py-3.5">Customer</th>
                <th scope="col" className="px-6 py-3.5">Email</th>
                <th scope="col" className="px-6 py-3.5">Amount Due</th>
                <th scope="col" className="px-6 py-3.5">Due Date</th>
                <th scope="col" className="px-6 py-3.5">Status</th>
                <th scope="col" className="px-6 py-3.5">Escalation Tier</th>
                <th scope="col" className="px-6 py-3.5">Last Reminded</th>
                <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white">
              {filteredInvoices.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-500 text-sm">
                    No tracked invoices match the filter criteria.
                  </td>
                </tr>
              ) : (
                filteredInvoices.map((inv) => {
                  const amount = inv.amount_due_dollars ?? (inv.amount_due > 100 ? inv.amount_due / 100 : inv.amount_due);
                  return (
                    <tr key={inv.stripe_invoice_id} className="hover:bg-slate-50/80 transition-colors">
                      {/* Customer Name */}
                      <td className="px-6 py-4 font-bold text-slate-900">
                        {inv.customer_name}
                        <div className="text-[10px] font-mono text-slate-400 font-normal">
                          {inv.stripe_invoice_id}
                        </div>
                      </td>

                      {/* Email */}
                      <td className="px-6 py-4 text-slate-600 font-medium">
                        {inv.customer_email}
                      </td>

                      {/* Amount Due */}
                      <td className="px-6 py-4 font-bold text-slate-900">
                        {formatCurrency(amount, inv.currency)}
                      </td>

                      {/* Due Date */}
                      <td className="px-6 py-4 text-slate-600">
                        {formatDate(inv.due_date)}
                      </td>

                      {/* Status Badge */}
                      <td className="px-6 py-4">
                        <StatusBadge status={inv.status} />
                      </td>

                      {/* Escalation Tier Badge */}
                      <td className="px-6 py-4">
                        <EscalationTierBadge tier={inv.current_escalation_tier} />
                      </td>

                      {/* Last Reminded */}
                      <td className="px-6 py-4 text-slate-500">
                        <div className="flex items-center gap-1.5">
                          <Clock className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                          <span>{formatDateTime(inv.last_reminded_at)}</span>
                        </div>
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        <a
                          href={inv.hosted_invoice_url || `https://invoice.stripe.com/${inv.stripe_invoice_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                        >
                          Invoice <ExternalLink className="h-3 w-3" />
                        </a>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upgrade / Plan Modal */}
      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl relative animate-in fade-in zoom-in-95">
            <button
              onClick={() => setShowUpgradeModal(false)}
              className="absolute right-4 top-4 text-slate-400 hover:text-slate-600"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2 mb-3">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-600 text-white font-bold text-sm">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <h3 className="text-base font-bold text-slate-900">Pro Automation Plan</h3>
                <p className="text-xs text-slate-500">$29/month • 14-day free trial</p>
              </div>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              Your subscription grants autonomous 6-hour sweeps, 3-tier graduated notification sequences, Resend email deliverability, and Stripe webhook syncing.
            </p>
            <div className="rounded-lg bg-slate-50 p-3 text-xs border border-slate-200 space-y-1.5 mb-5">
              <div className="flex items-center justify-between text-slate-700">
                <span>Billing Status:</span>
                <span className="font-semibold text-emerald-600">Active Trial</span>
              </div>
              <div className="flex items-center justify-between text-slate-700">
                <span>Next Renewal:</span>
                <span className="font-semibold">In 14 days ($29.00)</span>
              </div>
              <div className="flex items-center justify-between text-slate-700">
                <span>Payment Method:</span>
                <span className="font-semibold">Stripe Customer Portal</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowUpgradeModal(false)}
                className="w-full rounded-lg bg-indigo-600 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-colors"
              >
                Close
              </button>
              <Link
                href="/pricing"
                className="w-full text-center rounded-lg border border-slate-300 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                View Plans
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
