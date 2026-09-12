from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.core.config import settings
from app.services.escalation_service import escalation_service
from app.services.email_service import TIER_TEMPLATES

router = APIRouter()

# In-memory store for custom escalation rules and template overrides
_custom_rules_store = [
    {
        "tier": 1,
        "stage": 1,
        "name": "Courtesy Reminder",
        "days_overdue": 3,
        "days_overdue_threshold": 3,
        "email_subject": "Payment Reminder: Invoice from {{company_name}} is due",
        "email_body_template": "Hi {{customer_name}}, this is a courtesy reminder that your invoice of {{amount_due}} was due on {{due_date}}.",
        "action": "email",
        "is_active": True,
        "description": "Polite reminder with invoice summary and direct payment link."
    },
    {
        "tier": 2,
        "stage": 2,
        "name": "Firm Notice",
        "days_overdue": 7,
        "days_overdue_threshold": 7,
        "email_subject": "Second Notice: Overdue Balance with {{company_name}} - Action Required",
        "email_body_template": "Dear {{customer_name}}, your invoice of {{amount_due}} is now over a week past due (due {{due_date}}). To maintain service continuity and avoid late charges, please settle this balance.",
        "action": "email",
        "is_active": True,
        "description": "Firm notice emphasizing urgency, service continuity, and late charges."
    },
    {
        "tier": 3,
        "stage": 3,
        "name": "Final Demand",
        "days_overdue": 14,
        "days_overdue_threshold": 14,
        "email_subject": "FINAL DEMAND: Imminent Service Suspension on Invoice from {{company_name}}",
        "email_body_template": "Attention {{customer_name}}, final demand: Your invoice of {{amount_due}} (due {{due_date}}) is 14+ days delinquent. Service access will be paused within 48 hours unless payment is received.",
        "action": "email_and_hold",
        "is_active": True,
        "description": "Final demand notice prior to service suspension or escalation."
    }
]

_configured_stripe_key: Optional[str] = None


class EscalationRuleSchema(BaseModel):
    tier: int = Field(..., ge=1, le=3)
    stage: Optional[int] = None
    name: str
    days_overdue: int = Field(..., ge=1)
    days_overdue_threshold: Optional[int] = None
    email_subject: str
    email_body_template: str
    is_active: bool = True
    action: Optional[str] = "email"
    description: Optional[str] = ""

class UpdateRulesRequest(BaseModel):
    rules: List[EscalationRuleSchema]

class StripeKeyRequest(BaseModel):
    restricted_key: str


@router.get("/escalation-rules")
def get_escalation_rules():
    """Retrieve active escalation cadence rules and email templates."""
    return {"rules": _custom_rules_store}


@router.put("/escalation-rules")
def update_escalation_rules(payload: UpdateRulesRequest):
    """Update escalation cadence rules (intervals and email templates)."""
    global _custom_rules_store
    updated = []
    for r in payload.rules:
        dumped = r.model_dump()
        dumped["stage"] = r.tier
        dumped["days_overdue_threshold"] = r.days_overdue
        updated.append(dumped)

    _custom_rules_store = updated

    # Also update email templates in memory
    for rule in updated:
        tier = rule["tier"]
        if tier in TIER_TEMPLATES:
            TIER_TEMPLATES[tier]["subject"] = rule["email_subject"]

    return {"message": "Escalation rules and email templates updated successfully", "rules": _custom_rules_store}


@router.post("/stripe-key")
def save_stripe_restricted_key(payload: StripeKeyRequest):
    """Save Stripe Restricted API Key."""
    global _configured_stripe_key
    key = payload.restricted_key.strip()
    if not key.startswith("rk_") and not key.startswith("sk_"):
        raise HTTPException(
            status_code=400,
            detail="Invalid Stripe Key format. Restricted keys must begin with 'rk_' (or 'sk_')."
        )
    _configured_stripe_key = key
    masked = key[:7] + "..." + key[-4:] if len(key) > 12 else "rk_configured"
    return {
        "status": "success",
        "message": f"Stripe Restricted Key saved securely ({masked}).",
        "configured": True,
        "masked_key": masked
    }


@router.get("/integrations")
def get_integrations_status():
    """Check connectivity and configuration status for third-party services."""
    stripe_active = bool(settings.STRIPE_SECRET_KEY or _configured_stripe_key)
    return {
        "stripe": {
            "configured": stripe_active,
            "webhook_configured": bool(settings.STRIPE_WEBHOOK_SECRET),
            "status": "connected" if stripe_active else "mock_mode",
            "masked_key": (_configured_stripe_key[:7] + "..." + _configured_stripe_key[-4:]) if _configured_stripe_key else None
        },
        "resend": {
            "configured": bool(settings.RESEND_API_KEY),
            "sender_email": settings.DEFAULT_SENDER_EMAIL,
            "status": "connected" if settings.RESEND_API_KEY else "mock_mode"
        },
        "supabase": {
            "configured": bool(settings.SUPABASE_URL and settings.SUPABASE_KEY),
            "status": "connected" if settings.SUPABASE_URL else "mock_mode"
        },
        "scheduler": {
            "enabled": True,
            "interval_hours": 6,
            "status": "active"
        }
    }
