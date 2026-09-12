export interface MetricSummary {
  total_at_risk: number;
  total_outstanding?: number;
  recovered_revenue: number;
  active_escalations: number;
  escalated_count?: number;
  resolved_invoices: number;
  overdue_count?: number;
  currency: string;
}

export interface TrackedInvoice {
  id?: string;
  stripe_invoice_id: string;
  customer_name: string;
  customer_email: string;
  amount_due: number;
  amount_due_dollars?: number;
  currency: string;
  due_date: string;
  status: 'open' | 'paid' | 'uncollectible' | 'void';
  current_escalation_tier: number;
  last_reminded_at: string | null;
  hosted_invoice_url?: string;
}

export interface EscalationRule {
  tier: number;
  stage?: number;
  name: string;
  days_overdue: number;
  days_overdue_threshold?: number;
  email_subject: string;
  email_body_template: string;
  is_active: boolean;
  action?: string;
  description?: string;
}

export interface IntegrationStatus {
  stripe: {
    configured: boolean;
    webhook_configured: boolean;
    status: string;
    masked_key?: string | null;
  };
  resend: {
    configured: boolean;
    sender_email: string;
    status: string;
  };
  supabase: {
    configured: boolean;
    status: string;
  };
  scheduler: {
    enabled: boolean;
    interval_hours: number;
    status: string;
  };
}
