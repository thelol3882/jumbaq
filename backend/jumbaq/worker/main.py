"""Background worker (arq on Redis). Run with `arq jumbaq.worker.main.WorkerSettings`.

arq needs `redis_settings` on the class, so the Redis url is the only setting read at
import time. Everything else is created in `startup`, kept in `ctx` and closed in
`shutdown`, like the API lifespan.
"""

import logging
import os
from functools import partial
from typing import Any, ClassVar

from arq import cron, func
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.public import StoryWriter, build_story_writer
from jumbaq.billing.public import SubscriptionActivated
from jumbaq.cases.handlers import CasesHandlers
from jumbaq.cases.public import CaseOpened, CasePlanned, CaseSolved
from jumbaq.cases.services.planning import CasePlanning
from jumbaq.cases.services.progress import CaseProgress
from jumbaq.cases.uow import CasesUoW
from jumbaq.core.clock import Clock, SystemClock
from jumbaq.core.config import Settings
from jumbaq.core.db import create_engine, create_sessionmaker
from jumbaq.core.events import Event
from jumbaq.core.logging import setup_logging
from jumbaq.core.outbox import Handler, OutboxDelivery
from jumbaq.core.tasks import DELIVER_OUTBOX
from jumbaq.episodes.handlers import EpisodesHandlers
from jumbaq.episodes.public import EpisodePlayed, EpisodeRequested
from jumbaq.episodes.services.writing import EpisodeWriting
from jumbaq.episodes.uow import EpisodesUoW
from jumbaq.families.public import FamilyCreated
from jumbaq.worker.tasks import deliver_outbox, ping

logger = logging.getLogger(__name__)


def build_handlers(
    sessionmaker: async_sessionmaker[AsyncSession], writer: StoryWriter, clock: Clock
) -> dict[type[Event], list[Handler]]:
    """Which handlers run for which event. Handlers come from the `handlers.py` of each module.

    The writer is built once in `startup` and shared, like the engine.
    """
    cases_uow = partial(CasesUoW, sessionmaker)
    cases = CasesHandlers(CasePlanning(cases_uow, writer), CaseProgress(cases_uow))
    episodes = EpisodesHandlers(EpisodeWriting(partial(EpisodesUoW, sessionmaker), writer, clock))
    return {
        FamilyCreated: [cases.family_created],
        CaseOpened: [cases.case_opened],
        CasePlanned: [episodes.case_planned],
        EpisodeRequested: [episodes.episode_requested],
        EpisodePlayed: [cases.episode_played],
        # Registered without handlers, so their rows are marked processed and do not fail.
        CaseSolved: [],
        # Registered without handlers, so its rows are marked processed and do not fail.
        # cases will react to it.
        SubscriptionActivated: [],
    }


async def startup(ctx: dict[str, Any]) -> None:
    settings = Settings()
    setup_logging(settings.log_level)
    ctx["settings"] = settings
    ctx["engine"] = create_engine(settings.database_url)
    ctx["sessionmaker"] = create_sessionmaker(ctx["engine"])
    clock = SystemClock()
    writer = build_story_writer(ctx["sessionmaker"], settings, clock)
    handlers = build_handlers(ctx["sessionmaker"], writer, clock)
    ctx["outbox"] = OutboxDelivery(ctx["sessionmaker"], handlers)
    logger.info("worker started")


async def shutdown(ctx: dict[str, Any]) -> None:
    await ctx["engine"].dispose()
    logger.info("worker stopped")


class WorkerSettings:
    functions: ClassVar = [
        ping,
        func(deliver_outbox, name=DELIVER_OUTBOX, keep_result=0),
    ]
    # With more than one worker each cron job still runs once.
    cron_jobs: ClassVar = [
        cron(deliver_outbox, second=set(range(0, 60, 5)), keep_result=0),
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(os.environ["JUMBAQ_REDIS_URL"])
