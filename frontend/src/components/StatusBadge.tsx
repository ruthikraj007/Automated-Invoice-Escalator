import React from 'react';

export function StatusBadge({ status }: { status: string }) {
  switch (status?.toLowerCase()) {
    case 'paid':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
          Paid
        </span>
      );
    case 'open':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          Open
        </span>
      );
    case 'void':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200">
          Void
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
          {status}
        </span>
      );
  }
}

export function EscalationTierBadge({ tier }: { tier: number }) {
  switch (tier) {
    case 0:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
          None
        </span>
      );
    case 1:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
          Tier 1 (Reminder)
        </span>
      );
    case 2:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
          Tier 2 (Firm Notice)
        </span>
      );
    case 3:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200 animate-pulse">
          Tier 3 (Final Demand)
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700">
          Tier {tier}
        </span>
      );
  }
}

// Alias for compatibility
export const EscalationStageBadge = ({ stage }: { stage: number }) => <EscalationTierBadge tier={stage} />;
