"""Read-only views for screens."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.families.models import FamilyRow, KidRow


@dataclass(frozen=True)
class KidView:
    id: uuid.UUID
    nickname: str
    age: int


@dataclass(frozen=True)
class FamilyView:
    id: uuid.UUID
    rooms: list[str]
    objects: list[str]
    kids: list[KidView]
    created_at: datetime


class FamilyQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, family_id: uuid.UUID) -> FamilyView | None:
        """The family with its kids, the youngest first."""
        rows = (
            await self._session.execute(
                select(
                    FamilyRow.id,
                    FamilyRow.rooms,
                    FamilyRow.objects,
                    FamilyRow.created_at,
                    KidRow.id.label("kid_id"),
                    KidRow.nickname,
                    KidRow.age,
                )
                .outerjoin(KidRow, KidRow.family_id == FamilyRow.id)
                .where(FamilyRow.id == family_id)
                .order_by(KidRow.age, KidRow.nickname)
            )
        ).all()
        if not rows:
            return None
        first = rows[0]
        kids = [KidView(row.kid_id, row.nickname, row.age) for row in rows if row.kid_id]
        return FamilyView(first.id, first.rooms, first.objects, kids, first.created_at)
