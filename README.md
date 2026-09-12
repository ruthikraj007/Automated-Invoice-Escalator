# Automated Invoice & Payment Escalator (EscalatePay)

A full-stack Micro-SaaS application designed to automate collection sequences for overdue invoices, execute multi-stage escalation policies, and synchronize with Stripe and Resend.

---

## Architecture Overview

```
MIcroSaaS/
├── backend/                       # Python 3.11+ FastAPI Server
│   ├── app/
│   │   ├── api/v1/endpoints/      # API Routes (invoices, settings, webhooks)
│   │   │   ├── invoices.py        # Metrics, invoice queries, manual escalation triggers
│   │   │   ├── settings.py        # Escalation rules & third-party service status
│   │   │   └── webhooks.py        # Stripe & Resend webhook listeners
│   │   ├── core/
│   │   │   ├── config.py          # Pydantic Settings & environment variable loader
│   │   │   └── database.py        # Supabase client with dev mock fallback
│   │   ├── services/
│   │   │   ├── stripe_service.py  # Stripe invoice sync & checkout sessions
│   │   │   ├── escalation_service.py # Escalation policy engine & APScheduler sweeps
│   │   │   └── email_service.py   # Resend multi-tier HTML email dispatch
│   │   └── main.py                # FastAPI entrypoint, CORS, lifespan & health check
│   ├── .env.example               # Environment variable template
│   ├── pyproject.toml             # Python package configuration
│   └── requirements.txt           # Pip dependencies
│
├── frontend/                      # Next.js 14+ (App Router)
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx           # High-conversion Landing Page
│   │   │   ├── dashboard/page.tsx # Metrics, filterable invoice table, manual escalation actions
│   │   │   └── settings/page.tsx  # Cadence threshold configuration & integrations status
│   │   ├── components/            # Navbar, MetricCard, StatusBadge
│   │   └── lib/                   # API client & TypeScript interfaces
│   ├── package.json
│   ├── tailwind.config.ts
│   └── tsconfig.json
```

---

## Escalation Workflow

The engine evaluates overdue days against graduated stages:
1. **Stage 1 (Day 3 Overdue)**: Gentle courtesy reminder with frictionless Stripe payment URL.
2. **Stage 2 (Day 7 Overdue)**: Formal notice requesting accounting follow-up.
3. **Stage 3 (Day 14 Overdue)**: Firm collection demand with impending late fee warnings.
4. **Stage 4 (Day 30 Overdue)**: Final demand notice with 48-hour service suspension warning.

---

## Quickstart

### 1. Backend (FastAPI)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```
- **Health Check**: `http://localhost:8000/health`
- **Swagger Docs**: `http://localhost:8000/docs`

### 2. Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
- **Landing Page**: `http://localhost:3000/`
- **Dashboard**: `http://localhost:3000/dashboard`
- **Settings**: `http://localhost:3000/settings`
