import logging
from typing import Any

from jumbaq.core.outbox import OutboxDelivery

logger = logging.getLogger(__name__)


async def ping(ctx: dict[str, Any]) -> str:
    """Test task: shows that the API can enqueue jobs and the worker runs them."""
    logger.info("ping, try %s", ctx.get("job_try"))
    return "pong"


async def deliver_outbox(ctx: dict[str, Any]) -> int:
    """After a nudge, and every 5 seconds for what a nudge missed."""
    delivery: OutboxDelivery = ctx["outbox"]
    return await delivery.deliver_due()
