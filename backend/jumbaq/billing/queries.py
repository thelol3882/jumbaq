"""Read-only views for screens."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.billing.domain import ACCESS_STATUSES, SubscriptionStatus
from jumbaq.billing.models import SubscriptionRow


@dataclass(frozen=True)
class SubscriptionView:
    status: SubscriptionStatus | None
    active: bool


class BillingQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def subscription(self, family_id: uuid.UUID) -> SubscriptionView:
        """The subscription that gives access if there is one, else the newest."""
        status = await self._session.scalar(
            select(SubscriptionRow.status)
            .where(SubscriptionRow.family_id == family_id)
            .order_by(
                SubscriptionRow.status.in_(list(ACCESS_STATUSES)).desc(),
                SubscriptionRow.changed_at.desc(),
            )
            .limit(1)
        )
        if status is None:
            return SubscriptionView(None, False)
        found = SubscriptionStatus(status)
        return SubscriptionView(found, found in ACCESS_STATUSES)
