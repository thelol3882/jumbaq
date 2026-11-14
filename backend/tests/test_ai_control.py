"""The owner switch of the model: the service, the writer, the built-in stories and the CLI.

The switch is one row shared by all tests, so every test puts it back to "on, limit from the
settings" before and after.
"""

import io
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from functools import partial

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.control import run
from jumbaq.ai.domain import AiControl
from jumbaq.ai.errors import AiLimitInvalidError
from jumbaq.ai.models import LlmCallRow
from jumbaq.ai.providers.stub import StubProvider
from jumbaq.ai.public import (
    AiDailyLimitError,
    AiDisabledError,
    CasePlanInput,
    HomeInput,
    KidInput,
    Provider,
    StoryWriter,
    build_story_writer,
)
from jumbaq.ai.services.control import AiControlService
from jumbaq.ai.uow import AiUoW
from jumbaq.cases.models import CaseRow
from jumbaq.core.clock import FixedClock, SystemClock
from jumbaq.core.family import FamilyRef
from jumbaq.episodes.models import EpisodeRow
from tests.conftest import TEST_SETTINGS
from tests.flows import create_family, deliver_all, stub_handlers

Sessionmaker = async_sessionmaker[AsyncSession]

TASK = CasePlanInput(
    HomeInput((KidInput("Aru", 7),), ("kitchen",), ("fridge", "sofa", "kettle")), case_number=1
)
MORNING = datetime(2026, 11, 14, 5, 0, tzinfo=UTC)


def control(enabled: bool = True, limit: int | None = None) -> AiControl:
    return AiControl(enabled, limit, MORNING)


@pytest.fixture
async def reset_control(sessionmaker: Sessionmaker) -> AsyncIterator[None]:
    async def put_back() -> None:
        async with AiUoW(sessionmaker) as uow:
            await uow.control.save(control())
            await uow.commit()

    await put_back()
    yield
    await put_back()


pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("reset_control")]


def service(sessionmaker: Sessionmaker, setting_limit: int = 400) -> AiControlService:
    return AiControlService(partial(AiUoW, sessionmaker), FixedClock(MORNING), setting_limit)


def writer(
    sessionmaker: Sessionmaker, provider: Provider, global_limit: int = 1_000_000
) -> StoryWriter:
    settings = TEST_SETTINGS.model_copy(update={"ai_daily_call_limit": global_limit})
    return build_story_writer(sessionmaker, settings, FixedClock(MORNING), provider)


async def llm_calls(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> int:
    async with sessionmaker() as session:
        return (
            await session.scalar(
                select(func.count())
                .select_from(LlmCallRow)
                .where(LlmCallRow.family_id == family_id)
            )
            or 0
        )


class CountingProvider:
    name, model = "counting", "test"

    def __init__(self) -> None:
        self.calls = 0

    async def complete_json(self, prompt, schema):  # type: ignore[no-untyped-def]
        self.calls += 1
        return await StubProvider().complete_json(prompt, schema)


async def test_the_switch_and_the_limit_are_kept(sessionmaker: Sessionmaker) -> None:
    ai = service(sessionmaker)

    off = await ai.switch(False)
    limited = await ai.set_daily_limit(1000)
    on = await ai.switch(True)

    assert (off.enabled, off.from_table, off.limit_from_settings) == (False, True, True)
    assert (limited.enabled, limited.daily_call_limit, limited.limit_from_settings) == (
        False,
        1000,
        False,
    )
    # Switching keeps the limit.
    assert (on.enabled, on.daily_call_limit) == (True, 1000)
    assert (await ai.status()).calls_today >= 0


async def test_a_negative_limit_is_refused(sessionmaker: Sessionmaker) -> None:
    ai = service(sessionmaker)
    await ai.set_daily_limit(7)

    with pytest.raises(AiLimitInvalidError):
        await ai.set_daily_limit(-1)

    assert (await ai.status()).daily_call_limit == 7


async def test_a_zero_limit_is_allowed(sessionmaker: Sessionmaker) -> None:
    assert (await service(sessionmaker).set_daily_limit(0)).daily_call_limit == 0


async def test_a_disabled_model_is_not_called_and_not_recorded(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = CountingProvider()
    await service(sessionmaker).switch(False)

    with pytest.raises(AiDisabledError):
        await writer(sessionmaker, provider).plan_case(FamilyRef(family_id), TASK)

    assert provider.calls == 0
    assert await llm_calls(sessionmaker, family_id) == 0


async def test_switching_on_again_lets_the_model_write(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = CountingProvider()
    await service(sessionmaker).switch(False)
    await service(sessionmaker).switch(True)

    await writer(sessionmaker, provider).plan_case(FamilyRef(family_id), TASK)

    assert provider.calls == 1


async def test_no_row_values_keep_the_settings_in_charge(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    # reset_control writes "on, no limit", which behaves like no row at all.
    family_id, _ = create_family(live_client)

    with pytest.raises(AiDailyLimitError):
        await writer(sessionmaker, CountingProvider(), global_limit=0).plan_case(
            FamilyRef(family_id), TASK
        )
    await writer(sessionmaker, CountingProvider()).plan_case(FamilyRef(family_id), TASK)


async def test_the_limit_of_the_control_wins_over_the_setting(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = CountingProvider()

    await service(sessionmaker).set_daily_limit(0)
    with pytest.raises(AiDailyLimitError):
        await writer(sessionmaker, provider, global_limit=1_000_000).plan_case(
            FamilyRef(family_id), TASK
        )

    await service(sessionmaker).set_daily_limit(1_000_000)
    await writer(sessionmaker, provider, global_limit=0).plan_case(FamilyRef(family_id), TASK)
    assert provider.calls == 1


async def test_a_new_family_gets_built_in_stories_while_the_model_is_off(
    live_client: TestClient, sessionmaker: Sessionmaker, quiet_outbox: None
) -> None:
    await service(sessionmaker).switch(False)
    family_id, _ = create_family(live_client)

    await deliver_all(sessionmaker, stub_handlers(sessionmaker))

    async with sessionmaker() as session:
        case = (
            await session.execute(
                select(CaseRow.status, CaseRow.is_fallback).where(
                    CaseRow.family_id == family_id, CaseRow.number == 1
                )
            )
        ).one()
        episode = (
            await session.execute(
                select(EpisodeRow.status, EpisodeRow.is_fallback).where(
                    EpisodeRow.family_id == family_id, EpisodeRow.number == 1
                )
            )
        ).one()
    assert tuple(case) == ("active", True)
    assert tuple(episode) == ("ready", True)
    assert await llm_calls(sessionmaker, family_id) == 0


async def cli(sessionmaker: Sessionmaker, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    code = await run(argv, sessionmaker, TEST_SETTINGS, SystemClock(), out)
    return code, out.getvalue()


async def test_the_cli_status_names_the_source(sessionmaker: Sessionmaker) -> None:
    code, text = await cli(sessionmaker, "status")

    assert code == 0
    assert "enabled: yes" in text
    assert "daily limit: 1000000 (from settings)" in text
    assert "calls today:" in text


async def test_the_cli_switches_and_sets_the_limit(sessionmaker: Sessionmaker) -> None:
    code, text = await cli(sessionmaker, "off")
    assert code == 0 and "enabled: no (from table)" in text

    code, text = await cli(sessionmaker, "on")
    assert code == 0 and "enabled: yes (from table)" in text

    code, text = await cli(sessionmaker, "limit", "5")
    assert code == 0 and "daily limit: 5 (from table)" in text
    assert "enabled: yes" in (await cli(sessionmaker, "status"))[1]


async def test_the_cli_refuses_a_negative_limit(
    sessionmaker: Sessionmaker, capsys: pytest.CaptureFixture[str]
) -> None:
    code, text = await cli(sessionmaker, "limit", "-1")

    assert (code, text) == (2, "")
    assert "negative" in capsys.readouterr().err
    assert "daily limit: 1000000" in (await cli(sessionmaker, "status"))[1]


async def test_the_cli_exits_with_2_on_unknown_input(sessionmaker: Sessionmaker) -> None:
    for argv in (("limit", "many"), ("limit",), ("sing",), ()):
        with pytest.raises(SystemExit) as stop:
            await cli(sessionmaker, *argv)
        assert stop.value.code == 2
