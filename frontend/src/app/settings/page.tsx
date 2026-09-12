'use client';

import { useEffect, useState } from 'react';
import {
  Sliders,
  Key,
  CreditCard,
  Save,
  CheckCircle,
  AlertCircle,
  Mail,
  Copy,
  ExternalLink,
  Shield,
  Layers,
  Sparkles,
} from 'lucide-react';
import {
  getEscalationRules,
  updateEscalationRules,
  getIntegrations,
  saveStripeKey,
} from '@/lib/api';
import { EscalationRule, IntegrationStatus } from '@/lib/types';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<'cadence' | 'stripe' | 'billing'>('cadence');
  const [rules, setRules] = useState<EscalationRule[]>([]);
  const [integrations, setIntegrations] = useState<IntegrationStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [savingRules, setSavingRules] = useState<boolean>(false);
  const [savingKey, setSavingKey] = useState<boolean>(false);
  const [stripeKeyInput, setStripeKeyInput] = useState<string>('');
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [copiedWebhook, setCopiedWebhook] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [r, i] = await Promise.all([getEscalationRules(), getIntegrations()]);
        setRules(r);
        setIntegrations(i);
      } catch (err) {
        console.error('Failed loading settings:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleRuleFieldChange = (index: number, field: keyof EscalationRule, value: any) => {
    const updated = [...rules];
    updated[index] = { ...updated[index], [field]: value };
    setRules(updated);
  };

  const handleSaveCadence = async () => {
    try {
      setSavingRules(true);
      await updateEscalationRules(rules);
      setFeedback({
        type: 'success',
        message: 'Escalation cadence intervals and email templates saved successfully!',
      });
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed saving cadence rules.',
      });
    } finally {
      setSavingRules(false);
    }
  };

  const handleSaveStripeKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!stripeKeyInput.trim()) {
      setFeedback({ type: 'error', message: 'Please enter a valid Stripe Restricted Key.' });
      return;
    }
    try {
      setSavingKey(true);
      const res = await saveStripeKey(stripeKeyInput.trim());
      setFeedback({
        type: 'success',
        message: res.message || 'Stripe Restricted Key stored securely.',
      });
      setStripeKeyInput('');
      const updatedIntegrations = await getIntegrations();
      setIntegrations(updatedIntegrations);
    } catch (err: any) {
      setFeedback({
        type: 'error',
        message: err.message || 'Failed to save Stripe key. Ensure it starts with rk_.',
      });
    } finally {
      setSavingKey(false);
    }
  };

  const copyWebhookUrl = () => {
    navigator.clipboard.writeText('http://localhost:8000/api/v1/webhooks/stripe');
    setCopiedWebhook(true);
    setTimeout(() => setCopiedWebhook(false), 2000);
  };

  const templateVariables = [
    '{{customer_name}}',
    '{{amount_due}}',
    '{{due_date}}',
    '{{payment_link}}',
    '{{company_name}}',
  ];

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="pb-6 border-b border-slate-200">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Settings & Escalation Configuration
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Fine-tune escalation day thresholds, preview and edit email copy, and secure your Stripe connection.
        </p>

        {/* Tab Navigation */}
        <div className="mt-6 flex items-center gap-2 border-b border-slate-200">
          <button
            onClick={() => setActiveTab('cadence')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors -mb-px ${
              activeTab === 'cadence'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Sliders className="h-4 w-4" />
            Cadence & Email Templates
          </button>
          <button
            onClick={() => setActiveTab('stripe')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors -mb-px ${
              activeTab === 'stripe'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <Key className="h-4 w-4" />
            Stripe Restricted Key
          </button>
          <button
            onClick={() => setActiveTab('billing')}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors -mb-px ${
              activeTab === 'billing'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <CreditCard className="h-4 w-4" />
            Plan & Billing
          </button>
        </div>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`mt-6 flex items-center justify-between rounded-xl p-4 text-sm font-medium ${
            feedback.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
              : 'bg-rose-50 text-rose-800 border border-rose-200'
          }`}
        >
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? (
              <CheckCircle className="h-5 w-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="h-5 w-5 text-rose-600 flex-shrink-0" />
            )}
            <span>{feedback.message}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            className="text-xs uppercase font-bold text-slate-400 hover:text-slate-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* TAB 1: CADENCE & EMAIL TEMPLATES */}
      {activeTab === 'cadence' && (
        <div className="mt-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900">3-Tier Escalation Sequence</h2>
              <p className="text-xs text-slate-500">
                Adjust days overdue threshold and tailor the email copy dispatched to clients.
              </p>
            </div>
            <button
              onClick={handleSaveCadence}
              disabled={savingRules}
              className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 transition-colors"
            >
              <Save className="h-3.5 w-3.5" />
              {savingRules ? 'Saving...' : 'Save Rules & Templates'}
            </button>
          </div>

          {/* Dynamic Variable Chips */}
          <div className="rounded-lg bg-slate-100 p-3 text-xs text-slate-600">
            <span className="font-semibold text-slate-800 mr-2">Available Template Variables:</span>
            <div className="inline-flex flex-wrap gap-1.5 mt-1 sm:mt-0">
              {templateVariables.map((v) => (
                <span
                  key={v}
                  className="rounded bg-white px-2 py-0.5 font-mono text-[11px] font-medium text-indigo-700 border border-slate-200"
                >
                  {v}
                </span>
              ))}
            </div>
          </div>

          {/* Rules List */}
          <div className="space-y-6">
            {rules.map((rule, idx) => (
              <div
                key={rule.tier}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-3">
                    <span className="flex h-7 w-7 items-center justify-center rounded-full bg-indigo-100 font-bold text-xs text-indigo-700">
                      T{rule.tier}
                    </span>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm">{rule.name}</h3>
                      <p className="text-xs text-slate-500">{rule.description}</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="text-xs text-slate-500">Trigger at:</span>
                    <input
                      type="number"
                      min="1"
                      value={rule.days_overdue}
                      onChange={(e) =>
                        handleRuleFieldChange(idx, 'days_overdue', parseInt(e.target.value) || 1)
                      }
                      className="w-16 rounded border border-slate-300 bg-white px-2 py-1 text-xs text-center font-bold text-slate-900"
                    />
                    <span className="text-xs text-slate-600 font-medium">days overdue</span>
                  </div>
                </div>

                {/* Email Subject Field */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Email Subject Line
                  </label>
                  <input
                    type="text"
                    value={rule.email_subject}
                    onChange={(e) => handleRuleFieldChange(idx, 'email_subject', e.target.value)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                </div>

                {/* Email Body Template Field */}
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    Email Body Copy Template
                  </label>
                  <textarea
                    rows={3}
                    value={rule.email_body_template}
                    onChange={(e) =>
                      handleRuleFieldChange(idx, 'email_body_template', e.target.value)
                    }
                    className="w-full rounded-lg border border-slate-300 p-3 text-xs text-slate-800 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 font-sans"
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: STRIPE RESTRICTED API KEY */}
      {activeTab === 'stripe' && (
        <div className="mt-8 max-w-2xl space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Key className="h-5 w-5 text-indigo-600" />
                <h2 className="text-base font-bold text-slate-900">Stripe Restricted API Key</h2>
              </div>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${
                  integrations?.stripe.configured
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border border-amber-200'
                }`}
              >
                {integrations?.stripe.configured ? 'Key Configured' : 'Dev / Mock Mode'}
              </span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-4">
              For security, EscalatePay requires only a <strong>Restricted Key (rk_live_...)</strong> with read access to Invoices and write access to Checkout Sessions.
            </p>

            {integrations?.stripe.masked_key && (
              <div className="mb-4 rounded-lg bg-emerald-50 p-3 border border-emerald-200 text-xs text-emerald-800 flex items-center justify-between">
                <span>Active Key: <strong>{integrations.stripe.masked_key}</strong></span>
                <span className="text-[11px] font-semibold text-emerald-700">Encrypted</span>
              </div>
            )}

            <form onSubmit={handleSaveStripeKey} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Enter Stripe Restricted Key
                </label>
                <input
                  type="password"
                  placeholder="rk_live_..."
                  value={stripeKeyInput}
                  onChange={(e) => setStripeKeyInput(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-mono focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>

              <button
                type="submit"
                disabled={savingKey}
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 disabled:opacity-50 transition-colors"
              >
                <Save className="h-3.5 w-3.5" />
                {savingKey ? 'Verifying & Saving...' : 'Save Restricted Key'}
              </button>
            </form>

            <div className="mt-6 pt-5 border-t border-slate-100">
              <div className="text-xs font-semibold text-slate-700 mb-1.5">
                Stripe Webhook Endpoint:
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-50 p-2 border border-slate-200 text-xs font-mono">
                <span className="truncate">http://localhost:8000/api/v1/webhooks/stripe</span>
                <button
                  type="button"
                  onClick={copyWebhookUrl}
                  className="text-indigo-600 hover:text-indigo-800 font-sans font-semibold text-[11px] flex items-center gap-1 ml-2"
                >
                  <Copy className="h-3 w-3" />
                  {copiedWebhook ? 'Copied' : 'Copy'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: PLAN & BILLING */}
      {activeTab === 'billing' && (
        <div className="mt-8 max-w-2xl space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-indigo-600" />
                <h2 className="text-base font-bold text-slate-900">Current Subscription</h2>
              </div>
              <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-800">
                14-Day Free Trial
              </span>
            </div>

            <div className="rounded-lg bg-slate-50 p-4 border border-slate-200 space-y-2 text-xs text-slate-600 mb-6">
              <div className="flex justify-between">
                <span>Plan:</span>
                <span className="font-bold text-slate-900">Pro Automation Plan</span>
              </div>
              <div className="flex justify-between">
                <span>Billing Interval:</span>
                <span className="font-bold text-slate-900">$29.00 / month</span>
              </div>
              <div className="flex justify-between">
                <span>Trial Ends:</span>
                <span className="font-bold text-emerald-700">In 14 days</span>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="/pricing"
                className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-colors"
              >
                Change Plan
              </a>
              <button
                type="button"
                onClick={() => setFeedback({ type: 'success', message: 'Billing customer portal opened in test mode.' })}
                className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50 transition-colors"
              >
                Manage Payment Method
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
