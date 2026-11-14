"""The subscription through the real app: checkout, Stripe webhooks and access to cases.

No test calls Stripe: the checkout is replaced, and the webhook events are signed here with the
test secret of the Makefile and checked by the real Stripe code.
"""

import time
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.billing.deps import build_payment_provider, get_payment_provider
from jumbaq.billing.errors import BillingUnavailableError
from jumbaq.billing.models import SubscriptionRow
from jumbaq.billing.providers.stripe_provider import StripeProvider
from jumbaq.billing.public import (
    PaymentRequiredError,
    SubscriptionActivated,
    build_billing_access,
)
from jumbaq.core.config import Settings
from jumbaq.core.csrf import CSRF_HEADER
from jumbaq.core.family import FamilyRef
from jumbaq.core.outbox import OutboxRow
from jumbaq.families.deps import FAMILY_COOKIE
from tests.flows import create_family
from tests.stripe_events import signed, subscription_event

pytestmark = pytest.mark.integration

Sessionmaker = async_sessionmaker[AsyncSession]
WEBHOOK = "/api/v1/billing/webhook"


class FakeCheckout:
    """The real Stripe provider for webhooks, with a checkout that only records the call."""

    def __init__(self, real: StripeProvider) -> None:
        self._real = real
        self.calls: list[tuple[uuid.UUID, str, str]] = []
        self.portal_calls: list[tuple[str, str]] = []
        self.fail: Exception | None = None

    async def create_checkout(self, family_id: uuid.UUID, success_url: str, cancel_url: str) -> str:
        if self.fail:
            raise self.fail
        self.calls.append((family_id, success_url, cancel_url))
        return "https://checkout.stripe.com/c/pay/cs_test_fake"

    async def create_portal(self, customer_ref: str, return_url: str) -> str:
        if self.fail:
            raise self.fail
        self.portal_calls.append((customer_ref, return_url))
        return "https://billing.stripe.com/p/session/test_fake"

    def parse_event(self, payload: bytes, signature: str | None) -> Any:
        return self._real.parse_event(payload, signature)


@pytest.fixture
def settings() -> Settings:
    return Settings()


@pytest.fixture
def checkout(live_client: TestClient, settings: Settings) -> Iterator[FakeCheckout]:
    fake = FakeCheckout(build_payment_provider(settings))  # type: ignore[arg-type]
    live_client.app.dependency_overrides[get_payment_provider] = lambda: fake  # type: ignore[attr-defined]
    yield fake
    live_client.app.dependency_overrides.clear()  # type: ignore[attr-defined]


@pytest.fixture
def stripe(live_client: TestClient) -> TestClient:
    """The same client: a second TestClient would run the app on another event loop. Webhook
    requests blank the CSRF header, like Stripe, which cannot send it."""
    return live_client


def send(stripe: TestClient, settings: Settings, event: dict[str, Any]) -> Any:
    assert settings.stripe_webhook_secret is not None
    body, header = signed(event, settings.stripe_webhook_secret.get_secret_value())
    return stripe.post(WEBHOOK, content=body, headers=like_stripe(header))


def like_stripe(signature: str) -> dict[str, str]:
    return {"Stripe-Signature": signature, CSRF_HEADER: ""}


async def activations(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> int:
    async with sessionmaker() as session:
        return (
            await session.scalar(
                select(func.count())
                .select_from(OutboxRow)
                .where(
                    OutboxRow.family_id == family_id, OutboxRow.topic == SubscriptionActivated.topic
                )
            )
            or 0
        )


async def rows(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> list[tuple[str, str]]:
    async with sessionmaker() as session:
        found = await session.execute(
            select(SubscriptionRow.provider_ref, SubscriptionRow.status).where(
                SubscriptionRow.family_id == family_id
            )
        )
        return [tuple(row) for row in found]


def sub_id() -> str:
    return f"sub_{uuid.uuid4().hex}"


def test_checkout_gives_the_payment_page(live_client: TestClient, checkout: FakeCheckout) -> None:
    family_id, _ = create_family(live_client)

    response = live_client.post("/api/v1/billing/checkout")

    assert response.status_code == 200, response.text
    assert response.json() == {"url": "https://checkout.stripe.com/c/pay/cs_test_fake"}
    assert checkout.calls[0][0] == family_id
    assert checkout.calls[0][1].endswith("/billing/success")


def test_billing_needs_a_family(live_client: TestClient, checkout: FakeCheckout) -> None:
    live_client.cookies.delete(FAMILY_COOKIE)
    for response in (
        live_client.post("/api/v1/billing/checkout"),
        live_client.get("/api/v1/billing/subscription"),
    ):
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "family.no_session"


async def test_a_paid_subscription_opens_the_next_cases(
    live_client: TestClient,
    checkout: FakeCheckout,
    stripe: TestClient,
    settings: Settings,
    sessionmaker: Sessionmaker,
) -> None:
    family_id, _ = create_family(live_client)
    access = build_billing_access(sessionmaker, settings)
    family = FamilyRef(family_id)
    assert live_client.get("/api/v1/billing/subscription").json() == {
        "status": None,
        "active": False,
        "cancels_at": None,
    }
    assert await access.has_access(family, 1)
    with pytest.raises(PaymentRequiredError):
        await access.require_access(family, 2)

    response = send(
        stripe, settings, subscription_event(family_id, "active", subscription_id=sub_id())
    )

    assert response.status_code == 200, response.text
    assert live_client.get("/api/v1/billing/subscription").json() == {
        "status": "active",
        "active": True,
        "cancels_at": None,
    }
    assert await access.has_access(family, 2)
    assert await activations(sessionmaker, family_id) == 1
    already = live_client.post("/api/v1/billing/checkout")
    assert already.status_code == 409
    assert already.json()["error"]["code"] == "billing.already_subscribed"


async def test_the_same_event_twice_counts_once(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    event = subscription_event(family_id, "active", subscription_id=sub_id())

    assert send(stripe, settings, event).status_code == 200
    assert send(stripe, settings, event).status_code == 200

    assert len(await rows(sessionmaker, family_id)) == 1
    assert await activations(sessionmaker, family_id) == 1


async def test_an_older_event_does_not_bring_back_a_cancelled_subscription(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    ref, now = sub_id(), int(time.time())

    # Stripe delivered the cancel before the older "active".
    send(
        stripe,
        settings,
        subscription_event(family_id, "canceled", subscription_id=ref, created=now),
    )
    send(
        stripe,
        settings,
        subscription_event(family_id, "active", subscription_id=ref, created=now - 60),
    )

    assert await rows(sessionmaker, family_id) == [(ref, "canceled")]
    assert await activations(sessionmaker, family_id) == 0
    assert not await build_billing_access(sessionmaker, settings).has_access(
        FamilyRef(family_id), 2
    )


async def test_cancelling_closes_the_paid_cases(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    ref, now = sub_id(), int(time.time())
    send(
        stripe, settings, subscription_event(family_id, "active", subscription_id=ref, created=now)
    )

    send(
        stripe,
        settings,
        subscription_event(
            family_id, "canceled", subscription_id=ref, created=now + 1,
            event_type="customer.subscription.deleted",
        ),
    )  # fmt: skip

    assert live_client.get("/api/v1/billing/subscription").json() == {
        "status": "canceled",
        "active": False,
        "cancels_at": None,
    }
    assert not await build_billing_access(sessionmaker, settings).has_access(
        FamilyRef(family_id), 2
    )


async def test_one_family_pays_only_for_itself(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    payer_id, _ = create_family(live_client)
    other_id, _ = create_family(live_client)

    send(stripe, settings, subscription_event(payer_id, "active", subscription_id=sub_id()))

    assert live_client.get("/api/v1/billing/subscription").json()["active"] is False
    assert not await build_billing_access(sessionmaker, settings).has_access(FamilyRef(other_id), 2)


def test_a_wrong_signature_gives_400(stripe: TestClient, live_client: TestClient) -> None:
    family_id, _ = create_family(live_client)
    body, header = signed(subscription_event(family_id, "active"), "whsec_not_ours")

    response = stripe.post(WEBHOOK, content=body, headers=like_stripe(header))

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "billing.bad_signature"


def test_events_we_do_not_use_get_200(
    stripe: TestClient, live_client: TestClient, settings: Settings
) -> None:
    family_id, _ = create_family(live_client)
    event = subscription_event(family_id, "active", event_type="invoice.paid")

    assert send(stripe, settings, event).json() == {"received": True}


async def test_a_renewal_does_not_activate_again(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    ref, now = sub_id(), int(time.time())
    send(
        stripe, settings, subscription_event(family_id, "active", subscription_id=ref, created=now)
    )

    # Next month Stripe renews the subscription: still active.
    send(
        stripe,
        settings,
        subscription_event(family_id, "active", subscription_id=ref, created=now + 9),
    )

    assert await activations(sessionmaker, family_id) == 1


async def test_paying_after_a_failed_payment_activates_again(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    ref, now = sub_id(), int(time.time())
    for offset, status in ((0, "active"), (1, "past_due"), (2, "active")):
        event = subscription_event(family_id, status, subscription_id=ref, created=now + offset)
        send(stripe, settings, event)

    assert await activations(sessionmaker, family_id) == 2


async def test_an_event_for_an_unknown_family_gets_200_and_changes_nothing(
    stripe: TestClient,
    live_client: TestClient,
    settings: Settings,
    sessionmaker: Sessionmaker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    stranger = uuid.uuid4()
    event = subscription_event(stranger, "active", subscription_id=sub_id())

    response = send(stripe, settings, event)

    assert response.status_code == 200, response.text
    assert response.json() == {"received": True}
    assert await rows(sessionmaker, stranger) == []
    assert f"{event['id']} of type {event['type']}" in caplog.text
    assert "cus_test" not in caplog.text

    # Retried by Stripe: the same answer.
    assert send(stripe, settings, event).status_code == 200


def test_an_event_with_a_family_that_is_no_id_gets_200(
    stripe: TestClient, settings: Settings
) -> None:
    event = subscription_event(uuid.uuid4(), "active")
    event["data"]["object"]["metadata"]["family_id"] = "not-an-id"

    assert send(stripe, settings, event).status_code == 200


def test_a_subscribed_family_gets_the_portal(
    live_client: TestClient, checkout: FakeCheckout, stripe: TestClient, settings: Settings
) -> None:
    family_id, _ = create_family(live_client)
    send(
        stripe,
        settings,
        subscription_event(family_id, "active", subscription_id=sub_id(), customer="cus_mine"),
    )

    response = live_client.post("/api/v1/billing/portal")

    assert response.status_code == 200, response.text
    assert response.json() == {"url": "https://billing.stripe.com/p/session/test_fake"}
    assert checkout.portal_calls == [("cus_mine", f"{settings.web_app_url.rstrip('/')}/family")]


def test_a_family_with_no_subscription_gets_409_from_the_portal(
    live_client: TestClient, checkout: FakeCheckout, stripe: TestClient, settings: Settings
) -> None:
    family_id, _ = create_family(live_client)
    # A cancelled subscription gives no access, so there is nothing to manage.
    send(stripe, settings, subscription_event(family_id, "canceled", subscription_id=sub_id()))

    cancelled = live_client.post("/api/v1/billing/portal")
    assert cancelled.status_code == 409
    assert cancelled.json()["error"]["code"] == "billing.no_subscription"

    create_family(live_client)
    never = live_client.post("/api/v1/billing/portal")
    assert never.status_code == 409
    assert never.json()["error"]["code"] == "billing.no_subscription"
    assert checkout.portal_calls == []


def test_the_portal_needs_a_family(live_client: TestClient, checkout: FakeCheckout) -> None:
    live_client.cookies.delete(FAMILY_COOKIE)

    response = live_client.post("/api/v1/billing/portal")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "family.no_session"


def test_one_family_never_opens_the_portal_of_another(
    live_client: TestClient, checkout: FakeCheckout, stripe: TestClient, settings: Settings
) -> None:
    payer_id, payer_cookie = create_family(live_client)
    send(
        stripe,
        settings,
        subscription_event(payer_id, "active", subscription_id=sub_id(), customer="cus_payer"),
    )
    create_family(live_client)

    response = live_client.post("/api/v1/billing/portal")

    assert response.status_code == 409
    assert checkout.portal_calls == []
    live_client.cookies.set(FAMILY_COOKIE, payer_cookie)
    assert live_client.post("/api/v1/billing/portal").status_code == 200
    assert [call[0] for call in checkout.portal_calls] == ["cus_payer"]


def subscribe(live_client: TestClient, stripe: TestClient, settings: Settings) -> None:
    family_id, _ = create_family(live_client)
    send(
        stripe,
        settings,
        subscription_event(family_id, "active", subscription_id=sub_id(), customer="cus_mine"),
    )


def test_a_provider_that_is_down_gives_503_on_checkout_and_portal(
    live_client: TestClient, checkout: FakeCheckout, stripe: TestClient, settings: Settings
) -> None:
    checkout.fail = BillingUnavailableError("APIConnectionError")

    create_family(live_client)
    unpaid = live_client.post("/api/v1/billing/checkout")
    subscribe(live_client, stripe, settings)
    paid = live_client.post("/api/v1/billing/portal")

    for response in (unpaid, paid):
        assert response.status_code == 503, response.text
        assert response.json()["error"]["code"] == "billing.unavailable"


def test_without_stripe_keys_checkout_and_portal_give_503(
    live_client: TestClient, checkout: FakeCheckout, stripe: TestClient, settings: Settings
) -> None:
    subscribe(live_client, stripe, settings)  # the webhook still needs the real parser
    unconfigured = StripeProvider(None, None, 799, "usd")
    live_client.app.dependency_overrides[get_payment_provider] = lambda: unconfigured  # type: ignore[attr-defined]
    portal = live_client.post("/api/v1/billing/portal")
    create_family(live_client)
    checkout_page = live_client.post("/api/v1/billing/checkout")

    for response in (checkout_page, portal):
        assert response.status_code == 503, response.text
        assert response.json()["error"]["code"] == "billing.not_configured"


async def test_canceling_at_period_end_keeps_access_and_shows_the_end(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    ref, now = sub_id(), int(time.time())
    end = now + 20 * 86400
    send(
        stripe, settings, subscription_event(family_id, "active", subscription_id=ref, created=now)
    )
    assert live_client.get("/api/v1/billing/subscription").json()["cancels_at"] is None

    send(
        stripe,
        settings,
        subscription_event(
            family_id, "active", subscription_id=ref, created=now + 1,
            cancel_at_period_end=True, cancel_at=end,
        ),
    )  # fmt: skip

    body = live_client.get("/api/v1/billing/subscription").json()
    assert body["status"] == "active"
    assert body["active"] is True
    assert datetime.fromisoformat(body["cancels_at"]) == datetime.fromtimestamp(end, UTC)
    assert await build_billing_access(sessionmaker, settings).has_access(FamilyRef(family_id), 2)

    send(
        stripe,
        settings,
        subscription_event(family_id, "active", subscription_id=ref, created=now + 2),
    )

    body = live_client.get("/api/v1/billing/subscription").json()
    assert body == {"status": "active", "active": True, "cancels_at": None}


async def test_the_end_of_a_canceled_subscription_ends_access(
    live_client: TestClient, stripe: TestClient, settings: Settings, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    ref, now = sub_id(), int(time.time())
    send(
        stripe,
        settings,
        subscription_event(
            family_id, "active", subscription_id=ref, created=now,
            cancel_at_period_end=True, cancel_at=now + 60,
        ),
    )  # fmt: skip

    send(
        stripe,
        settings,
        subscription_event(
            family_id, "canceled", subscription_id=ref, created=now + 1,
            event_type="customer.subscription.deleted",
            cancel_at_period_end=True, cancel_at=now + 60,
        ),
    )  # fmt: skip

    assert live_client.get("/api/v1/billing/subscription").json() == {
        "status": "canceled",
        "active": False,
        "cancels_at": None,
    }
    assert not await build_billing_access(sessionmaker, settings).has_access(
        FamilyRef(family_id), 2
    )
