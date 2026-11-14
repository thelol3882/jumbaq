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
    sessionmaker: Sessionmaker,
    clock: FixedClock,
    provider: Provider,
    daily_limit: int = 40,
    global_limit: int = 1_000_000,
) -> StoryWriter:
    settings = TEST_SETTINGS.model_copy(
        update={"ai_daily_calls_per_family": daily_limit, "ai_daily_call_limit": global_limit}
    )
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


async def test_the_global_cap_counts_the_calls_of_all_families(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    first_id, _ = create_family(live_client)
    second_id, _ = create_family(live_client)
    # A day of its own on every run, so the calls of other tests and runs do not count.
    day = datetime(2100, 1, 1, 8, 0, tzinfo=UTC) + timedelta(days=uuid.uuid4().int % 20000)
    clock = FixedClock(day)
    capped = writer(sessionmaker, clock, StubProvider(), global_limit=1)

    await capped.plan_case(FamilyRef(first_id), TASK)
    with pytest.raises(AiDailyLimitError):
        await capped.plan_case(FamilyRef(second_id), TASK)

    assert await calls_of(sessionmaker, second_id) == []


async def test_a_refused_draft_marks_its_call_refused_and_nothing_else(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    other_id, _ = create_family(live_client)
    story = writer(sessionmaker, FixedClock(MORNING), StubProvider())
    family = FamilyRef(family_id)
    refused = await story.plan_case(family, TASK)
    kept = await story.plan_case(family, TASK)
    theirs = await story.plan_case(FamilyRef(other_id), TASK)
    assert refused.call_id is not None and kept.call_id != refused.call_id

    await story.mark_refused(family, refused.call_id)
    # Another family cannot refuse this call, and a call with no id is ignored.
    await story.mark_refused(FamilyRef(other_id), kept.call_id)
    await story.mark_refused(family, None)

    outcomes = [row[2] for row in await calls_of(sessionmaker, family_id)]
    assert outcomes == ["refused", "ok"]
    assert [row[2] for row in await calls_of(sessionmaker, other_id)] == ["ok"]
    assert theirs.call_id is not None


async def test_a_failed_call_is_not_turned_into_a_refused_one(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    family = FamilyRef(family_id)
    with pytest.raises(AiBadOutputError):
        await writer(sessionmaker, FixedClock(MORNING), WrongShape()).plan_case(family, TASK)
    async with sessionmaker() as session:
        call_id = await session.scalar(
            select(LlmCallRow.id).where(LlmCallRow.family_id == family_id)
        )
    assert call_id is not None

    await writer(sessionmaker, FixedClock(MORNING), StubProvider()).mark_refused(family, call_id)

    assert [row[2] for row in await calls_of(sessionmaker, family_id)] == ["bad_output"]
