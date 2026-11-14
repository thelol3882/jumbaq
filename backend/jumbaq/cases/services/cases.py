"""What a family does with its cases: read the current one, accuse, get the certificate and
start the next case."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from jumbaq.ai.public import EPISODES_PER_CASE
from jumbaq.billing.public import BillingAccess
from jumbaq.cases import domain
from jumbaq.cases.domain import Case, CaseStatus, Rank, Suspect
from jumbaq.cases.errors import (
    CaseNotAccusingError,
    CaseNotFoundError,
    CaseNotSolvedError,
    UnknownSuspectError,
)
from jumbaq.cases.events import CaseOpened, CaseSolved
from jumbaq.cases.queries import SolvedCaseView
from jumbaq.cases.uow import CasesUoWFactory
from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef
from jumbaq.episodes.public import EpisodeSlot

# Not an episode status: the case screen shows it for a slot whose episode is not requested yet.
LOCKED = "locked"


@dataclass(frozen=True)
class ClueView:
    episode: int
    text: str
    suspect_id: str
    rules_out: bool


@dataclass(frozen=True)
class EpisodeSlotView:
    number: int
    id: uuid.UUID | None
    status: str
    available_at: datetime | None


@dataclass(frozen=True)
class CaseView:
    """What a family may see of a case: never the culprit or the reveal."""

    id: uuid.UUID
    number: int
    status: CaseStatus
    title: str | None
    suspects: tuple[Suspect, ...]
    clues: tuple[ClueView, ...]
    episodes: tuple[EpisodeSlotView, ...]
    accusation_attempts: int
    rank: Rank | None


@dataclass(frozen=True)
class AccusationView:
    correct: bool
    accusation_attempts: int
    rank: Rank | None
    reveal: str | None
    culprit_id: str | None


@dataclass(frozen=True)
class CertificateView:
    case_id: uuid.UUID
    number: int
    title: str
    rank: Rank
    nicknames: tuple[str, ...]
    solved_at: datetime


class CaseService:
    def __init__(self, uow: CasesUoWFactory, clock: Clock, access: BillingAccess) -> None:
        self._uow = uow
        self._clock = clock
        self._access = access

    async def current(self, family: FamilyRef) -> CaseView:
        async with self._uow() as uow:
            case = await uow.cases.newest(family)
            slots = await uow.episodes.slots(family, case.id) if case else []
        if case is None:
            raise CaseNotFoundError()
        return _view(case, slots)

    async def start_next(self, family: FamilyRef) -> CaseView:
        async with self._uow() as uow:
            current = await uow.cases.newest(family)
        if current is None or current.status != CaseStatus.SOLVED:
            raise CaseNotSolvedError()
        number = current.number + 1
        await self._access.require_access(family, number)
        async with self._uow() as uow:
            case_id = await uow.cases.add_if_missing(family, number, CaseStatus.PLANNING)
            # A double click: the first request opened it, the second one shows it.
            if case_id is not None:
                await uow.publish(CaseOpened(family.family_id, case_id))
            case = await uow.cases.newest(family)
            await uow.commit()
        assert case is not None
        return _view(case, [])

    async def accuse(
        self, family: FamilyRef, case_id: uuid.UUID, suspect_id: str
    ) -> AccusationView:
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id, for_update=True)
            if case is None:
                raise CaseNotFoundError()
            if case.status != CaseStatus.ACCUSING or case.plan is None:
                raise CaseNotAccusingError()
            if suspect_id not in {suspect.id for suspect in case.plan.suspects}:
                raise UnknownSuspectError()
            result = domain.accuse(case, suspect_id, self._clock.now())
            await uow.cases.update(result.case)
            if result.correct:
                await uow.publish(CaseSolved(family.family_id, case_id))
            await uow.commit()
        if not result.correct:
            return AccusationView(False, result.case.accusation_attempts, None, None, None)
        return AccusationView(
            correct=True,
            accusation_attempts=result.case.accusation_attempts,
            rank=result.case.rank,
            reveal=case.plan.reveal,
            culprit_id=case.plan.culprit_id,
        )

    async def solved(self, family: FamilyRef) -> list[SolvedCaseView]:
        async with self._uow() as uow:
            return await uow.queries.solved(family.family_id)

    async def certificate(self, family: FamilyRef, case_id: uuid.UUID) -> CertificateView:
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id)
            home = await uow.families.get(family)
        if case is None or home is None:
            raise CaseNotFoundError()
        if case.status != CaseStatus.SOLVED or case.plan is None:
            raise CaseNotSolvedError()
        assert case.rank is not None and case.solved_at is not None
        return CertificateView(
            case_id=case.id,
            number=case.number,
            title=case.plan.title,
            rank=case.rank,
            nicknames=tuple(kid.nickname for kid in home.kids),
            solved_at=case.solved_at,
        )


def _view(case: Case, slots: list[EpisodeSlot]) -> CaseView:
    return CaseView(
        id=case.id,
        number=case.number,
        status=case.status,
        title=case.plan.title if case.plan else None,
        suspects=case.plan.suspects if case.plan else (),
        clues=tuple(
            ClueView(clue.episode, clue.text, clue.suspect_id, rules_out=not clue.points_at)
            for clue in domain.visible_clues(case)
        ),
        episodes=_slots(slots),
        accusation_attempts=case.accusation_attempts,
        rank=case.rank,
    )


def _slots(slots: list[EpisodeSlot]) -> tuple[EpisodeSlotView, ...]:
    """One per episode of the case. An episode not created yet is locked."""
    by_number = {slot.number: slot for slot in slots}
    views = []
    for number in range(1, EPISODES_PER_CASE + 1):
        slot = by_number.get(number)
        if slot is None:
            views.append(EpisodeSlotView(number, None, LOCKED, None))
        else:
            views.append(EpisodeSlotView(number, slot.id, slot.status.value, slot.available_at))
    return tuple(views)
