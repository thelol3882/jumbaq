"""What a family does with an episode: read it, answer the riddle, decode the clue, strike out
the suspect, swap the riddle and, in demo mode, open it at once."""

import uuid
from dataclasses import dataclass, replace
from datetime import datetime

from jumbaq.ai.public import ANSWER_SLOT, EPISODES_PER_CASE
from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef
from jumbaq.episodes import domain
from jumbaq.episodes.domain import CipherLevel, Episode, EpisodeStatus, EveningStep, Riddle
from jumbaq.episodes.errors import (
    DemoModeOffError,
    EpisodeNotAvailableYetError,
    EpisodeNotFoundError,
    EpisodeNotReadyError,
    EpisodeWrongStepError,
    RiddleAlreadySwappedError,
)
from jumbaq.episodes.events import EpisodePlayed, EpisodeRequested
from jumbaq.episodes.repositories.episodes import EpisodeRepository
from jumbaq.episodes.uow import EpisodesUoW, EpisodesUoWFactory


@dataclass(frozen=True)
class ResultView:
    answer: str
    resolution: str
    case_clue: str
    cliffhanger: str
    decoded_word: str | None
    revealed_suspect: bool
    struck_suspect_id: str | None
    rules_out: bool | None


@dataclass(frozen=True)
class AnsweredView:
    answer: str
    resolution: str


@dataclass(frozen=True)
class DecodeView:
    level: CipherLevel
    key: int
    start: int | None
    shift: int | None
    code: str | None
    count: int | None
    clue_with_gap: str | None
    options: list[str]
    attempts: int


@dataclass(frozen=True)
class StrikeView:
    clue: str
    points_at: bool
    attempts: int
    decoded_word: str | None
    revealed_word: bool


@dataclass(frozen=True)
class ContentView:
    recap: str
    read_aloud: tuple[str, ...]
    riddle: Riddle
    hint: str
    swapped: bool
    step: EveningStep
    answered: AnsweredView | None
    decode: DecodeView | None
    strike: StrikeView | None
    result: ResultView | None


@dataclass(frozen=True)
class EpisodeView:
    id: uuid.UUID
    case_id: uuid.UUID
    case_number: int
    number: int
    status: EpisodeStatus
    available_at: datetime | None
    content: ContentView | None


class EpisodeService:
    def __init__(
        self, uow: EpisodesUoWFactory, clock: Clock, demo_mode: bool, gap_hours: int
    ) -> None:
        self._uow = uow
        self._clock = clock
        self._demo_mode = demo_mode
        self._gap_hours = gap_hours

    async def current(self, family: FamilyRef) -> EpisodeView:
        async with self._uow() as uow:
            episode = await uow.episodes.newest(family)
            case_number = await uow.cases.current_case_number(family)
        # The newest case may have no episode yet: the one found then belongs to an older case.
        if episode is None or episode.case_number != case_number:
            raise EpisodeNotFoundError()
        return self._view(episode)

    async def get(self, family: FamilyRef, episode_id: uuid.UUID) -> EpisodeView:
        async with self._uow() as uow:
            episode = await uow.episodes.get(family, episode_id)
        if episode is None:
            raise EpisodeNotFoundError()
        return self._view(episode)

    async def answer(self, family: FamilyRef, episode_id: uuid.UUID, answer: str) -> EpisodeView:
        """Any answer fits: the template weaves it into the story with no model call. It is
        the first of three steps. An older episode without the cipher is played right here."""
        now = self._clock.now()
        async with self._uow() as uow:
            episode = await self._playable(uow.episodes, family, episode_id)
            assert episode.payload is not None
            if episode.answered_at is not None:
                raise EpisodeWrongStepError()
            cleaned = domain.clean_answer(answer)
            answered = replace(
                episode,
                answer=cleaned,
                resolution=domain.resolution(
                    episode.payload.resolution_template, cleaned, ANSWER_SLOT
                ),
                answered_at=now,
            )
            if domain.has_evening_steps(episode.payload):
                await uow.episodes.update(answered)
            else:
                answered = await self._finish(uow, family, answered, now)
            await uow.commit()
        return self._view(answered)

    async def decode(
        self, family: FamilyRef, episode_id: uuid.UUID, word: str | None
    ) -> EpisodeView:
        """Step two. A wrong pick counts; after the second the right word is given away and the
        evening goes on to the strike."""
        now = self._clock.now()
        async with self._uow() as uow:
            episode = await self._in_step(uow.episodes, family, episode_id, EveningStep.DECODE)
            assert episode.payload is not None
            secret = episode.payload.cipher_secret
            # A count level with no secret (a clue with no short word, or an older episode)
            # has no box to check: any body passes.
            if secret is None or (word is not None and domain.same_word(word, secret)):
                decoded = replace(episode, decoded_at=now)
            else:
                attempts = episode.decode_attempts + 1
                given_away = attempts >= domain.MAX_ATTEMPTS
                decoded = replace(
                    episode, decode_attempts=attempts, decoded_at=now if given_away else None
                )
            await uow.episodes.update(decoded)
            await uow.commit()
        return self._view(decoded)

    async def strike(
        self, family: FamilyRef, episode_id: uuid.UUID, suspect_id: str
    ) -> EpisodeView:
        """Step three. The evening counts as played with the right suspect, or after the second
        wrong one, when the right suspect is shown."""
        now = self._clock.now()
        async with self._uow() as uow:
            episode = await self._in_step(uow.episodes, family, episode_id, EveningStep.STRIKE)
            assert episode.payload is not None
            right = suspect_id == episode.payload.clue_suspect_id
            struck = (
                episode if right else replace(episode, strike_attempts=episode.strike_attempts + 1)
            )
            if right or struck.strike_attempts >= domain.MAX_ATTEMPTS:
                struck = await self._finish(uow, family, struck, now)
            else:
                await uow.episodes.update(struck)
            await uow.commit()
        return self._view(struck)

    async def _finish(
        self, uow: EpisodesUoW, family: FamilyRef, episode: Episode, now: datetime
    ) -> Episode:
        """The evening is played: cases counts it, and the next episode is requested and opens
        after the gap."""
        played = replace(episode, status=EpisodeStatus.PLAYED, played_at=now)
        await uow.episodes.update(played)
        await uow.publish(EpisodePlayed(family.family_id, episode.case_id, episode.number))
        if episode.number < EPISODES_PER_CASE:
            next_id = await uow.episodes.add_if_missing(
                family,
                episode.case_id,
                episode.case_number,
                episode.number + 1,
                available_at=domain.available_after(now, self._gap_hours),
                created_at=now,
            )
            if next_id is not None:
                await uow.publish(EpisodeRequested(family.family_id, next_id))
        return played

    async def swap(self, family: FamilyRef, episode_id: uuid.UUID) -> EpisodeView:
        """The second riddle, for when the object is not at hand. No model call."""
        async with self._uow() as uow:
            episode = await self._playable(uow.episodes, family, episode_id)
            # After the answer the riddle is solved: another one would not match the story.
            if episode.answered_at is not None:
                raise EpisodeWrongStepError()
            if episode.used_fallback_riddle:
                raise RiddleAlreadySwappedError()
            swapped = replace(episode, used_fallback_riddle=True)
            await uow.episodes.update(swapped)
            await uow.commit()
        return self._view(swapped)

    async def open_now(self, family: FamilyRef, episode_id: uuid.UUID) -> EpisodeView:
        """For the jury: five evenings in five minutes."""
        if not self._demo_mode:
            raise DemoModeOffError()
        async with self._uow() as uow:
            episode = await uow.episodes.get(family, episode_id, for_update=True)
            if episode is None:
                raise EpisodeNotFoundError()
            if episode.status == EpisodeStatus.PLAYED:
                raise EpisodeNotReadyError()
            opened = replace(episode, available_at=self._clock.now())
            await uow.episodes.update(opened)
            await uow.commit()
        return self._view(opened)

    async def _playable(
        self, episodes: EpisodeRepository, family: FamilyRef, episode_id: uuid.UUID
    ) -> Episode:
        """The episode, locked, when the kids can play it now."""
        episode = await episodes.get(family, episode_id, for_update=True)
        if episode is None:
            raise EpisodeNotFoundError()
        if episode.status == EpisodeStatus.PLAYED:
            raise EpisodeWrongStepError()
        if episode.status != EpisodeStatus.READY or episode.payload is None:
            raise EpisodeNotReadyError()
        if not domain.is_open(episode, self._clock.now()):
            raise EpisodeNotAvailableYetError()
        return episode

    async def _in_step(
        self,
        episodes: EpisodeRepository,
        family: FamilyRef,
        episode_id: uuid.UUID,
        step: EveningStep,
    ) -> Episode:
        """The episode, locked, when it is in the step asked for."""
        episode = await episodes.get(family, episode_id, for_update=True)
        if episode is None:
            raise EpisodeNotFoundError()
        if episode.status == EpisodeStatus.PLAYED:
            raise EpisodeWrongStepError()
        if episode.status != EpisodeStatus.READY or episode.payload is None:
            raise EpisodeNotReadyError()
        if not domain.is_open(episode, self._clock.now()):
            raise EpisodeNotAvailableYetError()
        if domain.evening_step(episode) != step:
            raise EpisodeWrongStepError()
        return episode

    def _view(self, episode: Episode) -> EpisodeView:
        """No content while the episode is written or waits for its evening."""
        return EpisodeView(
            id=episode.id,
            case_id=episode.case_id,
            case_number=episode.case_number,
            number=episode.number,
            status=episode.status,
            available_at=episode.available_at,
            content=_content(episode) if domain.is_open(episode, self._clock.now()) else None,
        )


def _content(episode: Episode) -> ContentView | None:
    if episode.payload is None or episode.riddle is None:
        return None
    payload = episode.payload
    step = domain.evening_step(episode)
    # The secret goes to the kids only once they decoded it or were shown it.
    decoded_word = payload.cipher_secret if episode.decoded_at is not None else None
    answered = None
    if episode.answered_at is not None:
        answered = AnsweredView(answer=episode.answer or "", resolution=episode.resolution or "")
    result = None
    if step == EveningStep.DONE:
        result = ResultView(
            answer=episode.answer or "",
            resolution=episode.resolution or "",
            case_clue=payload.case_clue,
            cliffhanger=payload.cliffhanger,
            decoded_word=decoded_word,
            revealed_suspect=episode.strike_attempts >= domain.MAX_ATTEMPTS,
            struck_suspect_id=payload.clue_suspect_id,
            rules_out=None if payload.clue_points_at is None else not payload.clue_points_at,
        )
    return ContentView(
        recap=payload.recap,
        read_aloud=payload.read_aloud,
        riddle=episode.riddle,
        hint=payload.hint,
        swapped=episode.used_fallback_riddle,
        step=step,
        answered=answered,
        decode=_decode(episode) if step == EveningStep.DECODE else None,
        strike=_strike(episode, decoded_word) if step == EveningStep.STRIKE else None,
        result=result,
    )


def _decode(episode: Episode) -> DecodeView | None:
    payload = episode.payload
    if payload is None or payload.cipher_level is None:
        return None
    key = domain.cipher_key(episode.answer or "")
    secret = payload.cipher_secret
    code = None
    count = None
    gap = None
    options: list[str] = []
    start = None
    shift = None
    if payload.cipher_level == CipherLevel.COUNT:
        count = domain.count_target(key)
        # The boxes keep their numbers, so they are never shuffled.
        if secret is not None:
            options = domain.count_options(secret, payload.cipher_decoys, count)
    elif secret is not None:
        if payload.cipher_level == CipherLevel.NUMBER_CODE:
            start = domain.number_start(key)
            code = domain.number_code(key, secret)
        else:
            shift = domain.shift_amount(key)
            code = domain.shift_text(key, secret)
        gap = domain.clue_with_gap(payload.case_clue, secret)
        options = domain.sorted_options(secret, payload.cipher_decoys)
    return DecodeView(
        level=payload.cipher_level,
        key=key,
        start=start,
        shift=shift,
        code=code,
        count=count,
        clue_with_gap=gap,
        options=options,
        attempts=episode.decode_attempts,
    )


def _strike(episode: Episode, decoded_word: str | None) -> StrikeView | None:
    payload = episode.payload
    if payload is None:
        return None
    return StrikeView(
        clue=payload.case_clue,
        points_at=bool(payload.clue_points_at),
        attempts=episode.strike_attempts,
        decoded_word=decoded_word,
        revealed_word=episode.decode_attempts >= domain.MAX_ATTEMPTS,
    )
