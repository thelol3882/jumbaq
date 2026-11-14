"""Creating episodes and writing them with the model. Both run in the worker, from events."""

import logging
import uuid
from dataclasses import replace

from jumbaq.ai.public import (
    ANSWER_SLOT,
    EPISODES_PER_CASE,
    AiBadOutputError,
    AiDailyLimitError,
    AiDisabledError,
    ClueDraft,
    EpisodeDraft,
    EpisodeInput,
    HomeInput,
    KidInput,
    PlayedEpisode,
    RiddleDraft,
    StoryWriter,
    SuspectDraft,
    TextRules,
)
from jumbaq.cases.public import EpisodeBrief
from jumbaq.core.clock import Clock
from jumbaq.core.context import is_last_attempt
from jumbaq.core.family import FamilyRef
from jumbaq.episodes import domain
from jumbaq.episodes.domain import CipherPlan, Episode, EpisodeStatus, Payload, Riddle
from jumbaq.episodes.events import EpisodeRequested
from jumbaq.episodes.uow import EpisodesUoWFactory
from jumbaq.families.public import Family

logger = logging.getLogger(__name__)

# The first answer and one more, as for the case plan.
WRITE_TRIES = 2
_WRITABLE = {EpisodeStatus.REQUESTED, EpisodeStatus.GENERATING}


class EpisodeWriting:
    def __init__(self, uow: EpisodesUoWFactory, writer: StoryWriter, clock: Clock) -> None:
        self._uow = uow
        self._writer = writer
        self._clock = clock

    async def case_planned(self, family: FamilyRef, case_id: uuid.UUID) -> None:
        """Episode 1 is open at once. Safe to run twice: it is created and requested once."""
        async with self._uow() as uow:
            brief = await uow.cases.episode_brief(family, case_id, 1)
            if brief is None:
                return
            now = self._clock.now()
            episode_id = await uow.episodes.add_if_missing(
                family, case_id, brief.case_number, 1, available_at=now, created_at=now
            )
            if episode_id is not None:
                await uow.publish(EpisodeRequested(family.family_id, episode_id))
            await uow.commit()

    async def write(self, family: FamilyRef, episode_id: uuid.UUID) -> None:
        """Safe to run twice: a ready or played episode is left alone.

        AiUnavailableError goes up, so the outbox tries again later. On the last attempt the
        episode gets the built-in text, so it never stays in generating.
        """
        async with self._uow() as uow:
            episode = await uow.episodes.get(family, episode_id, for_update=True)
            if episode is None or episode.status not in _WRITABLE:
                return
            brief = await uow.cases.episode_brief(family, episode.case_id, episode.number)
            home = await uow.families.get(family)
            played = await uow.episodes.played(family, episode.case_id)
            earlier = await uow.episodes.earlier(family, episode.case_number, episode.number)
            if brief is None or home is None:
                return
            await uow.episodes.set_status(family, episode_id, EpisodeStatus.GENERATING)
            await uow.commit()

        # The cipher comes first: the story must not give its secret away.
        oldest = max((kid.age for kid in home.kids), default=0)
        plan = domain.plan_cipher(brief.clue.text, oldest, brief.earlier_clues)
        # No unit of work is open here: the model call can take a while.
        targets = domain.pick_targets(home.objects, earlier)
        payload, is_fallback = await self._payload(
            family, episode, brief, home, played, plan, targets
        )
        payload = domain.with_evening_steps(
            payload, brief.clue.suspect_id, brief.clue.points_at, plan
        )

        async with self._uow() as uow:
            current = await uow.episodes.get(family, episode_id, for_update=True)
            # Another delivery of the same event may have finished first.
            if current is None or current.status not in _WRITABLE:
                return
            ready = replace(
                current, status=EpisodeStatus.READY, payload=payload, is_fallback=is_fallback
            )
            await uow.episodes.update(ready)
            await uow.commit()

    async def _payload(
        self,
        family: FamilyRef,
        episode: Episode,
        brief: EpisodeBrief,
        home: Family,
        played: list[Episode],
        plan: CipherPlan,
        targets: tuple[str | None, str | None],
    ) -> tuple[Payload, bool]:
        """The model's episode, or the built-in one. The second item is True for the built-in."""
        youngest = min((kid.age for kid in home.kids), default=domain.YOUNG_AGE)
        paragraph_max, short_max = domain.text_limits(youngest)
        budget = domain.read_aloud_budget(youngest)
        rules = TextRules(
            paragraph_max,
            short_max,
            domain.BANNED_WORDS,
            budget.words_min,
            budget.words_max,
            budget.paragraphs_min,
            budget.paragraphs_max,
        )
        target, fallback = targets
        task = replace(
            _task(episode, brief, home, played),
            rules=rules,
            secret_words=domain.secret_words(plan.secret),
            target_object=target,
            fallback_object=fallback,
        )
        safe_riddle: Riddle | None = None
        for attempt in range(1, WRITE_TRIES + 1):
            try:
                draft = await self._writer.write_episode(family, task)
            except AiBadOutputError:
                logger.info("episode of the wrong shape, try %s", attempt)
                continue
            except (AiDailyLimitError, AiDisabledError):
                # A built-in episode keeps the evening going, so the case still has all five.
                logger.warning("episode %s: no model call (daily cap or switched off)", episode.id)
                break
            except Exception:
                if not is_last_attempt():
                    raise
                logger.exception("episode %s: the model failed for good, built-in", episode.id)
                break
            payload = domain.with_plan_clue(_from_draft(draft), brief.clue.text)
            problems = domain.draft_problems(
                payload,
                home.objects,
                youngest,
                ANSWER_SLOT,
                plan.secret,
                _context(brief, target, fallback),
            )
            if not problems:
                return payload, False
            logger.info("episode breaks the rules (%s), try %s", "; ".join(problems), attempt)
            await self._writer.mark_refused(family, draft.call_id)
            task = replace(task, fix=tuple(problems))
            if domain.is_safe_riddle(payload.fallback_riddle, home.objects, youngest):
                safe_riddle = payload.fallback_riddle
        built_in = domain.built_in_payload(
            brief.title,
            brief.clue.text,
            home.objects,
            episode.number,
            last=episode.number == EPISODES_PER_CASE,
            slot=ANSWER_SLOT,
            model_riddle=safe_riddle,
            youngest_age=youngest,
            target_object=target,
            fallback_object=fallback,
        )
        return built_in, True


def _context(brief: EpisodeBrief, target: str | None, fallback: str | None) -> domain.DraftContext:
    names = {suspect.id: suspect.name for suspect in brief.suspects}
    return domain.DraftContext(
        clue_text=brief.clue.text,
        clue_suspect=names.get(brief.clue.suspect_id, ""),
        suspect_names=tuple(names.values()),
        target_object=target,
        fallback_object=fallback,
    )


def _task(
    episode: Episode, brief: EpisodeBrief, home: Family, played: list[Episode]
) -> EpisodeInput:
    return EpisodeInput(
        home=HomeInput(
            kids=tuple(KidInput(kid.nickname, kid.age) for kid in home.kids),
            rooms=home.rooms,
            objects=domain.safe_objects(home.objects),
        ),
        case_title=brief.title,
        setting=brief.setting,
        suspects=tuple(SuspectDraft(s.id, s.name, s.description) for s in brief.suspects),
        number=episode.number,
        clue=ClueDraft(
            brief.clue.episode, brief.clue.text, brief.clue.suspect_id, brief.clue.points_at
        ),
        played=tuple(
            PlayedEpisode(
                e.number,
                e.riddle.target_object,
                e.answer or "",
                e.payload.cliffhanger if e.payload is not None else "",
            )
            for e in played
            if e.riddle is not None
        ),
    )


def _riddle(draft: RiddleDraft) -> Riddle:
    return Riddle(
        draft.text,
        draft.target_object,
        draft.answer_type.value,
        draft.parent_note,
        draft.hint,
        draft.resolution_template,
    )


def _from_draft(draft: EpisodeDraft) -> Payload:
    return Payload(
        recap=draft.recap,
        read_aloud=draft.read_aloud,
        riddle=_riddle(draft.riddle),
        hint=draft.hint,
        fallback_riddle=_riddle(draft.fallback_riddle),
        resolution_template=draft.resolution_template,
        case_clue=draft.case_clue,
        cliffhanger=draft.cliffhanger,
    )
