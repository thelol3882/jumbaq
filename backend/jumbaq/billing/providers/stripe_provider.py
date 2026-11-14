"""Stripe Checkout in subscription mode, and its webhook events."""

import logging
import uuid
from datetime import UTC, datetime

import stripe

from jumbaq.billing.domain import SubscriptionChange, SubscriptionStatus
from jumbaq.billing.errors import (
    BadSignatureError,
    BillingNotConfiguredError,
    BillingUnavailableError,
)

logger = logging.getLogger(__name__)

PRODUCT_NAME = "jumbaq: a new detective case every week"
# Only these events change a subscription. Stripe sends many more; we answer them 200.
SUBSCRIPTION_EVENTS = frozenset(
    {
        "customer.subscription.created",
        "customer.subscription.updated",
        "customer.subscription.deleted",
    }
)


class StripeProvider:
    def __init__(
        self,
        secret_key: str | None,
        webhook_secret: str | None,
        price_cents: int,
        currency: str,
    ) -> None:
        self._webhook_secret = webhook_secret
        self._price_cents = price_cents
        self._currency = currency
        self._client = (
            stripe.StripeClient(secret_key, http_client=stripe.HTTPXClient(), max_network_retries=1)
            if secret_key
            else None
        )

    async def create_checkout(self, family_id: uuid.UUID, success_url: str, cancel_url: str) -> str:
        if self._client is None:
            raise BillingNotConfiguredError("no Stripe secret key")
        try:
            session = await self._client.v1.checkout.sessions.create_async(
                params={
                    "mode": "subscription",
                    "line_items": [
                        {
                            "quantity": 1,
                            # Set here, so nothing has to be made in the Stripe dashboard.
                            "price_data": {
                                "currency": self._currency,
                                "unit_amount": self._price_cents,
                                "recurring": {"interval": "month"},
                                "product_data": {"name": PRODUCT_NAME},
                            },
                        }
                    ],
                    # The subscription carries the family, so every later event finds it.
                    "subscription_data": {"metadata": {"family_id": str(family_id)}},
                    "client_reference_id": str(family_id),
                    "success_url": success_url,
                    "cancel_url": cancel_url,
                }
            )
        except (stripe.APIConnectionError, stripe.RateLimitError, stripe.APIError) as error:
            raise BillingUnavailableError(type(error).__name__) from error
        if session.url is None:
            raise BillingUnavailableError("Stripe gave no checkout url")
        return session.url

    def parse_event(self, payload: bytes, signature: str | None) -> SubscriptionChange | None:
        if not self._webhook_secret:
            raise BillingNotConfiguredError("no Stripe webhook secret")
        try:
            event = stripe.Webhook.construct_event(payload, signature, self._webhook_secret)
        except (stripe.SignatureVerificationError, ValueError) as error:
            raise BadSignatureError() from error
        if event.type not in SUBSCRIPTION_EVENTS:
            return None
        subscription = event.data.object.to_dict()
        family_id = (subscription.get("metadata") or {}).get("family_id")
        if not family_id:
            # Not made by our checkout, for example a test event from the dashboard.
            logger.info("Stripe event %s has no family, ignored", event.id)
            return None
        try:
            status = SubscriptionStatus(subscription["status"])
        except ValueError:
            logger.warning("Stripe event %s has an unknown status, ignored", event.id)
            return None
        return SubscriptionChange(
            event_id=event.id,
            family_id=uuid.UUID(family_id),
            provider_ref=subscription["id"],
            customer_ref=str(subscription.get("customer") or ""),
            status=status,
            changed_at=datetime.fromtimestamp(event.created, UTC),
        )
