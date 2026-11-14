"""The StoryWriter on the real database: every call is recorded and the daily cap holds."""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.models import LlmCallRow
from jumbaq.ai.prompts import Prompt
from jumbaq.ai.providers.base import Reply
from jumbaq.ai.providers.stub import StubProvider
from jumbaq.ai.public import (
    AiBadOutputError,
    AiDailyLimitError,
    AiUnavailableError,
    CasePlanInput,
    HomeInput,
    KidInput,
    Provider,
    StoryWriter,
    build_story_writer,
)
from jumbaq.core.clock import FixedClock
from jumbaq.core.family import FamilyRef
from tests.conftest import TEST_SETTINGS
from tests.flows import create_family

pytestmark = pytest.mark.integration

Sessionmaker = async_sessionmaker[AsyncSession]

TASK = CasePlanInput(
    HomeInput((KidInput("Aru", 7),), ("kitchen",), ("fridge", "sofa", "kettle")), case_number=1
)
# 10:00 in Almaty.
MORNING = datetime(2026, 11, 14, 5, 0, tzinfo=UTC)


class WrongShape:
    name = "wrong-shape"
    model = "test"

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        return Reply({"title": "no suspects"}, input_tokens=50, output_tokens=7)


class Down:
    name = "down"
    model = "test"

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        raise AiUnavailableError("timeout")


def writer(
    sessionmaker: Sessionmaker, clock: FixedClock, provider: Provider, daily_limit: int = 40
) -> StoryWriter:
    settings = TEST_SETTINGS.model_copy(update={"ai_daily_calls_per_family": daily_limit})
    return build_story_writer(sessionmaker, settings, clock, provider)


async def calls_of(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> list[tuple[Any, ...]]:
    async with sessionmaker() as session:
        rows = await session.execute(
            select(
                LlmCallRow.kind,
                LlmCallRow.provider,
                LlmCallRow.outcome,
                LlmCallRow.input_tokens,
                LlmCallRow.output_tokens,
            )
            .where(LlmCallRow.family_id == family_id)
            .order_by(LlmCallRow.created_at, LlmCallRow.id)
        )
        return [tuple(row) for row in rows]


async def test_a_plan_from_the_stub_is_recorded(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    plan = await writer(sessionmaker, FixedClock(MORNING), StubProvider()).plan_case(
        FamilyRef(family_id), TASK
    )

    assert len(plan.suspects) == 3
    assert await calls_of(sessionmaker, family_id) == [("case_plan", "stub", "ok", 0, 0)]


async def test_a_reply_of_the_wrong_shape_is_recorded_with_its_tokens(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    with pytest.raises(AiBadOutputError):
        await writer(sessionmaker, FixedClock(MORNING), WrongShape()).plan_case(
            FamilyRef(family_id), TASK
        )

    assert await calls_of(sessionmaker, family_id) == [
        ("case_plan", "wrong-shape", "bad_output", 50, 7)
    ]


async def test_a_provider_that_is_down_is_recorded_and_the_error_goes_up(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    with pytest.raises(AiUnavailableError):
        await writer(sessionmaker, FixedClock(MORNING), Down()).plan_case(
            FamilyRef(family_id), TASK
        )

    assert await calls_of(sessionmaker, family_id) == [("case_plan", "down", "unavailable", 0, 0)]


async def test_the_daily_cap_counts_every_call_and_starts_again_at_midnight(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    other_id, _ = create_family(live_client)
    clock = FixedClock(MORNING)
    capped = writer(sessionmaker, clock, StubProvider(), daily_limit=2)
    family = FamilyRef(family_id)

    await capped.plan_case(family, TASK)
    # A failed call counts too: it may have cost money.
    with pytest.raises(AiUnavailableError):
        await writer(sessionmaker, clock, Down(), daily_limit=2).plan_case(family, TASK)
    with pytest.raises(AiDailyLimitError):
        await capped.plan_case(family, TASK)

    assert len(await calls_of(sessionmaker, family_id)) == 2
    # Another family has its own cap.
    await capped.plan_case(FamilyRef(other_id), TASK)

    # 00:30 the next day in Almaty.
    clock.advance(timedelta(hours=14, minutes=30))
    await capped.plan_case(family, TASK)
    assert len(await calls_of(sessionmaker, family_id)) == 3
