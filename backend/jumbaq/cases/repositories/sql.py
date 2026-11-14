from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.cases.domain import CaseStatus
from jumbaq.cases.models import CaseRow
from jumbaq.core.family import FamilyRef


class SqlCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_if_missing(self, family: FamilyRef, number: int, status: CaseStatus) -> bool:
        added = await self._session.scalar(
            insert(CaseRow)
            .values(family_id=family.family_id, number=number, status=status)
            .on_conflict_do_nothing(index_elements=["family_id", "number"])
            .returning(CaseRow.id)
        )
        return added is not None
