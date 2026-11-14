import asyncio
import logging
from collections.abc import Awaitable

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from jumbaq.core.deps import EngineDep, RedisDep

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)

CHECK_TIMEOUT_SECONDS = 2


@router.get("/health")
async def health() -> dict[str, str]:
    """The process is up. Used by Docker."""
    return {"status": "ok"}


@router.get("/health/ready")
async def ready(engine: EngineDep, redis: RedisDep) -> JSONResponse:
    """PostgreSQL and Redis answer, so the API can serve requests."""
    database, redis_check = await asyncio.gather(
        _run_check(_check_database(engine), "database"),
        _run_check(_check_redis(redis), "redis"),
    )
    checks = {"database": database, "redis": redis_check}
    ok = all(result == "ok" for result in checks.values())
    return JSONResponse(
        {"status": "ok" if ok else "unavailable", "checks": checks},
        status_code=200 if ok else 503,
    )


async def _check_database(engine: AsyncEngine) -> None:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))


async def _check_redis(redis: Redis) -> None:
    await redis.ping()


async def _run_check(check: Awaitable[None], name: str) -> str:
    try:
        await asyncio.wait_for(check, timeout=CHECK_TIMEOUT_SECONDS)
    except Exception as exc:
        logger.warning("ready check %s failed: %r", name, exc)
        return "fail"
    return "ok"
