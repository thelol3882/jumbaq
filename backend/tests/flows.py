"""Shared steps of the tests."""

import uuid
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.providers.stub import StubProvider
from jumbaq.ai.public import StoryWriter, build_story_writer
from jumbaq.core.clock import SystemClock
from jumbaq.core.events import Event
from jumbaq.core.outbox import Handler, OutboxDelivery
from jumbaq.episodes.models import EpisodeRow
from jumbaq.families.deps import FAMILY_COOKIE
from jumbaq.worker.main import build_handlers
from tests.conftest import TEST_SETTINGS


def family_body(**changes: Any) -> dict[str, Any]:
    body = {
        "kids": [{"nickname": "Aru", "age": 7}, {"nickname": "Timur", "age": 9}],
        "rooms": ["kitchen", "living room", "bedroom"],
        "objects": ["fridge", "sofa", "bookshelf", "kettle"],
    }
    return body | changes


def create_family(client: TestClient, **changes: Any) -> tuple[uuid.UUID, str]:
    """The id of the new family and its session token from the cookie."""
    response = client.post("/api/v1/families", json=family_body(**changes))
    assert response.status_code == 201, response.text
    return uuid.UUID(response.json()["id"]), response.cookies[FAMILY_COOKIE]


def stub_handlers(
    sessionmaker: async_sessionmaker[AsyncSession], writer: StoryWriter | None = None
) -> dict[type[Event], list[Handler]]:
    """The worker's handlers with the stub model, or the given writer."""
    if writer is None:
        writer = build_story_writer(sessionmaker, TEST_SETTINGS, SystemClock(), StubProvider())
    return build_handlers(sessionmaker, writer, SystemClock())


async def deliver_all(
    sessionmaker: async_sessionmaker[AsyncSession],
    handlers: dict[type[Event], list[Handler]] | None = None,
) -> None:
    """Delivers the outbox until it is quiet, as the worker would: a handler publishes the next
    event, which the next round delivers."""
    delivery = OutboxDelivery(sessionmaker, handlers or stub_handlers(sessionmaker))
    for _ in range(20):
        if await delivery.deliver_due() == 0:
            return
    raise AssertionError("the outbox did not get quiet")


async def play_evening(
    client: TestClient,
    sessionmaker: async_sessionmaker[AsyncSession],
    episode_id: str,
    answer: str = "blue",
) -> dict[str, Any]:
    """The three steps with the right picks, read from the stored episode. Returns the played
    episode."""
    path = f"/api/v1/episodes/{episode_id}"
    async with sessionmaker() as session:
        row = await session.get(EpisodeRow, uuid.UUID(episode_id))
    assert row is not None and row.payload is not None
    payload = row.payload
    answered = client.post(f"{path}/answer", json={"answer": answer})
    assert answered.status_code == 200, answered.text
    decoded = client.post(f"{path}/decode", json={"word": payload["cipher_secret"]})
    assert decoded.status_code == 200, decoded.text
    struck = client.post(f"{path}/strike", json={"suspect_id": payload["clue_suspect_id"]})
    assert struck.status_code == 200, struck.text
    played: dict[str, Any] = struck.json()
    assert played["status"] == "played", played
    return played
