import { MetricSummary, TrackedInvoice, EscalationRule, IntegrationStatus } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export async function checkBackendHealth(): Promise<{ healthy: boolean; data?: any }> {
  try {
    const res = await fetch(`${API_BASE_URL}/health`, { cache: 'no-store' });
    if (!res.ok) return { healthy: false };
    const data = await res.json();
    return { healthy: true, data };
  } catch {
    return { healthy: false };
  }
}

export async function getMetricsSummary(): Promise<MetricSummary> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/invoices/metrics/summary`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('API unavailable, returning fallback metrics');
  }
  return {
    total_at_risk: 31250,
    total_outstanding: 31250,
    recovered_revenue: 14600,
    active_escalations: 3,
    escalated_count: 3,
    resolved_invoices: 8,
    overdue_count: 3,
    currency: 'USD',
  };
}

export async function getTrackedInvoices(): Promise<TrackedInvoice[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/invoices/tracked`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data) && data.length > 0) return data;
    }
  } catch (e) {
    console.warn('API unavailable, returning fallback tracked invoices');
  }

  return [
    {
      id: 'inv_mock_001',
      stripe_invoice_id: 'in_mock_001',
      customer_name: 'Jordan Reed (Apex Labs)',
      customer_email: 'jordan@apexlabs.com',
      amount_due: 320000,
      amount_due_dollars: 3200.0,
      currency: 'usd',
      due_date: new Date(Date.now() - 8 * 86400 * 1000).toISOString(),
      status: 'open',
      current_escalation_tier: 2,
      last_reminded_at: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
      hosted_invoice_url: 'https://invoice.stripe.com/in_mock_001',
    },
    {
      id: 'inv_mock_002',
      stripe_invoice_id: 'in_mock_002',
      customer_name: 'Mark Sloan (Enterprise Corp)',
      customer_email: 'mark@enterprise.org',
      amount_due: 980000,
      amount_due_dollars: 9800.0,
      currency: 'usd',
      due_date: new Date(Date.now() - 15 * 86400 * 1000).toISOString(),
      status: 'open',
      current_escalation_tier: 3,
      last_reminded_at: new Date(Date.now() - 6 * 3600 * 1000).toISOString(),
      hosted_invoice_url: 'https://invoice.stripe.com/in_mock_002',
    },
    {
      id: 'inv_mock_003',
      stripe_invoice_id: 'in_mock_003',
      customer_name: 'Sara Chen (Velocity Studio)',
      customer_email: 'sara@startup.co',
      amount_due: 125000,
      amount_due_dollars: 1250.0,
      currency: 'usd',
      due_date: new Date(Date.now() - 4 * 86400 * 1000).toISOString(),
      status: 'open',
      current_escalation_tier: 1,
      last_reminded_at: new Date(Date.now() - 24 * 3600 * 1000).toISOString(),
      hosted_invoice_url: 'https://invoice.stripe.com/in_mock_003',
    },
    {
      id: 'inv_mock_004',
      stripe_invoice_id: 'in_mock_004',
      customer_name: 'David Kim (Nexus Systems)',
      customer_email: 'david@nexus.io',
      amount_due: 540000,
      amount_due_dollars: 5400.0,
      currency: 'usd',
      due_date: new Date(Date.now() - 12 * 86400 * 1000).toISOString(),
      status: 'paid',
      current_escalation_tier: 2,
      last_reminded_at: new Date(Date.now() - 48 * 3600 * 1000).toISOString(),
      hosted_invoice_url: 'https://invoice.stripe.com/in_mock_004',
    },
  ];
}

export async function triggerEscalationRun(): Promise<{
  status: string;
  total_overdue_scanned: number;
  escalations_executed: number;
  invoices_skipped: number;
  escalations: any[];
}> {
  const res = await fetch(`${API_BASE_URL}/api/v1/invoices/run-escalation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Failed to execute escalation: ${errText}`);
  }
  return await res.json();
}

export async function getEscalationRules(): Promise<EscalationRule[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/settings/escalation-rules`, { cache: 'no-store' });
    if (res.ok) {
      const data = await res.json();
      return data.rules;
    }
  } catch (e) {
    console.warn('API unavailable, returning default rules');
  }

  return [
    {
      tier: 1,
      name: 'Courtesy Reminder',
      days_overdue: 3,
      email_subject: 'Payment Reminder: Invoice from {{company_name}} is due',
      email_body_template: 'Hi {{customer_name}}, this is a courtesy reminder that your invoice of {{amount_due}} was due on {{due_date}}.',
      is_active: true,
      description: 'Polite reminder with invoice summary and direct payment link.',
    },
    {
      tier: 2,
      name: 'Firm Notice',
      days_overdue: 7,
      email_subject: 'Second Notice: Overdue Balance with {{company_name}} - Action Required',
      email_body_template: 'Dear {{customer_name}}, your invoice of {{amount_due}} is now over a week past due (due {{due_date}}). To maintain service continuity and avoid late charges, please settle this balance.',
      is_active: true,
      description: 'Firm notice emphasizing urgency, service continuity, and late charges.',
    },
    {
      tier: 3,
      name: 'Final Demand',
      days_overdue: 14,
      email_subject: 'FINAL DEMAND: Imminent Service Suspension on Invoice from {{company_name}}',
      email_body_template: 'Attention {{customer_name}}, final demand: Your invoice of {{amount_due}} (due {{due_date}}) is 14+ days delinquent. Service access will be paused within 48 hours unless payment is received.',
      is_active: true,
      description: 'Final demand notice prior to service suspension or escalation.',
    },
  ];
}

export async function updateEscalationRules(rules: EscalationRule[]): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/escalation-rules`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rules }),
  });
  if (!res.ok) throw new Error('Failed to update escalation rules');
  return res.json();
}

export async function saveStripeKey(restrictedKey: string): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/settings/stripe-key`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ restricted_key: restrictedKey }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to save Stripe key');
  }
  return res.json();
}

export async function getIntegrations(): Promise<IntegrationStatus> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/settings/integrations`, { cache: 'no-store' });
    if (res.ok) return await res.json();
  } catch (e) {
    console.warn('API unavailable, returning default integration statuses');
  }
  return {
    stripe: { configured: false, webhook_configured: false, status: 'mock_mode' },
    resend: { configured: false, sender_email: 'billing@example.com', status: 'mock_mode' },
    supabase: { configured: false, status: 'mock_mode' },
    scheduler: { enabled: true, interval_hours: 6, status: 'active' },
  };
}
