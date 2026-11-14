import uuid
from dataclasses import asdict
from typing import Any

from sqlalchemy import Select, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.cases.domain import Case, CaseStatus, Clue, EpisodeBrief, Plan, Rank, Suspect
from jumbaq.cases.models import CaseRow
from jumbaq.core.family import FamilyRef


class SqlCaseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_if_missing(
        self, family: FamilyRef, number: int, status: CaseStatus
    ) -> uuid.UUID | None:
        return await self._session.scalar(
            insert(CaseRow)
            .values(family_id=family.family_id, number=number, status=status)
            .on_conflict_do_nothing(index_elements=["family_id", "number"])
            .returning(CaseRow.id)
        )

    async def get(
        self, family: FamilyRef, case_id: uuid.UUID, *, for_update: bool = False
    ) -> Case | None:
        query = select(CaseRow).where(CaseRow.family_id == family.family_id, CaseRow.id == case_id)
        return await self._one(query.with_for_update() if for_update else query)

    async def newest(self, family: FamilyRef) -> Case | None:
        return await self._one(
            select(CaseRow)
            .where(CaseRow.family_id == family.family_id)
            .order_by(CaseRow.number.desc())
            .limit(1)
        )

    async def earlier_plans(self, family: FamilyRef, case_id: uuid.UUID) -> list[Plan]:
        rows = await self._session.scalars(
            select(CaseRow.plan)
            .where(
                CaseRow.family_id == family.family_id,
                CaseRow.id != case_id,
                CaseRow.plan.is_not(None),
            )
            .order_by(CaseRow.number)
        )
        return [_plan(data) for data in rows]

    async def update(self, case: Case) -> None:
        await self._session.execute(
            update(CaseRow)
            .where(CaseRow.family_id == case.family_id, CaseRow.id == case.id)
            .values(
                status=case.status,
                title=case.plan.title if case.plan else None,
                plan=asdict(case.plan) if case.plan else None,
                is_fallback=case.is_fallback,
                played_episodes=case.played_episodes,
                accusation_attempts=case.accusation_attempts,
                rank=case.rank,
                solved_at=case.solved_at,
            )
        )

    async def _one(self, query: Select[tuple[CaseRow]]) -> Case | None:
        row = await self._session.scalar(query)
        return _case(row) if row else None


class SqlCaseLookup:
    """For other modules, on their session: what an episode of a case needs."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def episode_brief(
        self, family: FamilyRef, case_id: uuid.UUID, episode: int
    ) -> EpisodeBrief | None:
        """None when the case is not this family's, not planned yet, or has no such episode."""
        row = await self._session.scalar(
            select(CaseRow).where(CaseRow.family_id == family.family_id, CaseRow.id == case_id)
        )
        if row is None or row.plan is None:
            return None
        plan = _plan(row.plan)
        clue = next((clue for clue in plan.clues if clue.episode == episode), None)
        if clue is None:
            return None
        earlier = tuple(other.text for other in plan.clues if other.episode < episode)
        return EpisodeBrief(
            row.id, row.number, plan.title, plan.setting, plan.suspects, clue, earlier
        )

    async def current_case_number(self, family: FamilyRef) -> int | None:
        """The number of the family's newest case, None before the first one."""
        return await self._session.scalar(
            select(func.max(CaseRow.number)).where(CaseRow.family_id == family.family_id)
        )


def _case(row: CaseRow) -> Case:
    return Case(
        id=row.id,
        family_id=row.family_id,
        number=row.number,
        status=CaseStatus(row.status),
        plan=_plan(row.plan) if row.plan else None,
        is_fallback=row.is_fallback,
        played_episodes=row.played_episodes,
        accusation_attempts=row.accusation_attempts,
        rank=Rank(row.rank) if row.rank else None,
        solved_at=row.solved_at,
    )


def _plan(data: dict[str, Any]) -> Plan:
    return Plan(
        title=data["title"],
        setting=data["setting"],
        suspects=tuple(Suspect(**suspect) for suspect in data["suspects"]),
        culprit_id=data["culprit_id"],
        clues=tuple(Clue(**clue) for clue in data["clues"]),
        reveal=data["reveal"],
    )
