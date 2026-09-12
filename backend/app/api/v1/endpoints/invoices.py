from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.services.stripe_service import stripe_service
from app.services.escalation_service import escalation_service
from app.core.database import get_all_tracked_invoices, get_tracked_invoice

router = APIRouter()

class InvoiceSummary(BaseModel):
    total_at_risk: float
    total_outstanding: float
    recovered_revenue: float
    active_escalations: int
    escalated_count: int
    resolved_invoices: int
    overdue_count: int
    currency: str = "USD"

class EscalateRequest(BaseModel):
    target_stage: Optional[int] = None

@router.get("/metrics/summary", response_model=InvoiceSummary)
def get_metrics_summary():
    """Return executive KPI metrics for the dashboard."""
    # Combine Stripe/mock invoices and database-tracked invoices
    invoices_map = {}
    for inv in stripe_service.get_invoices(limit=50):
        invoices_map[inv["id"]] = inv

    for tracked in get_all_tracked_invoices():
        s_id = tracked.get("stripe_invoice_id")
        amount = tracked.get("amount_due", 0)
        amount_dollars = amount / 100.0 if amount > 100 and tracked.get("currency") == "usd" else float(amount)
        invoices_map[s_id] = {
            "id": s_id,
            "amount_due": amount_dollars,
            "status": tracked.get("status", "open"),
            "days_overdue": 8,
            "escalation_stage": tracked.get("current_escalation_tier", 0),
        }

    all_invoices = list(invoices_map.values())

    total_at_risk = sum(
        inv["amount_due"] for inv in all_invoices if inv.get("status") == "open"
    )
    overdue_count = sum(
        1 for inv in all_invoices if inv.get("status") == "open" and inv.get("days_overdue", 0) > 0
    )
    active_escalations = sum(
        1 for inv in all_invoices if inv.get("status") == "open" and inv.get("escalation_stage", 0) > 0
    )
    recovered_revenue = sum(
        inv["amount_due"] for inv in all_invoices if inv.get("status") == "paid"
    )
    resolved_invoices = sum(
        1 for inv in all_invoices if inv.get("status") == "paid"
    )

    return InvoiceSummary(
        total_at_risk=total_at_risk,
        total_outstanding=total_at_risk,
        recovered_revenue=recovered_revenue,
        active_escalations=active_escalations,
        escalated_count=active_escalations,
        resolved_invoices=resolved_invoices,
        overdue_count=overdue_count,
        currency="USD"
    )

@router.get("/tracked", response_model=List[Dict[str, Any]])
def list_tracked():
    """List invoices saved in database tracked_invoices with normalized dollar amounts."""
    tracked_records = get_all_tracked_invoices()
    formatted = []
    for inv in tracked_records:
        raw_amt = inv.get("amount_due", 0)
        amt_dollars = raw_amt / 100.0 if raw_amt > 100 and inv.get("currency") == "usd" else float(raw_amt)
        item = dict(inv)
        item["amount_due_dollars"] = amt_dollars
        formatted.append(item)
    return formatted

@router.get("/", response_model=List[Dict[str, Any]])
def list_invoices(
    status: Optional[str] = Query(None, description="Filter by status (open, paid, void)"),
    search: Optional[str] = Query(None, description="Search by customer name or email")
):
    """List all synchronized invoices with optional filters."""
    invoices_map = {}
    
    # 1. Base from Stripe sync / mock
    for inv in stripe_service.get_invoices(limit=50):
        invoices_map[inv["id"]] = inv
        
    # 2. Overlay / include database tracked_invoices
    for tracked in get_all_tracked_invoices():
        s_id = tracked.get("stripe_invoice_id")
        # Amount in tracked is stored in cents, convert to dollars for display consistency
        amount = tracked.get("amount_due", 0)
        if amount > 100 and tracked.get("currency") == "usd":
            amount_dollars = amount / 100.0
        else:
            amount_dollars = float(amount)

        invoices_map[s_id] = {
            "id": s_id,
            "customer_name": tracked.get("customer_name"),
            "customer_email": tracked.get("customer_email"),
            "amount_due": amount_dollars,
            "currency": tracked.get("currency", "usd"),
            "status": tracked.get("status", "open"),
            "due_date": tracked.get("due_date"),
            "days_overdue": 5, # default for tracked simulation
            "escalation_stage": tracked.get("current_escalation_tier", 0),
            "hosted_invoice_url": f"https://invoice.stripe.com/{s_id}"
        }

    invoices = list(invoices_map.values())

    if status and status != "all":
        invoices = [inv for inv in invoices if inv.get("status") == status]

    if search:
        search_lower = search.lower()
        invoices = [
            inv for inv in invoices
            if search_lower in inv.get("customer_name", "").lower()
            or search_lower in inv.get("customer_email", "").lower()
            or search_lower in inv.get("id", "").lower()
        ]

    return invoices

@router.get("/{invoice_id}")
def get_invoice(invoice_id: str):
    """Retrieve details for a single invoice."""
    invoices = stripe_service.get_invoices(limit=50)
    for inv in invoices:
        if inv.get("id") == invoice_id:
            return inv
    raise HTTPException(status_code=404, detail="Invoice not found")

@router.post("/{invoice_id}/escalate")
def escalate_invoice(invoice_id: str, payload: Optional[EscalateRequest] = None):
    """Manually advance the escalation stage for an invoice."""
    invoices = stripe_service.get_invoices(limit=50)
    target_invoice = None
    for inv in invoices:
        if inv.get("id") == invoice_id:
            target_invoice = inv
            break

    if not target_invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    target_stage = payload.target_stage if payload else None
    result = escalation_service.execute_escalation(target_invoice, target_stage=target_stage)
    return result

@router.post("/sweep/trigger")
async def trigger_manual_sweep():
    """Manually trigger an automated escalation sweep."""
    result = await escalation_service.run_escalation_sweep()
    return result

@router.post("/run-escalation")
async def run_escalation_now():
    """Immediately execute the overdue invoice escalation pipeline on demand."""
    result = await escalation_service.process_overdue_invoices()
    return result
