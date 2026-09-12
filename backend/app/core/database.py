import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger("app.database")

supabase_client = None

# In-memory storage for development & testing when Supabase credentials are unset
_in_memory_db = {
    "tracked_invoices": {},  # stripe_invoice_id -> invoice_dict
    "audit_logs": [],        # list of audit log dicts
    "escalation_rules": [],
    "profiles": {}
}

def get_supabase_client():
    global supabase_client
    if supabase_client is not None:
        return supabase_client

    if settings.SUPABASE_URL and settings.SUPABASE_KEY:
        try:
            from supabase import create_client
            supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
            logger.info("Supabase client successfully initialized.")
            return supabase_client
        except Exception as e:
            logger.warning(f"Failed to initialize Supabase client: {e}. Falling back to in-memory store.")
            return None
    else:
        logger.info("Supabase credentials not configured. Running in in-memory dev mode.")
        return None


def upsert_tracked_invoice(invoice_data: Dict[str, Any]) -> Dict[str, Any]:
    """Upsert invoice into tracked_invoices table or in-memory store."""
    client = get_supabase_client()
    stripe_invoice_id = invoice_data.get("stripe_invoice_id")

    if client:
        try:
            res = client.table("tracked_invoices").upsert(
                invoice_data,
                on_conflict="stripe_invoice_id"
            ).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return invoice_data
        except Exception as e:
            logger.error(f"Supabase upsert_tracked_invoice error: {e}")
            raise e

    # In-memory store fallback
    existing = _in_memory_db["tracked_invoices"].get(stripe_invoice_id, {})
    record = {
        "id": existing.get("id", str(uuid.uuid4())),
        "user_id": invoice_data.get("user_id", existing.get("user_id")),
        "stripe_invoice_id": stripe_invoice_id,
        "customer_name": invoice_data.get("customer_name", existing.get("customer_name", "Unknown")),
        "customer_email": invoice_data.get("customer_email", existing.get("customer_email", "unknown@example.com")),
        "amount_due": invoice_data.get("amount_due", existing.get("amount_due", 0)),
        "currency": invoice_data.get("currency", existing.get("currency", "usd")),
        "due_date": invoice_data.get("due_date", existing.get("due_date", datetime.now(timezone.utc).isoformat())),
        "status": invoice_data.get("status", existing.get("status", "open")),
        "current_escalation_tier": invoice_data.get("current_escalation_tier", existing.get("current_escalation_tier", 0)),
        "last_reminded_at": invoice_data.get("last_reminded_at", existing.get("last_reminded_at")),
        "created_at": existing.get("created_at", datetime.now(timezone.utc).isoformat()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _in_memory_db["tracked_invoices"][stripe_invoice_id] = record
    logger.info(f"Recorded tracked invoice {stripe_invoice_id} with status '{record['status']}'.")
    return record


def update_invoice_status(stripe_invoice_id: str, status: str) -> Optional[Dict[str, Any]]:
    """Update invoice status in tracked_invoices."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("tracked_invoices").update(
                {"status": status}
            ).eq("stripe_invoice_id", stripe_invoice_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error(f"Supabase update_invoice_status error: {e}")
            raise e

    # In-memory store fallback
    if stripe_invoice_id in _in_memory_db["tracked_invoices"]:
        record = _in_memory_db["tracked_invoices"][stripe_invoice_id]
        record["status"] = status
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Updated tracked invoice {stripe_invoice_id} to status '{status}'.")
        return record
    return None


def get_tracked_invoice(stripe_invoice_id: str) -> Optional[Dict[str, Any]]:
    """Fetch tracked invoice by Stripe invoice ID."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("tracked_invoices").select("*").eq("stripe_invoice_id", stripe_invoice_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error(f"Supabase get_tracked_invoice error: {e}")
            return None

    return _in_memory_db["tracked_invoices"].get(stripe_invoice_id)


def get_all_tracked_invoices() -> List[Dict[str, Any]]:
    """Retrieve all tracked invoices."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("tracked_invoices").select("*").order("created_at", desc=True).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Supabase get_all_tracked_invoices error: {e}")
            return []

    return list(_in_memory_db["tracked_invoices"].values())


def get_open_overdue_invoices() -> List[Dict[str, Any]]:
    """Retrieve all open invoices whose due_date is in the past."""
    now_iso = datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()
    if client:
        try:
            res = client.table("tracked_invoices").select("*")\
                .eq("status", "open")\
                .lt("due_date", now_iso)\
                .order("due_date", desc=False)\
                .execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Supabase get_open_overdue_invoices error: {e}")
            return []

    # In-memory fallback
    now = datetime.now(timezone.utc)
    overdue = []
    for inv in _in_memory_db["tracked_invoices"].values():
        if inv.get("status") == "open":
            due_date_str = inv.get("due_date")
            try:
                if isinstance(due_date_str, str):
                    due_date = datetime.fromisoformat(due_date_str.replace("Z", "+00:00"))
                elif isinstance(due_date_str, (int, float)):
                    due_date = datetime.fromtimestamp(due_date_str, tz=timezone.utc)
                else:
                    continue
                if due_date < now:
                    overdue.append(inv)
            except Exception as e:
                logger.warning(f"Failed to parse due_date '{due_date_str}': {e}")
    return overdue


def update_invoice_escalation_tier(
    stripe_invoice_id: str,
    tier: int,
    last_reminded_at: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Update current_escalation_tier and last_reminded_at for an invoice."""
    reminded_at = last_reminded_at or datetime.now(timezone.utc).isoformat()
    client = get_supabase_client()
    if client:
        try:
            res = client.table("tracked_invoices").update({
                "current_escalation_tier": tier,
                "last_reminded_at": reminded_at,
            }).eq("stripe_invoice_id", stripe_invoice_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception as e:
            logger.error(f"Supabase update_invoice_escalation_tier error: {e}")
            raise e

    if stripe_invoice_id in _in_memory_db["tracked_invoices"]:
        record = _in_memory_db["tracked_invoices"][stripe_invoice_id]
        record["current_escalation_tier"] = tier
        record["last_reminded_at"] = reminded_at
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Updated invoice {stripe_invoice_id} to tier {tier} (reminded_at: {reminded_at}).")
        return record
    return None


def insert_audit_log(invoice_id: Optional[str], event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record an event into the audit_logs table."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("audit_logs").insert({
                "invoice_id": invoice_id,
                "event_type": event_type,
                "payload": payload,
            }).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
        except Exception as e:
            logger.error(f"Supabase insert_audit_log error: {e}")

    # In-memory fallback
    log_entry = {
        "id": str(uuid.uuid4()),
        "invoice_id": invoice_id,
        "event_type": event_type,
        "payload": payload,
        "sent_at": datetime.now(timezone.utc).isoformat()
    }
    _in_memory_db["audit_logs"].append(log_entry)
    logger.info(f"Logged audit event '{event_type}' for invoice_id '{invoice_id}'.")
    return log_entry


def get_audit_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve audit logs."""
    client = get_supabase_client()
    if client:
        try:
            res = client.table("audit_logs").select("*").order("sent_at", desc=True).limit(limit).execute()
            return res.data or []
        except Exception as e:
            logger.error(f"Supabase get_audit_logs error: {e}")
            return []

    return list(reversed(_in_memory_db["audit_logs"]))[:limit]
