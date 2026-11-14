"""Read-only views for screens."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.cases.domain import CaseStatus, Rank
from jumbaq.cases.models import CaseRow


@dataclass(frozen=True)
class SolvedCaseView:
    id: uuid.UUID
    number: int
    title: str
    rank: Rank
    solved_at: datetime


class CasesQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def solved(self, family_id: uuid.UUID) -> list[SolvedCaseView]:
        """The family's solved cases, newest first. Never the culprit or the reveal."""
        rows = await self._session.execute(
            select(CaseRow.id, CaseRow.number, CaseRow.title, CaseRow.rank, CaseRow.solved_at)
            .where(
                CaseRow.family_id == family_id,
                CaseRow.status == CaseStatus.SOLVED,
                CaseRow.title.is_not(None),
                CaseRow.rank.is_not(None),
                CaseRow.solved_at.is_not(None),
            )
            .order_by(CaseRow.number.desc())
        )
        return [
            SolvedCaseView(row.id, row.number, row.title, Rank(row.rank), row.solved_at)
            for row in rows
        ]
