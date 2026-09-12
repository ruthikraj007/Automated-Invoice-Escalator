import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, Header, HTTPException
import stripe
from app.core.config import settings
from app.core.database import (
    upsert_tracked_invoice,
    update_invoice_status,
    insert_audit_log,
    get_audit_logs,
    get_tracked_invoice,
)

logger = logging.getLogger("app.api.webhooks")
router = APIRouter()


def _extract_invoice_fields(invoice_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to extract normalized fields from a Stripe Invoice object."""
    stripe_invoice_id = invoice_obj.get("id")
    customer_name = (
        invoice_obj.get("customer_name")
        or (invoice_obj.get("customer_details") or {}).get("name")
        or "Valued Customer"
    )
    customer_email = (
        invoice_obj.get("customer_email")
        or (invoice_obj.get("customer_details") or {}).get("email")
        or "billing@customer.com"
    )
    amount_due = invoice_obj.get("amount_due", 0)
    currency = invoice_obj.get("currency", "usd")

    # Parse due_date (timestamp integer or ISO string)
    raw_due_date = invoice_obj.get("due_date")
    if isinstance(raw_due_date, (int, float)):
        due_date_iso = datetime.fromtimestamp(raw_due_date, tz=timezone.utc).isoformat()
    elif isinstance(raw_due_date, str):
        due_date_iso = raw_due_date
    else:
        due_date_iso = datetime.now(timezone.utc).isoformat()

    return {
        "stripe_invoice_id": stripe_invoice_id,
        "customer_name": customer_name,
        "customer_email": customer_email,
        "amount_due": int(amount_due),
        "currency": currency,
        "due_date": due_date_iso,
    }


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """
    Stripe webhook endpoint.
    Verifies cryptographic signature using stripe.Webhook.construct_event and STRIPE_WEBHOOK_SECRET.
    Dispatches:
      - invoice.finalized -> Upsert into tracked_invoices with status 'open'
      - invoice.payment_failed -> Upsert/update tracked_invoices with status 'open'
      - invoice.paid -> Update tracked_invoices status to 'paid', halting escalations
      - All events logged to audit_logs
    """
    if not stripe_signature:
        logger.error("Missing Stripe-Signature header.")
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        logger.error(f"Invalid payload for Stripe webhook: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Stripe signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Unexpected error constructing Stripe webhook event: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    if hasattr(event, "to_dict"):
        event_dict = event.to_dict()
    else:
        event_dict = dict(event)

    event_type = event_dict.get("type", "")
    event_data = event_dict.get("data", {})
    invoice_obj = event_data.get("object", {})
    stripe_invoice_id = invoice_obj.get("id")

    logger.info(f"Verified Stripe webhook event: {event_type} (Invoice: {stripe_invoice_id})")

    invoice_record = None

    if event_type == "invoice.finalized":
        extracted = _extract_invoice_fields(invoice_obj)
        extracted["status"] = "open"
        invoice_record = upsert_tracked_invoice(extracted)
        logger.info(f"Recorded finalized invoice {stripe_invoice_id} as 'open'.")

    elif event_type == "invoice.payment_failed":
        extracted = _extract_invoice_fields(invoice_obj)
        extracted["status"] = "open"
        invoice_record = upsert_tracked_invoice(extracted)
        logger.info(f"Recorded payment failure on invoice {stripe_invoice_id}. Status remains 'open'.")

    elif event_type == "invoice.paid":
        invoice_record = update_invoice_status(stripe_invoice_id, status="paid")
        if not invoice_record:
            extracted = _extract_invoice_fields(invoice_obj)
            extracted["status"] = "paid"
            invoice_record = upsert_tracked_invoice(extracted)
        logger.info(f"Updated invoice {stripe_invoice_id} to 'paid'. Halting escalations.")

    # Record all webhook events to audit_logs
    audit_entry = insert_audit_log(
        invoice_id=invoice_record.get("id") if invoice_record else None,
        event_type=event_type,
        payload={
            "stripe_event_id": event_dict.get("id"),
            "stripe_invoice_id": stripe_invoice_id,
            "event_type": event_type,
            "created": event_dict.get("created"),
            "livemode": event_dict.get("livemode", False),
            "summary": f"Processed Stripe event {event_type} for invoice {stripe_invoice_id}"
        }
    )

    return {
        "status": "success",
        "event_type": event_type,
        "stripe_invoice_id": stripe_invoice_id,
        "invoice_status": invoice_record.get("status") if invoice_record else None,
        "audit_log_id": audit_entry.get("id"),
    }


@router.get("/audit-logs")
def list_audit_logs():
    """Retrieve recent audit logs for debugging and verification."""
    return {"audit_logs": get_audit_logs(limit=50)}


@router.post("/resend")
async def resend_webhook(request: Request):
    """Listen for Resend email delivery events."""
    body = await request.json()
    event_type = body.get("type", "email.unknown")
    data = body.get("data", {})
    logger.info(f"Resend webhook event: {event_type} for email {data.get('email_id')}")

    insert_audit_log(
        invoice_id=None,
        event_type=f"resend.{event_type}",
        payload=body
    )

    return {"status": "processed", "type": event_type}
