"""Background worker (arq on Redis). Run with `arq jumbaq.worker.main.WorkerSettings`.

arq needs `redis_settings` on the class, so the Redis url is the only setting read at
import time. Everything else is created in `startup`, kept in `ctx` and closed in
`shutdown`, like the API lifespan.
"""

import logging
import os
from typing import Any, ClassVar

from arq import cron, func
from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.core.config import Settings
from jumbaq.core.db import create_engine, create_sessionmaker
from jumbaq.core.events import Event
from jumbaq.core.logging import setup_logging
from jumbaq.core.outbox import Handler, OutboxDelivery
from jumbaq.core.tasks import DELIVER_OUTBOX
from jumbaq.worker.tasks import deliver_outbox, ping

logger = logging.getLogger(__name__)


def build_handlers(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> dict[type[Event], list[Handler]]:
    """Which handlers run for which event. Handlers come from the `handlers.py` of each module."""
    return {}


async def startup(ctx: dict[str, Any]) -> None:
    settings = Settings()
    setup_logging(settings.log_level)
    ctx["settings"] = settings
    ctx["engine"] = create_engine(settings.database_url)
    ctx["sessionmaker"] = create_sessionmaker(ctx["engine"])
    ctx["outbox"] = OutboxDelivery(ctx["sessionmaker"], build_handlers(ctx["sessionmaker"]))
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
