from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.billing.domain import ACCESS_STATUSES, Subscription, SubscriptionStatus
from jumbaq.billing.models import PaymentEventRow, SubscriptionRow
from jumbaq.core.family import FamilyRef


class SqlSubscriptionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def statuses(self, family: FamilyRef) -> list[SubscriptionStatus]:
        rows = await self._session.scalars(
            select(SubscriptionRow.status).where(SubscriptionRow.family_id == family.family_id)
        )
        return [SubscriptionStatus(status) for status in rows]

    async def latest_with_access(self, family: FamilyRef) -> Subscription | None:
        row = (
            await self._session.execute(
                select(
                    SubscriptionRow.provider_ref,
                    SubscriptionRow.customer_ref,
                    SubscriptionRow.status,
                    SubscriptionRow.changed_at,
                    SubscriptionRow.cancels_at,
                )
                .where(
                    SubscriptionRow.family_id == family.family_id,
                    SubscriptionRow.status.in_(ACCESS_STATUSES),
                )
                .order_by(SubscriptionRow.changed_at.desc())
                .limit(1)
            )
        ).first()
        if row is None:
            return None
        return Subscription(
            family.family_id,
            row.provider_ref,
            row.customer_ref,
            SubscriptionStatus(row.status),
            row.changed_at,
            row.cancels_at,
        )

    async def get_for_update(self, family: FamilyRef, provider_ref: str) -> Subscription | None:
        row = (
            await self._session.execute(
                select(
                    SubscriptionRow.customer_ref,
                    SubscriptionRow.status,
                    SubscriptionRow.changed_at,
                    SubscriptionRow.cancels_at,
                )
                .where(
                    SubscriptionRow.family_id == family.family_id,
                    SubscriptionRow.provider_ref == provider_ref,
                )
                .with_for_update()
            )
        ).first()
        if row is None:
            return None
        return Subscription(
            family.family_id,
            provider_ref,
            row.customer_ref,
            SubscriptionStatus(row.status),
            row.changed_at,
            row.cancels_at,
        )

    async def add(self, subscription: Subscription, created_at: datetime) -> None:
        await self._session.execute(
            insert(SubscriptionRow).values(
                family_id=subscription.family_id,
                provider_ref=subscription.provider_ref,
                customer_ref=subscription.customer_ref,
                status=subscription.status,
                changed_at=subscription.changed_at,
                cancels_at=subscription.cancels_at,
                created_at=created_at,
            )
        )

    async def set_status(
        self,
        family: FamilyRef,
        provider_ref: str,
        status: SubscriptionStatus,
        changed_at: datetime,
        cancels_at: datetime | None,
    ) -> None:
        await self._session.execute(
            update(SubscriptionRow)
            .where(
                SubscriptionRow.family_id == family.family_id,
                SubscriptionRow.provider_ref == provider_ref,
            )
            .values(status=status, changed_at=changed_at, cancels_at=cancels_at)
        )

    async def remember_event(
        self, family: FamilyRef, provider_event_id: str, received_at: datetime
    ) -> bool:
        added = await self._session.scalar(
            pg_insert(PaymentEventRow)
            .values(
                family_id=family.family_id,
                provider_event_id=provider_event_id,
                received_at=received_at,
            )
            .on_conflict_do_nothing(index_elements=["provider_event_id"])
            .returning(PaymentEventRow.id)
        )
        return added is not None
