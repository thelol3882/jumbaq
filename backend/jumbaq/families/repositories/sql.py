import uuid

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.core.family import FamilyRef
from jumbaq.families.domain import Family, Kid, NewFamily
from jumbaq.families.models import FamilyRow, KidRow


class SqlFamilyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, family: NewFamily) -> Family:
        family_id = await self._session.scalar(
            insert(FamilyRow)
            .values(
                session_token_hash=family.session_token_hash,
                rooms=list(family.rooms),
                objects=list(family.objects),
                created_at=family.created_at,
            )
            .returning(FamilyRow.id)
        )
        assert family_id is not None
        kids = await self._session.execute(
            insert(KidRow).returning(
                KidRow.id, KidRow.nickname, KidRow.age, sort_by_parameter_order=True
            ),
            [
                {"family_id": family_id, "nickname": kid.nickname, "age": kid.age}
                for kid in family.kids
            ],
        )
        return Family(
            id=family_id,
            rooms=family.rooms,
            objects=family.objects,
            kids=tuple(Kid(*row) for row in kids),
            created_at=family.created_at,
        )

    async def id_by_session(self, session_token_hash: str) -> uuid.UUID | None:
        return await self._session.scalar(
            select(FamilyRow.id).where(FamilyRow.session_token_hash == session_token_hash)
        )


class SqlFamilyLookup:
    """For other modules, on their session: the family as the setup saved it."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, family: FamilyRef) -> Family | None:
        row = await self._session.get(FamilyRow, family.family_id)
        if row is None:
            return None
        kids = await self._session.execute(
            select(KidRow.id, KidRow.nickname, KidRow.age)
            .where(KidRow.family_id == family.family_id)
            .order_by(KidRow.age, KidRow.nickname, KidRow.id)
        )
        return Family(
            id=row.id,
            rooms=tuple(row.rooms),
            objects=tuple(row.objects),
            kids=tuple(Kid(*kid) for kid in kids),
            created_at=row.created_at,
        )
