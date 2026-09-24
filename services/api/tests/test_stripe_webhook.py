from __future__ import annotations

import hashlib
import hmac
import json
import time


def _signature(payload: bytes, secret: str, timestamp: int | None = None) -> str:
    timestamp = timestamp or int(time.time())
    signed_payload = f"{timestamp}.".encode() + payload
    digest = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def test_stripe_webhook_accepts_a_valid_signature(client, monkeypatch):
    secret = "whsec_test_fixture"
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", secret)
    payload = json.dumps(
        {
            "id": "evt_test_verified",
            "object": "event",
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": "pi_test_safe_reference"}},
        },
        separators=(",", ":"),
    ).encode()

    response = client.post(
        "/api/payments/stripe/webhook",
        content=payload,
        headers={
            "content-type": "application/json",
            "stripe-signature": _signature(payload, secret),
        },
    )

    assert response.status_code == 200
    assert response.json() == {"received": True}


def test_stripe_webhook_rejects_an_invalid_signature(client, monkeypatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_correct")
    payload = b'{"id":"evt_test_invalid","object":"event"}'

    response = client.post(
        "/api/payments/stripe/webhook",
        content=payload,
        headers={"stripe-signature": _signature(payload, "whsec_wrong")},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid Stripe webhook"}


def test_stripe_webhook_fails_closed_while_secret_is_placeholder(client, monkeypatch):
    monkeypatch.setenv(
        "STRIPE_WEBHOOK_SECRET", "PASTE_STRIPE_WEBHOOK_SECRET_HERE"
    )
    payload = b'{"id":"evt_test_unconfigured","object":"event"}'

    response = client.post(
        "/api/payments/stripe/webhook",
        content=payload,
        headers={"stripe-signature": _signature(payload, "unused")},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Stripe webhook is not configured"}
