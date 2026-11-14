"""Pure parts of billing: access, event order, test keys only, and reading Stripe events."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from jumbaq.billing import domain
from jumbaq.billing.domain import Subscription, SubscriptionChange, SubscriptionStatus
from jumbaq.billing.errors import BadSignatureError, BillingNotConfiguredError
from jumbaq.billing.providers.stripe_provider import StripeProvider
from jumbaq.core.config import Settings
from tests.stripe_events import signed, subscription_event

SECRET = "whsec_unit"
FAMILY = uuid.uuid4()
NOON = datetime(2026, 11, 14, 12, 0, tzinfo=UTC)
S = SubscriptionStatus


def test_free_cases_need_no_subscription() -> None:
    assert domain.has_access(1, free_cases=1, statuses=[])
    assert not domain.has_access(2, free_cases=1, statuses=[])
    assert not domain.has_access(2, free_cases=1, statuses=[S.CANCELED, S.PAST_DUE])
    assert domain.has_access(2, free_cases=1, statuses=[S.CANCELED, S.ACTIVE])
    assert domain.has_access(7, free_cases=1, statuses=[S.TRIALING])


def _stored(status: SubscriptionStatus, at: datetime) -> Subscription:
    return Subscription(FAMILY, "sub_1", "cus_1", status, at)


def _change(status: SubscriptionStatus, at: datetime) -> SubscriptionChange:
    return SubscriptionChange("evt", FAMILY, "sub_1", "cus_1", status, at)


def test_an_older_event_does_not_undo_a_newer_one() -> None:
    later = NOON + timedelta(seconds=5)
    assert domain.is_newer(_stored(S.ACTIVE, NOON), _change(S.CANCELED, later))
    assert not domain.is_newer(_stored(S.CANCELED, later), _change(S.ACTIVE, NOON))


def test_in_the_same_second_the_later_stage_wins() -> None:
    # "created" (incomplete) and "updated" (active) often share a second, in any order.
    assert domain.is_newer(_stored(S.INCOMPLETE, NOON), _change(S.ACTIVE, NOON))
    assert not domain.is_newer(_stored(S.ACTIVE, NOON), _change(S.INCOMPLETE, NOON))
    assert not domain.is_newer(_stored(S.ACTIVE, NOON), _change(S.ACTIVE, NOON))


def test_settings_refuse_a_live_stripe_key() -> None:
    base: dict[str, Any] = {"database_url": "x", "redis_url": "y"}
    with pytest.raises(ValidationError):
        Settings(**base, stripe_secret_key="sk_live_123")
    assert Settings(**base, stripe_secret_key="sk_test_123").stripe_secret_key is not None
    assert Settings(**base, stripe_secret_key="").stripe_secret_key is not None


def _provider(webhook_secret: str | None = SECRET) -> StripeProvider:
    return StripeProvider("sk_test_unit", webhook_secret, 799, "usd")


def test_a_signed_subscription_event_is_read() -> None:
    event = subscription_event(FAMILY, "active", subscription_id="sub_9", created=1_800_000_000)
    change = _provider().parse_event(*signed(event, SECRET))

    assert change == SubscriptionChange(
        event["id"], FAMILY, "sub_9", "cus_test", S.ACTIVE,
        datetime.fromtimestamp(1_800_000_000, UTC), event["type"],
    )  # fmt: skip


def test_a_wrong_signature_is_refused() -> None:
    body, header = signed(subscription_event(FAMILY, "active"), "whsec_someone_else")
    with pytest.raises(BadSignatureError):
        _provider().parse_event(body, header)
    with pytest.raises(BadSignatureError):
        _provider().parse_event(body, None)


def test_a_changed_body_is_refused() -> None:
    body, header = signed(subscription_event(FAMILY, "canceled"), SECRET)
    with pytest.raises(BadSignatureError):
        _provider().parse_event(body.replace(b"canceled", b"active"), header)


@pytest.mark.parametrize(
    "event",
    [
        subscription_event(FAMILY, "active", event_type="invoice.paid"),
        subscription_event(None, "active"),
        subscription_event(FAMILY, "some_new_status"),
    ],
)
def test_events_we_do_not_use_are_ignored(event: dict[str, Any]) -> None:
    assert _provider().parse_event(*signed(event, SECRET)) is None


def test_without_a_webhook_secret_events_are_not_read() -> None:
    with pytest.raises(BillingNotConfiguredError):
        _provider(webhook_secret=None).parse_event(b"{}", "t=1,v1=x")


async def test_without_a_secret_key_there_is_no_checkout() -> None:
    provider = StripeProvider(None, SECRET, 799, "usd")
    with pytest.raises(BillingNotConfiguredError):
        await provider.create_checkout(FAMILY, "https://a/ok", "https://a/no")


async def test_the_checkout_is_a_monthly_subscription_that_carries_the_family() -> None:
    provider = _provider()
    sent: dict[str, Any] = {}

    async def create_async(params: dict[str, Any]) -> Any:
        sent.update(params)
        return type("Session", (), {"url": "https://checkout.stripe.com/c/pay/cs_test"})()

    provider._client.v1.checkout.sessions.create_async = create_async  # type: ignore[union-attr, method-assign]
    url = await provider.create_checkout(FAMILY, "https://a/ok", "https://a/no")

    assert url == "https://checkout.stripe.com/c/pay/cs_test"
    assert sent["mode"] == "subscription"
    price = sent["line_items"][0]["price_data"]
    assert (price["unit_amount"], price["currency"], price["recurring"]) == (
        799, "usd", {"interval": "month"},
    )  # fmt: skip
    assert sent["subscription_data"]["metadata"] == {"family_id": str(FAMILY)}


def test_a_cancel_at_period_end_reads_the_end_of_the_period() -> None:
    event = subscription_event(FAMILY, "active", cancel_at_period_end=True)
    event["data"]["object"]["current_period_end"] = 1_800_100_000
    change = _provider().parse_event(*signed(event, SECRET))

    assert change is not None
    assert change.cancels_at == datetime.fromtimestamp(1_800_100_000, UTC)

    event["data"]["object"]["cancel_at_period_end"] = False
    change = _provider().parse_event(*signed(event, SECRET))

    assert change is not None
    assert change.cancels_at is None
