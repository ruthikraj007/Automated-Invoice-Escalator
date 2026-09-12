-- ==============================================================================
-- Migration: 001_initial_schema.sql
-- Description: Core schema for Automated Invoice & Payment Escalator with RLS
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Profiles Table (extends auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    stripe_account_id TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Escalation Rules Table
CREATE TABLE IF NOT EXISTS public.escalation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tier INT NOT NULL CHECK (tier BETWEEN 1 AND 3),
    days_overdue INT NOT NULL CHECK (days_overdue >= 0),
    email_subject TEXT NOT NULL,
    email_body_template TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Tracked Invoices Table
CREATE TABLE IF NOT EXISTS public.tracked_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL REFERENCES public.profiles(id) ON DELETE SET NULL,
    stripe_invoice_id TEXT UNIQUE NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    amount_due INT NOT NULL, -- Stored in smallest currency unit (e.g. cents)
    currency TEXT NOT NULL DEFAULT 'usd',
    due_date TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'open', -- 'open', 'paid', 'uncollectible', 'void'
    current_escalation_tier INT NOT NULL DEFAULT 0,
    last_reminded_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes on tracked_invoices for fast querying
CREATE INDEX IF NOT EXISTS idx_tracked_invoices_user_id ON public.tracked_invoices(user_id);
CREATE INDEX IF NOT EXISTS idx_tracked_invoices_stripe_id ON public.tracked_invoices(stripe_invoice_id);
CREATE INDEX IF NOT EXISTS idx_tracked_invoices_status ON public.tracked_invoices(status);

-- 4. Audit Logs Table
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NULL REFERENCES public.tracked_invoices(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_invoice_id ON public.audit_logs(invoice_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type ON public.audit_logs(event_type);

-- ==============================================================================
-- Row Level Security (RLS) Policies
-- ==============================================================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.escalation_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tracked_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

-- Escalation Rules policies
CREATE POLICY "Users can view own escalation rules"
    ON public.escalation_rules FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own escalation rules"
    ON public.escalation_rules FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own escalation rules"
    ON public.escalation_rules FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own escalation rules"
    ON public.escalation_rules FOR DELETE
    USING (auth.uid() = user_id);

-- Tracked Invoices policies
CREATE POLICY "Users can view own tracked invoices"
    ON public.tracked_invoices FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update own tracked invoices"
    ON public.tracked_invoices FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own tracked invoices"
    ON public.tracked_invoices FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Service role bypass / Server-side webhook handling for tracked_invoices & audit_logs
CREATE POLICY "Service role full access on tracked_invoices"
    ON public.tracked_invoices FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Audit logs policies: Users can view audit logs for invoices they own
CREATE POLICY "Users can view audit logs for own invoices"
    ON public.audit_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.tracked_invoices ti
            WHERE ti.id = public.audit_logs.invoice_id
            AND ti.user_id = auth.uid()
        )
    );

CREATE POLICY "Service role full access on audit_logs"
    ON public.audit_logs FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
