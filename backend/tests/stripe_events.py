"""Stripe webhook events for tests, signed the way Stripe signs them.

The scheme: header `t=<unix time>,v1=<hex HMAC-SHA256 of "<t>.<body>" with the webhook secret>`.
"""

import hashlib
import hmac
import json
import time
import uuid
from typing import Any


def subscription_event(
    family_id: uuid.UUID | None,
    status: str,
    *,
    subscription_id: str = "sub_test",
    created: int | None = None,
    event_type: str = "customer.subscription.updated",
    event_id: str | None = None,
    customer: str = "cus_test",
    cancel_at_period_end: bool = False,
    cancel_at: int | None = None,
) -> dict[str, Any]:
    metadata = {"family_id": str(family_id)} if family_id else {}
    return {
        "id": event_id or f"evt_{uuid.uuid4().hex}",
        "object": "event",
        "type": event_type,
        "created": created if created is not None else int(time.time()),
        "livemode": False,
        "data": {
            "object": {
                "id": subscription_id,
                "object": "subscription",
                "customer": customer,
                "status": status,
                "metadata": metadata,
                "cancel_at_period_end": cancel_at_period_end,
                "cancel_at": cancel_at,
            }
        },
    }


def signed(event: dict[str, Any], secret: str) -> tuple[bytes, str]:
    """The body and the Stripe-Signature header."""
    body = json.dumps(event).encode()
    timestamp = int(time.time())
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256)
    return body, f"t={timestamp},v1={digest.hexdigest()}"
