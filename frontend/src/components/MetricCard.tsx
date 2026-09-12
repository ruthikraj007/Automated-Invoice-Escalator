import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  variant?: 'default' | 'warning' | 'danger' | 'success';
}

export function MetricCard({ title, value, subtitle, icon: Icon, variant = 'default' }: MetricCardProps) {
  const colorMap = {
    default: {
      bg: 'bg-indigo-50',
      text: 'text-indigo-600',
      border: 'border-slate-200',
    },
    warning: {
      bg: 'bg-amber-50',
      text: 'text-amber-600',
      border: 'border-amber-100',
    },
    danger: {
      bg: 'bg-rose-50',
      text: 'text-rose-600',
      border: 'border-rose-100',
    },
    success: {
      bg: 'bg-emerald-50',
      text: 'text-emerald-600',
      border: 'border-emerald-100',
    },
  };

  const style = colorMap[variant];

  return (
    <div className={`rounded-xl border ${style.border} bg-white p-5 shadow-sm transition-all hover:shadow-md`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-500">{title}</span>
        <div className={`rounded-lg p-2 ${style.bg}`}>
          <Icon className={`h-5 w-5 ${style.text}`} />
        </div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-bold tracking-tight text-slate-900">{value}</div>
        {subtitle && <div className="mt-1 text-xs text-slate-500">{subtitle}</div>}
      </div>
    </div>
  );
}
