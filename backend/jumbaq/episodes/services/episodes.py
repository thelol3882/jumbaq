"""What a family does with an episode: read it, answer the riddle, swap the riddle and, in demo
mode, open it at once."""

import uuid
from dataclasses import dataclass, replace
from datetime import datetime

from jumbaq.ai.public import ANSWER_SLOT, EPISODES_PER_CASE
from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef
from jumbaq.episodes import domain
from jumbaq.episodes.domain import Episode, EpisodeStatus, Riddle
from jumbaq.episodes.errors import (
    DemoModeOffError,
    EpisodeNotAvailableYetError,
    EpisodeNotFoundError,
    EpisodeNotReadyError,
    RiddleAlreadySwappedError,
)
from jumbaq.episodes.events import EpisodePlayed, EpisodeRequested
from jumbaq.episodes.repositories.episodes import EpisodeRepository
from jumbaq.episodes.uow import EpisodesUoWFactory


@dataclass(frozen=True)
class ResultView:
    answer: str
    resolution: str
    case_clue: str
    cliffhanger: str


@dataclass(frozen=True)
class ContentView:
    recap: str
    read_aloud: tuple[str, ...]
    riddle: Riddle
    hint: str
    swapped: bool
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
        if episode is None:
            raise EpisodeNotFoundError()
        return self._view(episode)

    async def get(self, family: FamilyRef, episode_id: uuid.UUID) -> EpisodeView:
        async with self._uow() as uow:
            episode = await uow.episodes.get(family, episode_id)
        if episode is None:
            raise EpisodeNotFoundError()
        return self._view(episode)

    async def answer(self, family: FamilyRef, episode_id: uuid.UUID, answer: str) -> EpisodeView:
        """Any answer fits: the template weaves it into the story with no model call. The next
        episode is requested in the same step and opens after the gap."""
        now = self._clock.now()
        async with self._uow() as uow:
            episode = await self._playable(uow.episodes, family, episode_id)
            assert episode.payload is not None
            cleaned = domain.clean_answer(answer)
            played = replace(
                episode,
                status=EpisodeStatus.PLAYED,
                answer=cleaned,
                resolution=domain.resolution(
                    episode.payload.resolution_template, cleaned, ANSWER_SLOT
                ),
                played_at=now,
            )
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
            await uow.commit()
        return self._view(played)

    async def swap(self, family: FamilyRef, episode_id: uuid.UUID) -> EpisodeView:
        """The second riddle, for when the object is not at hand. No model call."""
        async with self._uow() as uow:
            episode = await self._playable(uow.episodes, family, episode_id)
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
        if episode.status != EpisodeStatus.READY or episode.payload is None:
            raise EpisodeNotReadyError()
        if not domain.is_open(episode, self._clock.now()):
            raise EpisodeNotAvailableYetError()
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
    result = None
    if episode.status == EpisodeStatus.PLAYED:
        result = ResultView(
            answer=episode.answer or "",
            resolution=episode.resolution or "",
            case_clue=payload.case_clue,
            cliffhanger=payload.cliffhanger,
        )
    return ContentView(
        recap=payload.recap,
        read_aloud=payload.read_aloud,
        riddle=episode.riddle,
        hint=payload.hint,
        swapped=episode.used_fallback_riddle,
        result=result,
    )
