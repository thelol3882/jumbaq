"""What the services of billing need from storage."""

from datetime import datetime
from typing import Protocol

from jumbaq.billing.domain import Subscription, SubscriptionStatus
from jumbaq.core.family import FamilyRef


class SubscriptionRepository(Protocol):
    async def statuses(self, family: FamilyRef) -> list[SubscriptionStatus]: ...

    async def get_for_update(self, family: FamilyRef, provider_ref: str) -> Subscription | None:
        """Locks the row, so two webhook events for one subscription run one after another."""
        ...

    async def add(self, subscription: Subscription, created_at: datetime) -> None: ...

    async def set_status(
        self,
        family: FamilyRef,
        provider_ref: str,
        status: SubscriptionStatus,
        changed_at: datetime,
    ) -> None: ...

    async def remember_event(
        self, family: FamilyRef, provider_event_id: str, received_at: datetime
    ) -> bool:
        """False when the event was handled before."""
        ...
