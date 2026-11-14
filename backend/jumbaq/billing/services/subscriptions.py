"""The monthly subscription: the payment page, the provider's webhook and the status."""

import logging

from jumbaq.billing import domain
from jumbaq.billing.domain import Subscription, SubscriptionChange
from jumbaq.billing.errors import AlreadySubscribedError, NoSubscriptionError
from jumbaq.billing.events import SubscriptionActivated
from jumbaq.billing.providers.base import PaymentProvider
from jumbaq.billing.queries import SubscriptionView
from jumbaq.billing.uow import BillingUoWFactory
from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef

logger = logging.getLogger(__name__)


class SubscriptionService:
    def __init__(
        self, uow: BillingUoWFactory, provider: PaymentProvider, clock: Clock, web_app_url: str
    ) -> None:
        self._uow = uow
        self._provider = provider
        self._clock = clock
        self._web_app_url = web_app_url.rstrip("/")

    async def start_checkout(self, family: FamilyRef) -> str:
        async with self._uow() as uow:
            statuses = await uow.subscriptions.statuses(family)
        if any(domain.gives_access(status) for status in statuses):
            raise AlreadySubscribedError()
        # Outside the transaction: the provider call can take seconds.
        return await self._provider.create_checkout(
            family.family_id,
            success_url=f"{self._web_app_url}/billing/success",
            cancel_url=f"{self._web_app_url}/billing/cancel",
        )

    async def open_portal(self, family: FamilyRef) -> str:
        async with self._uow() as uow:
            subscription = await uow.subscriptions.latest_with_access(family)
        if subscription is None:
            raise NoSubscriptionError()
        # Outside the transaction: the provider call can take seconds.
        return await self._provider.create_portal(
            subscription.customer_ref, return_url=f"{self._web_app_url}/family"
        )

    async def receive_webhook(self, payload: bytes, signature: str | None) -> None:
        """Safe to run twice and in any order: each event counts once, and an older event never
        undoes a newer one."""
        change = self._provider.parse_event(payload, signature)
        if change is None:
            return
        # The family comes from the signed event, which our checkout filled.
        family = FamilyRef(change.family_id)
        async with self._uow() as uow:
            if await uow.families.get(family) is None:
                # Answered 200: an error would make Stripe send the event again for days.
                logger.warning(
                    "Stripe event %s of type %s names an unknown family, ignored",
                    change.event_id,
                    change.event_type,
                )
                return
            if not await uow.subscriptions.remember_event(
                family, change.event_id, self._clock.now()
            ):
                return
            stored = await uow.subscriptions.get_for_update(family, change.provider_ref)
            if stored is None:
                # Two first events for one subscription at once: one insert fails on the unique
                # provider_ref, the webhook answers 500 and Stripe sends that event again.
                await uow.subscriptions.add(_subscription(change), self._clock.now())
                activated = domain.gives_access(change.status)
            elif domain.is_newer(stored, change):
                await uow.subscriptions.set_status(
                    family, change.provider_ref, change.status, change.changed_at, change.cancels_at
                )
                activated = domain.gives_access(change.status) and not domain.gives_access(
                    stored.status
                )
            else:
                activated = False
            if activated:
                await uow.publish(SubscriptionActivated(family.family_id))
            await uow.commit()

    async def get(self, family: FamilyRef) -> SubscriptionView:
        async with self._uow() as uow:
            return await uow.queries.subscription(family.family_id)


def _subscription(change: SubscriptionChange) -> Subscription:
    return Subscription(
        family_id=change.family_id,
        provider_ref=change.provider_ref,
        customer_ref=change.customer_ref,
        status=change.status,
        changed_at=change.changed_at,
        cancels_at=change.cancels_at,
    )
