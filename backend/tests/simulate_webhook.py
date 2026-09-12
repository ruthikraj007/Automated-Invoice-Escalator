#!/usr/bin/env python3
"""
Webhook Simulation Test Script
Generates cryptographically signed mock Stripe webhook events (invoice.payment_failed, invoice.paid)
and transmits them to the FastAPI webhook endpoint, verifying 200 OK responses and database recording.
"""

import hmac
import hashlib
import json
import time
import sys
import httpx
import stripe

BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_ENDPOINT = f"{BASE_URL}/api/v1/webhooks/stripe"
WEBHOOK_SECRET = "whsec_test_secret_12345"


def generate_stripe_signature_header(payload: str, secret: str) -> str:
    """Generate a valid Stripe-Signature header matching Stripe's HMAC-SHA256 specification."""
    try:
        # Use official Stripe SDK helper if available
        header = stripe.Webhook.generate_header_for_user_payload(
            payload, secret, timestamp=int(time.time())
        )
        return header
    except Exception:
        # Fallback manual signature generation
        timestamp = int(time.time())
        signed_payload = f"{timestamp}.{payload}"
        mac = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256
        )
        signature = mac.hexdigest()
        return f"t={timestamp},v1={signature}"


def run_webhook_simulation():
    print("=" * 70)
    print("STRIPE WEBHOOK ENGINE SIMULATION & DATABASE TEST")
    print("=" * 70)

    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 0. Check Backend Health
    try:
        health_resp = client.get("/health")
        if health_resp.status_code != 200:
            print(f"[FAIL] Backend is not healthy: {health_resp.status_code}")
            sys.exit(1)
        print(f"[OK] Backend is healthy: {health_resp.json()['status']}")
    except Exception as e:
        print(f"[ERROR] Could not connect to {BASE_URL}: {e}")
        print("Please ensure the FastAPI backend is running on port 8000.")
        sys.exit(1)

    test_invoice_id = f"in_test_sim_{int(time.time())}"
    customer_email = "alex.founder@techcorp.io"
    customer_name = "Alex Rivera (TechCorp)"
    amount_due_cents = 450000  # $4,500.00
    due_date_epoch = int(time.time()) - (5 * 86400)  # 5 days ago

    # =========================================================================
    # Test 1A: Send signed 'invoice.finalized' event
    # =========================================================================
    print(f"\n--- [Test 1A] Simulating 'invoice.finalized' for {test_invoice_id} ---")
    finalized_event = {
        "id": f"evt_fin_{int(time.time())}",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "type": "invoice.finalized",
        "livemode": False,
        "data": {
            "object": {
                "id": test_invoice_id,
                "object": "invoice",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "amount_due": amount_due_cents,
                "currency": "usd",
                "status": "open",
                "due_date": due_date_epoch,
                "hosted_invoice_url": f"https://invoice.stripe.com/{test_invoice_id}",
            }
        }
    }
    payload_fin_str = json.dumps(finalized_event)
    sig_fin_header = generate_stripe_signature_header(payload_fin_str, WEBHOOK_SECRET)

    response_fin = client.post(
        "/api/v1/webhooks/stripe",
        content=payload_fin_str,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": sig_fin_header,
        }
    )
    assert response_fin.status_code == 200, f"Expected 200, got {response_fin.status_code}"
    body_fin = response_fin.json()
    assert body_fin["status"] == "success"
    assert body_fin["event_type"] == "invoice.finalized"
    assert body_fin["invoice_status"] == "open"
    print("[PASS] invoice.finalized verified and upserted with status 'open'.")

    # =========================================================================
    # Test 1: Send signed 'invoice.payment_failed' event
    # =========================================================================
    print(f"\n--- [Test 1] Simulating 'invoice.payment_failed' for {test_invoice_id} ---")
    payment_failed_event = {
        "id": f"evt_fail_{int(time.time())}",
        "object": "event",
        "api_version": "2023-10-16",
        "created": int(time.time()),
        "type": "invoice.payment_failed",
        "livemode": False,
        "data": {
            "object": {
                "id": test_invoice_id,
                "object": "invoice",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "amount_due": amount_due_cents,
                "currency": "usd",
                "status": "open",
                "due_date": due_date_epoch,
                "attempt_count": 2,
                "hosted_invoice_url": f"https://invoice.stripe.com/{test_invoice_id}",
            }
        }
    }

    payload_str = json.dumps(payment_failed_event)
    sig_header = generate_stripe_signature_header(payload_str, WEBHOOK_SECRET)

    response = client.post(
        "/api/v1/webhooks/stripe",
        content=payload_str,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": sig_header,
        }
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.json()}")

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["status"] == "success"
    assert body["event_type"] == "invoice.payment_failed"
    assert body["stripe_invoice_id"] == test_invoice_id
    assert body["invoice_status"] == "open"
    print("[PASS] invoice.payment_failed verified and processed with HTTP 200 OK.")

    # =========================================================================
    # Test 2: Verify Database Storage for Tracked Invoice
    # =========================================================================
    print(f"\n--- [Test 2] Verifying database records for {test_invoice_id} ---")
    tracked_resp = client.get("/api/v1/invoices/tracked")
    assert tracked_resp.status_code == 200
    tracked_invoices = tracked_resp.json()

    matched_inv = next((inv for inv in tracked_invoices if inv["stripe_invoice_id"] == test_invoice_id), None)
    assert matched_inv is not None, f"Invoice {test_invoice_id} not found in database!"
    print(f"[OK] Database record found: id={matched_inv['id']}")
    print(f"     Status: {matched_inv['status']}")
    print(f"     Customer: {matched_inv['customer_name']} ({matched_inv['customer_email']})")
    print(f"     Amount Due: {matched_inv['amount_due']} cents")
    assert matched_inv["status"] == "open"
    assert matched_inv["customer_email"] == customer_email
    print("[PASS] Database record matches expected invoice fields.")

    # =========================================================================
    # Test 3: Verify Audit Logs Table
    # =========================================================================
    print("\n--- [Test 3] Verifying audit_logs table entry ---")
    audit_resp = client.get("/api/v1/webhooks/audit-logs")
    assert audit_resp.status_code == 200
    audit_logs = audit_resp.json().get("audit_logs", [])

    matched_audit = next(
        (log for log in audit_logs if log.get("payload", {}).get("stripe_invoice_id") == test_invoice_id),
        None
    )
    assert matched_audit is not None, f"Audit log for {test_invoice_id} not found!"
    print(f"[OK] Audit log entry found: id={matched_audit['id']}")
    print(f"     Event: {matched_audit['event_type']}")
    print(f"     Sent at: {matched_audit['sent_at']}")
    print(f"     Summary: {matched_audit['payload'].get('summary')}")
    assert matched_audit["event_type"] == "invoice.payment_failed"
    print("[PASS] Audit log accurately recorded event.")

    # =========================================================================
    # Test 4: Simulating 'invoice.paid' event
    # =========================================================================
    print(f"\n--- [Test 4] Simulating 'invoice.paid' event for {test_invoice_id} ---")
    paid_event = {
        "id": f"evt_paid_{int(time.time())}",
        "object": "event",
        "created": int(time.time()),
        "type": "invoice.paid",
        "data": {
            "object": {
                "id": test_invoice_id,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "amount_due": amount_due_cents,
                "currency": "usd",
                "status": "paid",
            }
        }
    }
    payload_paid_str = json.dumps(paid_event)
    sig_paid_header = generate_stripe_signature_header(payload_paid_str, WEBHOOK_SECRET)

    response_paid = client.post(
        "/api/v1/webhooks/stripe",
        content=payload_paid_str,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": sig_paid_header,
        }
    )
    assert response_paid.status_code == 200
    body_paid = response_paid.json()
    assert body_paid["invoice_status"] == "paid"
    print("[PASS] invoice.paid processed, status updated to 'paid' (escalations halted).")

    # Verify status in DB is now 'paid'
    tracked_resp2 = client.get("/api/v1/invoices/tracked")
    matched_inv2 = next((inv for inv in tracked_resp2.json() if inv["stripe_invoice_id"] == test_invoice_id), None)
    assert matched_inv2 is not None
    assert matched_inv2["status"] == "paid"
    print("[PASS] Verified database record status is now 'paid'.")

    # =========================================================================
    # Test 5: Rejection of Invalid Signature
    # =========================================================================
    print("\n--- [Test 5] Security Check: Rejecting invalid webhook signature ---")
    bad_sig_header = "t=1700000000,v1=invalid_tampered_signature_hex_code_1234567890"
    bad_resp = client.post(
        "/api/v1/webhooks/stripe",
        content=payload_str,
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": bad_sig_header,
        }
    )
    print(f"Status Code with bad signature: {bad_resp.status_code} (Expected 400)")
    assert bad_resp.status_code == 400, f"Expected 400, got {bad_resp.status_code}"
    print("[PASS] Successfully rejected unauthorized webhook request with 400 Bad Request.")

    print("\n" + "=" * 70)
    print("ALL 5 TESTS PASSED SUCCESSFULLY! Stripe Webhook engine is verified.")
    print("=" * 70)


if __name__ == "__main__":
    run_webhook_simulation()
