"""Stripe calls this. It has no family cookie and cannot send the CSRF header, so main.py
mounts it outside the CSRF check; the Stripe signature protects it instead."""

from typing import Annotated

from fastapi import APIRouter, Header, Request

from jumbaq.billing.deps import SubscriptionServiceDep
from jumbaq.billing.schemas import WebhookOut

router = APIRouter(tags=["billing"])


@router.post("/billing/webhook")
async def stripe_webhook(
    request: Request,
    billing: SubscriptionServiceDep,
    stripe_signature: Annotated[str | None, Header(alias="Stripe-Signature")] = None,
) -> WebhookOut:
    """A wrong signature gives 400 `billing.bad_signature`. Events we do not use get 200."""
    # The signature covers the exact bytes, so the body is not parsed before the check.
    await billing.receive_webhook(await request.body(), stripe_signature)
    return WebhookOut()
