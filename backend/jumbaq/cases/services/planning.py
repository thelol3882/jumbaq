"""Opening a case and planning it with the model. Both run in the worker, from events."""

import logging
import uuid
from dataclasses import replace

from jumbaq.ai.public import (
    EPISODES_PER_CASE,
    SUSPECTS_PER_CASE,
    AiBadOutputError,
    AiDailyLimitError,
    CaseDraft,
    CasePlanInput,
    HomeInput,
    KidInput,
    StoryWriter,
)
from jumbaq.cases import domain
from jumbaq.cases.domain import FIRST_CASE, CaseStatus, Clue, Plan, Suspect
from jumbaq.cases.events import CaseOpened, CasePlanned
from jumbaq.cases.uow import CasesUoWFactory
from jumbaq.core.family import FamilyRef
from jumbaq.families.public import Family

logger = logging.getLogger(__name__)

# The first answer and one more: a third call rarely helps and keeps the family waiting.
PLAN_TRIES = 2


class CasePlanning:
    def __init__(self, uow: CasesUoWFactory, writer: StoryWriter) -> None:
        self._uow = uow
        self._writer = writer

    async def open_first(self, family: FamilyRef) -> None:
        """Safe to run twice: a family that has case 1 keeps it, and the event goes out once."""
        async with self._uow() as uow:
            case_id = await uow.cases.add_if_missing(family, FIRST_CASE, CaseStatus.PLANNING)
            if case_id is not None:
                await uow.publish(CaseOpened(family.family_id, case_id))
            await uow.commit()

    async def plan(self, family: FamilyRef, case_id: uuid.UUID) -> None:
        """Safe to run twice: a case that is not in planning is left alone.

        AiUnavailableError goes up, so the outbox tries again later.
        """
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id)
            home = await uow.families.get(family)
        if case is None or home is None or case.status != CaseStatus.PLANNING:
            return

        # No unit of work is open here: the model call can take a while.
        try:
            task = CasePlanInput(_home(home), case.number, clue_max_chars=domain.CLUE_MAX_CHARS)
            plan = await self._ask(family, task)
        except AiDailyLimitError:
            logger.warning("case %s not planned: the family reached the daily cap", case_id)
            await self._fail(family, case_id)
            return
        await self._save(family, case_id, plan)

    async def _ask(self, family: FamilyRef, task: CasePlanInput) -> Plan | None:
        """A valid plan from the model, or None after PLAN_TRIES bad ones."""
        for attempt in range(1, PLAN_TRIES + 1):
            try:
                plan = _plan(await self._writer.plan_case(family, task))
            except AiBadOutputError:
                logger.info("plan of the wrong shape, try %s", attempt)
                continue
            problems = domain.plan_problems(plan, SUSPECTS_PER_CASE, EPISODES_PER_CASE)
            if not problems:
                return plan
            logger.info("plan breaks the rules (%s), try %s", "; ".join(problems), attempt)
            task = replace(task, fix=tuple(problems))
        return None

    async def _save(self, family: FamilyRef, case_id: uuid.UUID, plan: Plan | None) -> None:
        """The model's plan, or the built-in one after bad answers. Then the case is active."""
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id, for_update=True)
            # Another delivery of the same event may have finished first.
            if case is None or case.status != CaseStatus.PLANNING:
                return
            active = replace(
                case,
                status=CaseStatus.ACTIVE,
                plan=plan or domain.FALLBACK_PLAN,
                is_fallback=plan is None,
            )
            await uow.cases.update(active)
            await uow.publish(CasePlanned(family.family_id, case_id))
            await uow.commit()

    async def _fail(self, family: FamilyRef, case_id: uuid.UUID) -> None:
        """The daily cap: a status the web app shows, instead of an error that retries."""
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id, for_update=True)
            if case is None or not domain.can_move(case.status, CaseStatus.FAILED):
                return
            await uow.cases.update(replace(case, status=CaseStatus.FAILED))
            await uow.commit()


def _home(family: Family) -> HomeInput:
    return HomeInput(
        kids=tuple(KidInput(kid.nickname, kid.age) for kid in family.kids),
        rooms=family.rooms,
        objects=family.objects,
    )


def _plan(draft: CaseDraft) -> Plan:
    return Plan(
        title=draft.title,
        setting=draft.setting,
        suspects=tuple(Suspect(s.id, s.name, s.description) for s in draft.suspects),
        culprit_id=draft.culprit_id,
        clues=tuple(Clue(c.episode, c.text, c.suspect_id, c.points_at) for c in draft.clues),
        reveal=draft.reveal,
    )
