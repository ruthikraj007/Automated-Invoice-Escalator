#!/usr/bin/env python3
"""
End-to-End Escalation Pipeline & Email Engine Simulation Script
Tests:
  1. Ingestion of overdue invoices (due 8 days ago, 4 days ago, 15 days ago)
  2. Execution of POST /api/v1/invoices/run-escalation
  3. Verification of Tier 2 progression (8 days overdue), DB record updates, and audit logging
  4. Verification of idempotency (repeated sweep skips already-escalated tiers)
  5. Multi-tier verification (Tier 1 for 4 days, Tier 3 for 15 days)
"""

import time
import json
import sys
import hmac
import hashlib
import httpx
import stripe

BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_SECRET = "whsec_test_secret_12345"


def generate_stripe_signature(payload: str, secret: str) -> str:
    """Generate valid HMAC-SHA256 signature header for Stripe webhook."""
    try:
        return stripe.Webhook.generate_header_for_user_payload(payload, secret, timestamp=int(time.time()))
    except Exception:
        ts = int(time.time())
        signed = f"{ts}.{payload}"
        sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
        return f"t={ts},v1={sig}"


def inject_invoice(client: httpx.Client, invoice_id: str, days_ago: int, customer_name: str, customer_email: str, amount_cents: int):
    """Inject an overdue invoice into tracked_invoices via signed Stripe webhook."""
    due_timestamp = int(time.time()) - (days_ago * 86400)
    event_payload = {
        "id": f"evt_mock_{int(time.time())}_{invoice_id}",
        "object": "event",
        "type": "invoice.finalized",
        "data": {
            "object": {
                "id": invoice_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "amount_due": amount_cents,
                "currency": "usd",
                "status": "open",
                "due_date": due_timestamp,
                "hosted_invoice_url": f"https://invoice.stripe.com/{invoice_id}",
            }
        }
    }
    payload_str = json.dumps(event_payload)
    sig = generate_stripe_signature(payload_str, WEBHOOK_SECRET)
    resp = client.post(
        "/api/v1/webhooks/stripe",
        content=payload_str,
        headers={"Content-Type": "application/json", "Stripe-Signature": sig}
    )
    assert resp.status_code == 200, f"Failed injecting {invoice_id}: {resp.status_code} - {resp.text}"
    return resp.json()


def run_simulation():
    print("=" * 75)
    print("AUTOMATED ESCALATION SCHEDULER & EMAIL ENGINE SIMULATION")
    print("=" * 75)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 0. Health check
    try:
        health = client.get("/health")
        assert health.status_code == 200
        print(f"[OK] Backend active: {health.json()['app']} (Version: {health.json()['version']})")
    except Exception as e:
        print(f"[ERROR] Could not reach backend: {e}")
        sys.exit(1)

    # =========================================================================
    # Test 1: Insert an overdue invoice (8 days overdue)
    # =========================================================================
    test_inv_8d = f"in_overdue_8d_{int(time.time())}"
    print(f"\n--- [Test 1] Injecting 8-day overdue invoice ({test_inv_8d}) ---")
    inject_invoice(
        client=client,
        invoice_id=test_inv_8d,
        days_ago=8,
        customer_name="Jordan Reed (Apex Labs)",
        customer_email="jordan@apexlabs.com",
        amount_cents=320000 # $3,200.00
    )
    print(f"[PASS] Injected {test_inv_8d} with status 'open', due 8 days ago.")

    # Verify initial tier is 0
    inv_check = client.get("/api/v1/invoices/tracked").json()
    matched = next((i for i in inv_check if i["stripe_invoice_id"] == test_inv_8d), None)
    assert matched is not None
    assert matched["current_escalation_tier"] == 0
    print(f"[OK] Verified initial state: current_escalation_tier = {matched['current_escalation_tier']}")

    # =========================================================================
    # Test 2: Execute POST /api/v1/invoices/run-escalation
    # =========================================================================
    print(f"\n--- [Test 2] Triggering POST /api/v1/invoices/run-escalation ---")
    esc_resp = client.post("/api/v1/invoices/run-escalation")
    assert esc_resp.status_code == 200, f"Escalation endpoint failed: {esc_resp.status_code} - {esc_resp.text}"
    result = esc_resp.json()
    print(f"Escalation Response: status={result['status']}, scanned={result['total_overdue_scanned']}, executed={result['escalations_executed']}")

    # Find the escalated record
    esc_entry = next((e for e in result.get("escalations", []) if e["stripe_invoice_id"] == test_inv_8d), None)
    assert esc_entry is not None, f"Invoice {test_inv_8d} was not escalated in result!"
    print(f"[OK] Escalation matched: previous_tier={esc_entry['previous_tier']} -> new_tier={esc_entry['new_tier']}")
    print(f"     Days Overdue: {esc_entry['days_overdue']}")
    print(f"     Recipient: {esc_entry['recipient']}")
    print(f"     Email Status: {esc_entry['email_status']}")

    assert esc_entry["new_tier"] == 2, f"Expected Tier 2 for 8 days overdue, got Tier {esc_entry['new_tier']}"
    print("[PASS] Successfully escalated 8-day overdue invoice to Tier 2 (Firm Notice).")

    # =========================================================================
    # Test 3: Verify Database Record Updated
    # =========================================================================
    print(f"\n--- [Test 3] Verifying database record updates for {test_inv_8d} ---")
    tracked_list = client.get("/api/v1/invoices/tracked").json()
    db_inv = next((i for i in tracked_list if i["stripe_invoice_id"] == test_inv_8d), None)
    assert db_inv is not None
    assert db_inv["current_escalation_tier"] == 2, f"Expected tier 2 in DB, got {db_inv['current_escalation_tier']}"
    assert db_inv.get("last_reminded_at") is not None, "last_reminded_at was not updated!"
    print(f"[OK] DB Record: current_escalation_tier = {db_inv['current_escalation_tier']}")
    print(f"     last_reminded_at = {db_inv['last_reminded_at']}")
    print("[PASS] Database correctly reflects updated escalation tier and timestamp.")

    # =========================================================================
    # Test 4: Verify Audit Logs Table
    # =========================================================================
    print(f"\n--- [Test 4] Verifying audit_logs entry for {test_inv_8d} ---")
    audit_resp = client.get("/api/v1/webhooks/audit-logs")
    assert audit_resp.status_code == 200
    logs = audit_resp.json().get("audit_logs", [])

    matched_log = next(
        (l for l in logs if l.get("event_type") == "invoice.escalated" and l.get("payload", {}).get("stripe_invoice_id") == test_inv_8d),
        None
    )
    assert matched_log is not None, f"Audit log for escalation of {test_inv_8d} not found!"
    print(f"[OK] Audit Log: id={matched_log['id']}")
    print(f"     Event: {matched_log['event_type']}")
    print(f"     Payload: Tier {matched_log['payload']['escalated_tier']} to {matched_log['payload']['recipient_email']}")
    assert matched_log["payload"]["escalated_tier"] == 2
    print("[PASS] Audit log contains verified escalation event.")

    # =========================================================================
    # Test 5: Verify Idempotency (Repeat Escalation Loop)
    # =========================================================================
    print(f"\n--- [Test 5] Verifying Idempotency on second run ---")
    second_run = client.post("/api/v1/invoices/run-escalation").json()
    # The 8-day overdue invoice is already at Tier 2, so it must not be re-escalated to Tier 2
    re_escalated = [e for e in second_run.get("escalations", []) if e["stripe_invoice_id"] == test_inv_8d]
    assert len(re_escalated) == 0, f"Invoice was re-escalated redundantly: {re_escalated}"
    print(f"[OK] Invoices skipped: {second_run['invoices_skipped']}")
    print("[PASS] Idempotency confirmed: already-escalated tier was safely skipped.")

    # =========================================================================
    # Test 6: Verify Tier 1 (4 days overdue) and Tier 3 (15 days overdue)
    # =========================================================================
    print(f"\n--- [Test 6] Testing Tier 1 (4 days overdue) and Tier 3 (15 days overdue) ---")
    test_inv_4d = f"in_overdue_4d_{int(time.time())}"
    test_inv_15d = f"in_overdue_15d_{int(time.time())}"

    inject_invoice(client, test_inv_4d, days_ago=4, customer_name="Sara Chen", customer_email="sara@startup.co", amount_cents=125000)
    inject_invoice(client, test_inv_15d, days_ago=15, customer_name="Mark Sloan", customer_email="mark@enterprise.org", amount_cents=980000)

    multi_run = client.post("/api/v1/invoices/run-escalation").json()
    e_4d = next((e for e in multi_run.get("escalations", []) if e["stripe_invoice_id"] == test_inv_4d), None)
    e_15d = next((e for e in multi_run.get("escalations", []) if e["stripe_invoice_id"] == test_inv_15d), None)

    assert e_4d is not None and e_4d["new_tier"] == 1, f"Expected Tier 1 for 4-day overdue, got {e_4d}"
    print(f"[PASS] 4-day overdue invoice {test_inv_4d} escalated to Tier 1 (Courtesy Reminder).")

    assert e_15d is not None and e_15d["new_tier"] == 3, f"Expected Tier 3 for 15-day overdue, got {e_15d}"
    print(f"[PASS] 15-day overdue invoice {test_inv_15d} escalated to Tier 3 (Final Demand).")

    print("\n" + "=" * 75)
    print("ALL 6 TESTS PASSED! Escalation Scheduler & Email Engine verified.")
    print("=" * 75)


if __name__ == "__main__":
    run_simulation()
