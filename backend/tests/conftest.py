"""Unit tests use an app without the lifespan, so no real engine or Redis is created.

Dependencies are replaced with app.dependency_overrides. Tests marked `integration`
use the real services (`make up`): `live_client` runs the lifespan, and the database
fixtures below migrate the test database once and connect as both roles.
"""

import os
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from jumbaq.core.config import Settings
from jumbaq.core.csrf import CSRF_HEADER, CSRF_VALUE
from jumbaq.core.db import create_engine, create_sessionmaker
from jumbaq.core.deps import get_settings
from jumbaq.main import create_app

BACKEND_DIR = Path(__file__).resolve().parent.parent

TEST_SETTINGS = Settings(
    environment="test",
    database_url="postgresql+asyncpg://unused:unused@unused:5432/unused",
    redis_url="redis://unused:6379/0",
    # Tests never clean the database, so the shared daily cap must not run out across runs.
    ai_daily_call_limit=1_000_000,
)

# What the web app sends with every request. HTTPS, so the client sends the Secure cookie back.
FROM_THE_WEB_APP = {CSRF_HEADER: CSRF_VALUE}
BASE_URL = "https://testserver"


@pytest.fixture
def app() -> Iterator[FastAPI]:
    application = create_app()
    application.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    yield application
    application.dependency_overrides.clear()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    # No `with`, so the lifespan does not run.
    return TestClient(
        app, base_url=BASE_URL, headers=FROM_THE_WEB_APP, raise_server_exceptions=False
    )


@pytest.fixture
def live_client(migrated_database: None) -> Iterator[TestClient]:
    with TestClient(create_app(), base_url=BASE_URL, headers=FROM_THE_WEB_APP) as c:
        yield c


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        pytest.fail(f"{name} is not set. Run the tests with `make test` after `make up`.")
    return value


@pytest.fixture(scope="session")
def migrated_database() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = _env("JUMBAQ_MIGRATION_DATABASE_URL")
    config.attributes["configure_logger"] = False
    # env.py calls asyncio.run, which must not run on the thread of the test event loop.
    with ThreadPoolExecutor(max_workers=1) as pool:
        pool.submit(command.upgrade, config, "head").result()


@pytest.fixture(scope="session")
async def app_engine(migrated_database: None) -> AsyncIterator[AsyncEngine]:
    """Connects as jumbaq_app, like the API and the worker."""
    engine = create_engine(_env("JUMBAQ_DATABASE_URL"))
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
def sessionmaker(app_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return create_sessionmaker(app_engine)


@pytest.fixture
async def quiet_outbox(sessionmaker: async_sessionmaker[AsyncSession]) -> None:
    """Marks the waiting outbox rows of earlier tests processed, so `deliver_due()` sees only
    the rows of this test. All tests share one database, and the app role cannot delete."""
    async with sessionmaker() as session:
        await session.execute(
            text("UPDATE outbox SET processed_at = now() WHERE processed_at IS NULL")
        )
        await session.commit()
