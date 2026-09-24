from __future__ import annotations

import logging
import os

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from stripe import SignatureVerificationError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments/stripe", tags=["payments"])


def _webhook_secret() -> str:
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret or secret.startswith("PASTE_"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe webhook is not configured",
        )
    return secret


@router.post("/webhook", include_in_schema=False)
async def receive_stripe_webhook(request: Request) -> dict[str, bool]:
    """Verify and acknowledge Stripe events without accepting card data.

    Payment state mutation will be connected when Tralvana creates its first
    PaymentIntent. Until then this endpoint deliberately records only safe
    identifiers in application logs.
    """

    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=_webhook_secret(),
        )
    except (ValueError, SignatureVerificationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook",
        ) from exc

    logger.info(
        "Verified Stripe webhook event id=%s type=%s",
        getattr(event, "id", "unknown"),
        getattr(event, "type", "unknown"),
    )
    return {"received": True}
