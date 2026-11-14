"""Shared FastAPI dependencies. Endpoints use these and never read app.state directly.

Tests replace them with app.dependency_overrides.
"""

from typing import Annotated

from arq.connections import ArqRedis
from fastapi import Depends, Request
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from jumbaq.core.clock import Clock, SystemClock
from jumbaq.core.config import Settings
from jumbaq.core.tasks import TaskQueue


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_engine(request: Request) -> AsyncEngine:
    return request.app.state.engine


def get_sessionmaker(request: Request) -> async_sessionmaker[AsyncSession]:
    """Services open sessions only through UnitOfWork."""
    return request.app.state.sessionmaker


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_clock(request: Request) -> Clock:
    # Unit tests run without the lifespan, so the attribute may be missing.
    return getattr(request.app.state, "clock", None) or SystemClock()


def get_task_queue(request: Request) -> TaskQueue:
    redis: ArqRedis = request.app.state.redis
    return redis


SettingsDep = Annotated[Settings, Depends(get_settings)]
EngineDep = Annotated[AsyncEngine, Depends(get_engine)]
SessionmakerDep = Annotated[async_sessionmaker[AsyncSession], Depends(get_sessionmaker)]
RedisDep = Annotated[Redis, Depends(get_redis)]
TaskQueueDep = Annotated[TaskQueue, Depends(get_task_queue)]
ClockDep = Annotated[Clock, Depends(get_clock)]
