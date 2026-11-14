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

from jumbaq.ai.public import build_story_writer
from jumbaq.core.clock import SystemClock
from jumbaq.core.config import Settings
from jumbaq.core.db import create_engine, create_sessionmaker
from jumbaq.core.logging import setup_logging
from jumbaq.core.outbox import OutboxDelivery
from jumbaq.core.tasks import DELIVER_OUTBOX
from jumbaq.worker.tasks import deliver_outbox, ping
from jumbaq.worker.wiring import build_handlers

logger = logging.getLogger(__name__)


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
