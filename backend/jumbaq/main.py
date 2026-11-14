"""Run with `uvicorn jumbaq.main:create_app --factory`. Nothing happens at import time."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from jumbaq import health
from jumbaq.billing.routers import subscription as subscription_routers
from jumbaq.billing.routers import webhook as webhook_routers
from jumbaq.core.clock import SystemClock
from jumbaq.core.config import CorsSettings, Settings
from jumbaq.core.csrf import CSRF_HEADER, require_csrf_header_on_change
from jumbaq.core.db import create_engine, create_sessionmaker
from jumbaq.core.exception_handlers import register_exception_handlers
from jumbaq.core.logging import setup_logging
from jumbaq.core.middleware import RequestContextMiddleware
from jumbaq.families.routers import family as family_routers

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Raises if a required setting is missing, so the API does not start.
    settings = Settings()
    setup_logging(settings.log_level)
    app.state.settings = settings
    app.state.clock = SystemClock()
    # Both clients connect lazily, so the API starts even if a service is still booting.
    app.state.engine = create_engine(settings.database_url)
    app.state.sessionmaker = create_sessionmaker(app.state.engine)
    # A Redis client that can also put tasks in the queue of the worker.
    app.state.redis = ArqRedis.from_url(settings.redis_url, socket_connect_timeout=2)
    try:
        yield
    finally:
        await app.state.redis.aclose()
        await app.state.engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="jumbaq API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
    )
    register_exception_handlers(app)

    api = APIRouter(prefix=API_PREFIX, dependencies=[Depends(require_csrf_header_on_change)])
    api.include_router(health.router)
    api.include_router(family_routers.router)
    api.include_router(subscription_routers.router)
    app.include_router(api)

    # Payment providers cannot send the CSRF header or a family cookie. Each webhook checks
    # the provider's signature instead, so these routes skip the CSRF check.
    webhooks = APIRouter(prefix=API_PREFIX)
    webhooks.include_router(webhook_routers.router)
    app.include_router(webhooks)

    app.add_middleware(RequestContextMiddleware)
    # Added last, so it is the outer one: preflight requests and errors get CORS headers too.
    origins = CorsSettings().cors_origins
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-Request-ID", CSRF_HEADER],
            expose_headers=["X-Request-ID"],
            max_age=600,
        )
    return app
