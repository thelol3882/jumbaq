"""Read-only views for screens."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.billing.domain import ACCESS_STATUSES, SubscriptionStatus
from jumbaq.billing.models import SubscriptionRow


@dataclass(frozen=True)
class SubscriptionView:
    status: SubscriptionStatus | None
    active: bool
    # Only while active: the day the paid period ends after a cancel.
    cancels_at: datetime | None = None


class BillingQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def subscription(self, family_id: uuid.UUID) -> SubscriptionView:
        """The subscription that gives access if there is one, else the newest."""
        row = (
            await self._session.execute(
                select(SubscriptionRow.status, SubscriptionRow.cancels_at)
                .where(SubscriptionRow.family_id == family_id)
                .order_by(
                    SubscriptionRow.status.in_(list(ACCESS_STATUSES)).desc(),
                    SubscriptionRow.changed_at.desc(),
                )
                .limit(1)
            )
        ).first()
        if row is None:
            return SubscriptionView(None, False)
        found = SubscriptionStatus(row.status)
        active = found in ACCESS_STATUSES
        return SubscriptionView(found, active, row.cancels_at if active else None)
