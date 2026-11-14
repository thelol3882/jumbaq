"""What a family does with an episode: read it, answer the riddle, swap the riddle and, in demo
mode, open it at once."""

import uuid
from typing import NoReturn

from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef
from jumbaq.episodes.uow import EpisodesUoWFactory


class EpisodeService:
    def __init__(self, uow: EpisodesUoWFactory, clock: Clock, demo_mode: bool) -> None:
        self._uow = uow
        self._clock = clock
        self._demo_mode = demo_mode

    async def current(self, family: FamilyRef) -> NoReturn:
        raise NotImplementedError

    async def get(self, family: FamilyRef, episode_id: uuid.UUID) -> NoReturn:
        raise NotImplementedError

    async def answer(self, family: FamilyRef, episode_id: uuid.UUID, answer: str) -> NoReturn:
        raise NotImplementedError

    async def swap(self, family: FamilyRef, episode_id: uuid.UUID) -> NoReturn:
        raise NotImplementedError

    async def open_now(self, family: FamilyRef, episode_id: uuid.UUID) -> NoReturn:
        raise NotImplementedError
