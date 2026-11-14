from functools import partial
from typing import Annotated

from fastapi import Depends

from jumbaq.core.deps import ClockDep, SessionmakerDep, SettingsDep, TaskQueueDep
from jumbaq.core.outbox import nudge_worker
from jumbaq.episodes.services.episodes import EpisodeService
from jumbaq.episodes.uow import EpisodesUoW, EpisodesUoWFactory


def get_uow_factory(sessionmaker: SessionmakerDep, queue: TaskQueueDep) -> EpisodesUoWFactory:
    return partial(EpisodesUoW, sessionmaker, nudge=nudge_worker(queue))


EpisodesUoWFactoryDep = Annotated[EpisodesUoWFactory, Depends(get_uow_factory)]


def get_episode_service(
    uow: EpisodesUoWFactoryDep, clock: ClockDep, settings: SettingsDep
) -> EpisodeService:
    return EpisodeService(uow, clock, settings.demo_mode, settings.episode_gap_hours)


EpisodeServiceDep = Annotated[EpisodeService, Depends(get_episode_service)]
