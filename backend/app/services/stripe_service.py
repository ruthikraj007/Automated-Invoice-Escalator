import logging
from typing import Dict, Any, List, Optional
import stripe
from app.core.config import settings

logger = logging.getLogger("app.services.stripe")

class StripeService:
    def __init__(self):
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            self.configured = True
        else:
            self.configured = False
            logger.info("Stripe secret key not configured; operating in mock mode.")

    def verify_webhook_signature(self, payload: bytes, sig_header: str) -> Optional[Dict[str, Any]]:
        """Verify Stripe webhook signature or return mock event in dev mode."""
        if not self.configured or not settings.STRIPE_WEBHOOK_SECRET:
            logger.warning("Stripe webhook verification bypassed in development mode.")
            return {"type": "mock.event", "data": {"object": {}}}

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except Exception as e:
            logger.error(f"Error verifying Stripe webhook: {e}")
            raise e

    def get_invoices(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve invoices from Stripe or return mock invoices in dev mode."""
        if not self.configured:
            return [
                {
                    "id": "in_mock_001",
                    "customer_name": "Acme Corp",
                    "customer_email": "finance@acme.com",
                    "amount_due": 3450.00,
                    "currency": "usd",
                    "status": "open",
                    "due_date": "2026-09-01T00:00:00Z",
                    "days_overdue": 11,
                    "escalation_stage": 2,
                    "hosted_invoice_url": "https://invoice.stripe.com/mock_001"
                },
                {
                    "id": "in_mock_002",
                    "customer_name": "Globex Inc",
                    "customer_email": "billing@globex.io",
                    "amount_due": 8900.00,
                    "currency": "usd",
                    "status": "open",
                    "due_date": "2026-08-15T00:00:00Z",
                    "days_overdue": 28,
                    "escalation_stage": 3,
                    "hosted_invoice_url": "https://invoice.stripe.com/mock_002"
                },
                {
                    "id": "in_mock_003",
                    "customer_name": "Soylent Tech",
                    "customer_email": "accounts@soylent.com",
                    "amount_due": 1200.00,
                    "currency": "usd",
                    "status": "paid",
                    "due_date": "2026-09-10T00:00:00Z",
                    "days_overdue": 0,
                    "escalation_stage": 0,
                    "hosted_invoice_url": "https://invoice.stripe.com/mock_003"
                },
                {
                    "id": "in_mock_004",
                    "customer_name": "Initech Systems",
                    "customer_email": "peter@initech.org",
                    "amount_due": 15400.00,
                    "currency": "usd",
                    "status": "open",
                    "due_date": "2026-08-05T00:00:00Z",
                    "days_overdue": 38,
                    "escalation_stage": 4,
                    "hosted_invoice_url": "https://invoice.stripe.com/mock_004"
                }
            ]

        try:
            invoices = stripe.Invoice.list(limit=limit)
            return invoices.data
        except Exception as e:
            logger.error(f"Error fetching Stripe invoices: {e}")
            return []

    def create_payment_session(self, invoice_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create a payment recovery session for an overdue invoice."""
        if not self.configured:
            return {
                "session_id": f"cs_mock_{invoice_id}",
                "url": f"https://checkout.stripe.com/pay/mock_{invoice_id}"
            }
        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
            )
            return {"session_id": session.id, "url": session.url}
        except Exception as e:
            logger.error(f"Error creating Stripe checkout session: {e}")
            raise e

stripe_service = StripeService()
