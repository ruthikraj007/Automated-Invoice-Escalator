# Production Deployment Checklist & Configuration Guide

This guide details all configuration variables, database provisioning steps, third-party credentials, and deployment procedures required to take the **Automated Invoice & Payment Escalator** (EscalatePay) live into production.

---

## 1. Cloud Architecture Overview

| Component | Recommended Host | Production Runtime | Port / Target |
| :--- | :--- | :--- | :--- |
| **Backend API** | Railway / Render | Docker (`python:3.11-slim`) with Uvicorn (2 workers) | Port `8000` (`/health`) |
| **Frontend UI** | Vercel | Next.js 14+ (App Router, Standalone) | Port `3000` / Edge CDN |
| **Database** | Supabase | PostgreSQL 15+ with Row Level Security (RLS) | Port `5432` / REST |
| **Email Dispatch**| Resend | High-deliverability transactional SMTP/HTTP API | REST API |
| **Payment Ingestion**| Stripe | Webhooks (`invoice.finalized`, `payment_failed`, `paid`) | HTTPS Webhook URL |

---

## 2. Environment Variables Matrix

### Backend (`backend/.env` / Cloud Secrets)

| Variable Name | Required | Example / Format | Description |
| :--- | :---: | :--- | :--- |
| `APP_NAME` | No | `"Automated Invoice & Payment Escalator"` | Application brand display name. |
| `DEBUG` | Yes | `false` | Disable interactive debug tools in production. |
| `PORT` | Yes | `8000` | Port for Uvicorn binding (auto-injected by Railway/Render). |
| `HOST` | Yes | `0.0.0.0` | Bind address. |
| `CORS_ORIGINS` | Yes | `["https://your-app.vercel.app"]` | JSON array or comma-separated list of allowed frontend domains. |
| `SUPABASE_URL` | Yes | `https://xyzproject.supabase.co` | Supabase Project REST URL (Dashboard &rarr; Settings &rarr; API). |
| `SUPABASE_KEY` | Yes | `eyJhbGciOi...` | Supabase Service Role Key (for secure server-side webhook updates). |
| `STRIPE_SECRET_KEY` | Yes | `rk_live_...` or `sk_live_...` | Stripe Live Secret or Restricted Key with invoices & checkout access. |
| `STRIPE_WEBHOOK_SECRET` | Yes | `whsec_...` | Live Webhook signing secret generated in the Stripe Dashboard. |
| `RESEND_API_KEY` | Yes | `re_live_...` | Resend Live API Key for transactional email delivery. |
| `DEFAULT_SENDER_EMAIL` | Yes | `billing@yourverifieddomain.com` | Authenticated sender address configured in Resend. |
| `ESCALATION_CHECK_HOURS`| Yes | `6` | Frequency of automated overdue invoice sweeps (in hours). |
| `ENABLE_SCHEDULER` | Yes | `true` | Enables APScheduler background job upon app startup. |

### Frontend (`frontend/.env.production` / Vercel Environment Variables)

| Variable Name | Required | Example / Format | Description |
| :--- | :---: | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | Yes | `https://api.yourdomain.com` | Base URL of the hosted FastAPI backend. |
| `STRIPE_SECRET_KEY` | Yes | `sk_live_...` | Used by `/api/checkout` to create recurring Stripe Checkout Sessions. |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Optional | `pk_live_...` | Client-side Stripe Elements / Checkout integration. |

---

## 3. Database Migration (Supabase)

1. Open your **Supabase Project Dashboard** &rarr; navigate to the **SQL Editor**.
2. Open [`backend/migrations/001_initial_schema.sql`](file:///Users/ruthikraj007/Downloads/Coding/MIcroSaaS/backend/migrations/001_initial_schema.sql).
3. Paste the contents into the SQL Editor and click **Run**.
4. Verify that the following 4 tables are created with **Row Level Security (RLS)** active:
   - `profiles`
   - `escalation_rules`
   - `tracked_invoices`
   - `audit_logs`

---

## 4. Resend Production Email Setup

1. Sign in to [Resend.com](https://resend.com) &rarr; **Domains** &rarr; **Add Domain** (e.g., `yourdomain.com`).
2. Add the required **DNS Records** (MX, TXT SPF, TXT DKIM, and CNAME) in your DNS provider (Cloudflare, Route53, Namecheap).
3. Wait for Resend status to change to **Verified**.
4. Go to **API Keys** &rarr; create a production key with `Sending access` permission.
5. Set `RESEND_API_KEY=re_...` and `DEFAULT_SENDER_EMAIL=billing@yourdomain.com`.

---

## 5. Live Stripe Webhook Configuration

Follow these exact steps to ensure Stripe notifies your backend when invoices are created, fail, or are settled:

1. Log into the **Stripe Dashboard** &rarr; toggle to **Live mode** (top right).
2. Navigate to **Developers** &rarr; **Webhooks** &rarr; click **Add destination / Add endpoint**.
3. In **Endpoint URL**, enter:
   ```
   https://<YOUR-BACKEND-DOMAIN>/api/v1/webhooks/stripe
   ```
4. In **Listen to**, select **Events on your account**.
5. In **Select events to send**, check the following 3 events:
   - `invoice.finalized` (triggers initial tracking with status `open`)
   - `invoice.payment_failed` (triggers overdue tracking and escalation eligibility)
   - `invoice.paid` (instantly updates status to `paid`, halting escalations)
6. Click **Add endpoint**.
7. Click **Reveal** under **Signing secret** (starts with `whsec_...`).
8. Copy this secret and set it as `STRIPE_WEBHOOK_SECRET` in your backend environment variables.

---

## 6. Cloud Deployment Guide

### Option A: Deploy Backend to Railway
1. Fork or push this repository to GitHub.
2. Log into [Railway.app](https://railway.app) &rarr; **New Project** &rarr; **Deploy from GitHub repo**.
3. Select your repository &rarr; choose the `/backend` folder as the root directory.
4. Railway automatically detects [`backend/railway.toml`](file:///Users/ruthikraj007/Downloads/Coding/MIcroSaaS/backend/railway.toml) and [`backend/Dockerfile`](file:///Users/ruthikraj007/Downloads/Coding/MIcroSaaS/backend/Dockerfile).
5. In the Railway service settings &rarr; **Variables**, paste all backend environment variables from Section 2.
6. Under **Networking**, click **Generate Domain** to get your live API URL (e.g. `https://invoice-escalator-production.up.railway.app`).

### Option B: Deploy Backend to Render
1. Log into [Render.com](https://render.com) &rarr; **New** &rarr; **Blueprint**.
2. Select your repository. Render will detect [`render.yaml`](file:///Users/ruthikraj007/Downloads/Coding/MIcroSaaS/render.yaml).
3. Fill in the non-synced secrets (Supabase, Stripe, Resend) and click **Apply**.

### Option C: Deploy Frontend to Vercel
1. Log into [Vercel.com](https://vercel.com) &rarr; **Add New...** &rarr; **Project**.
2. Import your GitHub repository &rarr; set **Root Directory** to `frontend`.
3. In **Environment Variables**, add:
   - `NEXT_PUBLIC_API_URL`: Your live backend URL from Railway/Render (e.g. `https://api.yourdomain.com`).
   - `STRIPE_SECRET_KEY`: `sk_live_...`
   - `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY`: `pk_live_...`
4. Click **Deploy**.

---

## 7. Docker Local Build & Health Verification Commands

Run the following commands in your shell to build and verify the containerized backend:

```bash
# 1. Build the production Docker image
docker build -t invoice-escalator-backend:latest ./backend

# 2. Run the container locally in detached mode on port 8000
docker run -d --name escalator-backend-prod -p 8000:8000 \
  -e APP_NAME="Automated Invoice & Payment Escalator" \
  -e DEBUG="false" \
  -e STRIPE_WEBHOOK_SECRET="whsec_test_secret_12345" \
  invoice-escalator-backend:latest

# 3. Wait 3 seconds and verify health readiness
sleep 3
curl -f -s http://localhost:8000/health | jq .

# 4. Cleanup test container
docker stop escalator-backend-prod && docker rm escalator-backend-prod
```

### Expected Output
```json
{
  "status": "healthy",
  "timestamp": "2026-09-12T06:50:00.000000+00:00",
  "app": "Automated Invoice & Payment Escalator",
  "version": "1.0.0",
  "scheduler_running": true
}
```
