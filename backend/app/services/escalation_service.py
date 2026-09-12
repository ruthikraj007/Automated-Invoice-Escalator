import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.services.email_service import email_service
from app.core.database import (
    get_open_overdue_invoices,
    update_invoice_escalation_tier,
    insert_audit_log,
)

logger = logging.getLogger("app.services.escalation")

# Standard 3-Tier Escalation Thresholds
DEFAULT_TIER_RULES = [
    {
        "tier": 1,
        "name": "Courtesy Reminder",
        "days_overdue": 3,
        "description": "Polite reminder with invoice summary and direct payment link."
    },
    {
        "tier": 2,
        "name": "Firm Notice",
        "days_overdue": 7,
        "description": "Firm notice emphasizing urgency, service continuity, and late charges."
    },
    {
        "tier": 3,
        "name": "Final Demand",
        "days_overdue": 14,
        "description": "Final demand notice prior to service suspension or escalation."
    }
]


class EscalationService:
    def __init__(self):
        self.rules = list(DEFAULT_TIER_RULES)
        self.scheduler = AsyncIOScheduler()

    def determine_target_tier(self, days_overdue: int) -> int:
        """
        Determine target escalation tier (1, 2, or 3) based on days overdue:
          - Tier 3: >= 14 days overdue
          - Tier 2: >= 7 days overdue
          - Tier 1: >= 3 days overdue
          - 0: < 3 days overdue (in grace period)
        """
        if days_overdue >= 14:
            return 3
        elif days_overdue >= 7:
            return 2
        elif days_overdue >= 3:
            return 1
        return 0

    def format_amount(self, amount_raw: Any, currency: str = "usd") -> str:
        """Format amount in dollars/currency string."""
        try:
            val = float(amount_raw)
            # If amount is stored in cents (e.g. 450000 -> $4,500.00)
            if val > 100:
                val = val / 100.0
            return f"${val:,.2f} {currency.upper()}"
        except Exception:
            return f"${amount_raw} {currency.upper()}"

    def format_date(self, date_val: Any) -> str:
        """Format date into human-readable YYYY-MM-DD string."""
        if isinstance(date_val, (int, float)):
            return datetime.fromtimestamp(date_val, tz=timezone.utc).strftime("%Y-%m-%d")
        elif isinstance(date_val, str):
            try:
                dt = datetime.fromisoformat(date_val.replace("Z", "+00:00"))
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return date_val[:10]
        return str(date_val)

    async def process_overdue_invoices(self) -> Dict[str, Any]:
        """
        Core automated escalation pipeline:
          1. Fetch all tracked_invoices where status == 'open' and due_date < now()
          2. For each invoice, calculate days_overdue = (now - due_date).days
          3. Match against escalation_rules to determine target tier (1, 2, or 3)
          4. Skip if invoice's current_escalation_tier is already >= target_tier
          5. Dispatch email via email_service
          6. Update tracked_invoices: set current_escalation_tier = target_tier, last_reminded_at = now()
          7. Insert record into audit_logs capturing tier, recipient, invoice ID, and dispatch status
        """
        now = datetime.now(timezone.utc)
        logger.info(f"Executing overdue invoice escalation processing at {now.isoformat()}...")

        overdue_invoices = get_open_overdue_invoices()
        scanned_count = len(overdue_invoices)
        escalated_records = []
        skipped_count = 0

        for invoice in overdue_invoices:
            stripe_invoice_id = invoice.get("stripe_invoice_id")
            raw_due_date = invoice.get("due_date")

            # Parse due date to datetime
            try:
                if isinstance(raw_due_date, (int, float)):
                    due_date = datetime.fromtimestamp(raw_due_date, tz=timezone.utc)
                elif isinstance(raw_due_date, str):
                    due_date = datetime.fromisoformat(raw_due_date.replace("Z", "+00:00"))
                else:
                    due_date = now
            except Exception as e:
                logger.error(f"Error parsing due date for {stripe_invoice_id}: {e}")
                continue

            # Calculate days overdue
            days_overdue = (now - due_date).days
            target_tier = self.determine_target_tier(days_overdue)
            current_tier = invoice.get("current_escalation_tier", 0)

            # Rule: Skip if already at or beyond target tier or not yet eligible
            if target_tier == 0 or current_tier >= target_tier:
                skipped_count += 1
                logger.info(
                    f"Skipping invoice {stripe_invoice_id}: days_overdue={days_overdue}, "
                    f"current_tier={current_tier}, target_tier={target_tier}"
                )
                continue

            # Prepare dynamic template variables
            customer_name = invoice.get("customer_name", "Valued Customer")
            customer_email = invoice.get("customer_email", "billing@example.com")
            formatted_amount = self.format_amount(invoice.get("amount_due", 0), invoice.get("currency", "usd"))
            formatted_due_date = self.format_date(due_date)
            payment_link = invoice.get(
                "hosted_invoice_url",
                f"https://invoice.stripe.com/{stripe_invoice_id}"
            )

            # Dispatch escalation email
            email_result = email_service.send_escalation_email(
                recipient_email=customer_email,
                customer_name=customer_name,
                invoice_id=stripe_invoice_id,
                amount_due=formatted_amount,
                due_date=formatted_due_date,
                payment_link=payment_link,
                tier=target_tier,
                company_name=settings.APP_NAME
            )

            # Update tracked invoice in database
            now_iso = now.isoformat()
            updated_invoice = update_invoice_escalation_tier(
                stripe_invoice_id=stripe_invoice_id,
                tier=target_tier,
                last_reminded_at=now_iso
            )

            # Insert audit log
            audit_entry = insert_audit_log(
                invoice_id=invoice.get("id"),
                event_type="invoice.escalated",
                payload={
                    "stripe_invoice_id": stripe_invoice_id,
                    "previous_tier": current_tier,
                    "escalated_tier": target_tier,
                    "days_overdue": days_overdue,
                    "recipient_email": customer_email,
                    "amount_due": formatted_amount,
                    "email_status": email_result.get("status"),
                    "email_id": email_result.get("id"),
                    "timestamp": now_iso
                }
            )

            record_summary = {
                "stripe_invoice_id": stripe_invoice_id,
                "previous_tier": current_tier,
                "new_tier": target_tier,
                "days_overdue": days_overdue,
                "recipient": customer_email,
                "email_status": email_result.get("status"),
                "audit_log_id": audit_entry.get("id"),
            }
            escalated_records.append(record_summary)
            logger.info(
                f"Escalated invoice {stripe_invoice_id} to Tier {target_tier} "
                f"({days_overdue} days overdue) for {customer_email}."
            )

        summary = {
            "status": "completed",
            "timestamp": now.isoformat(),
            "total_overdue_scanned": scanned_count,
            "escalations_executed": len(escalated_records),
            "invoices_skipped": skipped_count,
            "escalations": escalated_records,
        }
        return summary

    def start_scheduler(self):
        """Start the background scheduler running every 6 hours."""
        if not self.scheduler.running:
            self.scheduler.add_job(
                self.process_overdue_invoices,
                "interval",
                hours=6,
                id="periodic_escalation_job",
                replace_existing=True
            )
            self.scheduler.start()
            logger.info("APScheduler initialized: Running overdue invoice escalations every 6 hours.")

    def stop_scheduler(self):
        """Stop scheduler on app shutdown."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("APScheduler stopped.")


escalation_service = EscalationService()
