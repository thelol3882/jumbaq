"""Opening a case and planning it with the model. Both run in the worker, from events."""

import logging
import uuid
from dataclasses import replace

from jumbaq.ai.public import (
    EPISODES_PER_CASE,
    SUSPECTS_PER_CASE,
    AiBadOutputError,
    AiDailyLimitError,
    AiDisabledError,
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
from jumbaq.core.context import is_last_attempt
from jumbaq.core.family import FamilyRef
from jumbaq.episodes.public import banned_words, safe_objects
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

        AiUnavailableError goes up, so the outbox tries again later. On the last attempt, and when
        the family reached the daily cap, the case gets the built-in plan, so it never stays in
        planning and never fails because of the model.
        """
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id)
            home = await uow.families.get(family)
            earlier = await uow.cases.earlier_plans(family, case_id)
        if case is None or home is None or case.status != CaseStatus.PLANNING:
            return

        # No unit of work is open here: the model call can take a while.
        try:
            world, missing_thing = domain.world_for(case_id)
            task = CasePlanInput(
                _home(home),
                case.number,
                clue_max_chars=domain.CLUE_MAX_CHARS,
                world=world,
                missing_thing=missing_thing,
                used_titles=tuple(old.title for old in earlier),
                used_suspect_names=tuple(s.name for old in earlier for s in old.suspects),
            )
            plan = await self._ask(family, task)
        except (AiDailyLimitError, AiDisabledError):
            logger.warning("case %s: daily cap or switched off, built-in plan", case_id)
            plan = None
        except Exception:
            if not is_last_attempt():
                raise
            logger.exception("case %s: the model failed for good, built-in plan", case_id)
            plan = None
        await self._save(family, case_id, plan)

    async def _ask(self, family: FamilyRef, task: CasePlanInput) -> Plan | None:
        """A valid plan from the model, or None after PLAN_TRIES bad ones."""
        for attempt in range(1, PLAN_TRIES + 1):
            try:
                draft = await self._writer.plan_case(family, task)
                plan = _plan(draft)
            except AiBadOutputError:
                logger.info("plan of the wrong shape, try %s", attempt)
                continue
            problems = domain.plan_problems(
                plan,
                SUSPECTS_PER_CASE,
                EPISODES_PER_CASE,
                banned_words,
                task.used_titles,
                task.used_suspect_names,
            )
            if not problems:
                return plan
            logger.info("plan breaks the rules (%s), try %s", "; ".join(problems), attempt)
            await self._writer.mark_refused(family, draft.call_id)
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
                plan=plan or domain.fallback_plan(case.number),
                is_fallback=plan is None,
            )
            await uow.cases.update(active)
            await uow.publish(CasePlanned(family.family_id, case_id))
            await uow.commit()


def _home(family: Family) -> HomeInput:
    return HomeInput(
        kids=tuple(KidInput(kid.nickname, kid.age) for kid in family.kids),
        rooms=family.rooms,
        objects=safe_objects(family.objects),
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
