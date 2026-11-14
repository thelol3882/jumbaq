"""Cases through the worker and the API on the real database, with the stub model."""

import uuid
from functools import partial
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.models import LlmCallRow
from jumbaq.ai.prompts import CASE_PLAN_SCHEMA, Prompt
from jumbaq.ai.providers.base import Reply
from jumbaq.ai.providers.stub import StubProvider
from jumbaq.ai.public import AiUnavailableError, Provider, build_story_writer
from jumbaq.cases.domain import FALLBACK_PLAN
from jumbaq.cases.models import CaseRow
from jumbaq.cases.public import CaseOpened, CasePlanned, CaseSolved
from jumbaq.cases.services.progress import CaseProgress
from jumbaq.cases.uow import CasesUoW
from jumbaq.core.clock import SystemClock
from jumbaq.core.config import Settings
from jumbaq.core.csrf import CSRF_HEADER
from jumbaq.core.family import FamilyRef
from jumbaq.core.outbox import OutboxDelivery, OutboxRow
from jumbaq.families.deps import FAMILY_COOKIE
from jumbaq.families.public import FamilyCreated
from tests.conftest import TEST_SETTINGS
from tests.flows import create_family, deliver_all, stub_handlers
from tests.stripe_events import signed, subscription_event

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("quiet_outbox")]

Sessionmaker = async_sessionmaker[AsyncSession]
# The stub plans a case where s2 did it.
CULPRIT, INNOCENT = "s2", "s1"
STUB_REVEAL = "Olga the Owl took the cake"


class WrongShape:
    name, model = "wrong-shape", "test"

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        return Reply({"title": "no suspects"}, 0, 0)


class BadThenStub:
    """A plan of the wrong shape first, then the stub's good plan. Episodes come from the stub."""

    name, model = "bad-then-stub", "test"

    def __init__(self) -> None:
        self.plan_calls = 0

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        if schema is CASE_PLAN_SCHEMA:
            self.plan_calls += 1
            if self.plan_calls == 1:
                return Reply({"title": "no suspects"}, 0, 0)
        return await StubProvider().complete_json(prompt, schema)


class RuleBreaker:
    """The stub's plan with a clue that rules out the culprit."""

    name, model = "rule-breaker", "test"

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        reply = await StubProvider().complete_json(prompt, schema)
        reply.data["clues"][4] |= {"suspect_id": CULPRIT, "points_at": False}
        return reply


class Down:
    name, model = "down", "test"

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        raise AiUnavailableError("timeout")


def handlers_with(sessionmaker: Sessionmaker, provider: Provider, daily_limit: int = 40) -> Any:
    settings = TEST_SETTINGS.model_copy(update={"ai_daily_calls_per_family": daily_limit})
    writer = build_story_writer(sessionmaker, settings, SystemClock(), provider)
    return stub_handlers(sessionmaker, writer)


async def case_1(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> tuple[Any, ...]:
    async with sessionmaker() as session:
        row = (
            await session.execute(
                select(CaseRow.status, CaseRow.is_fallback, CaseRow.title).where(
                    CaseRow.family_id == family_id, CaseRow.number == 1
                )
            )
        ).one()
        return tuple(row)


async def events(sessionmaker: Sessionmaker, family_id: uuid.UUID, topic: str) -> int:
    async with sessionmaker() as session:
        return (
            await session.scalar(
                select(func.count())
                .select_from(OutboxRow)
                .where(OutboxRow.family_id == family_id, OutboxRow.topic == topic)
            )
            or 0
        )


async def play_all(sessionmaker: Sessionmaker, family_id: uuid.UUID, case_id: str) -> None:
    progress = CaseProgress(partial(CasesUoW, sessionmaker))
    for number in range(1, 6):
        await progress.episode_played(FamilyRef(family_id), uuid.UUID(case_id), number)


async def test_a_new_family_gets_a_planned_case_1(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    await deliver_all(sessionmaker)

    assert await case_1(sessionmaker, family_id) == (
        "active",
        False,
        "Case 1: the missing honey cake",
    )
    assert await events(sessionmaker, family_id, CaseOpened.topic) == 1
    assert await events(sessionmaker, family_id, CasePlanned.topic) == 1


async def test_one_bad_answer_is_asked_again(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = BadThenStub()

    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))

    assert provider.plan_calls == 2
    assert (await case_1(sessionmaker, family_id))[:2] == ("active", False)


@pytest.mark.parametrize("provider", [WrongShape(), RuleBreaker()])
async def test_two_bad_plans_give_the_built_in_one(
    live_client: TestClient, sessionmaker: Sessionmaker, provider: Provider
) -> None:
    family_id, _ = create_family(live_client)

    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))

    assert await case_1(sessionmaker, family_id) == ("active", True, FALLBACK_PLAN.title)
    assert await events(sessionmaker, family_id, CasePlanned.topic) == 1


async def test_the_daily_cap_fails_the_case_instead_of_retrying(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    await deliver_all(sessionmaker, handlers_with(sessionmaker, StubProvider(), daily_limit=0))

    assert await case_1(sessionmaker, family_id) == ("failed", False, None)
    assert await events(sessionmaker, family_id, CasePlanned.topic) == 0


async def test_a_model_that_is_down_leaves_the_case_for_the_next_try(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    delivery = OutboxDelivery(sessionmaker, handlers_with(sessionmaker, Down()))

    await delivery.deliver_due()  # FamilyCreated: opens the case
    await delivery.deliver_due()  # CaseOpened: the model is down

    assert (await case_1(sessionmaker, family_id))[0] == "planning"
    async with sessionmaker() as session:
        row = (
            await session.execute(
                select(OutboxRow.attempts, OutboxRow.last_error).where(
                    OutboxRow.family_id == family_id, OutboxRow.topic == CaseOpened.topic
                )
            )
        ).one()
    assert tuple(row) == (1, "AiUnavailableError")


async def test_planning_twice_changes_nothing(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)
    case_id = uuid.UUID(live_client.get("/api/v1/cases/current").json()["id"])

    handlers = stub_handlers(sessionmaker)
    await handlers[CaseOpened][0](CaseOpened(family_id, case_id))
    await handlers[FamilyCreated][0](FamilyCreated(family_id))

    assert (await case_1(sessionmaker, family_id))[:2] == ("active", False)
    assert await events(sessionmaker, family_id, CaseOpened.topic) == 1
    assert await events(sessionmaker, family_id, CasePlanned.topic) == 1
    # A planned case is left alone before the model is asked again.
    async with sessionmaker() as session:
        calls = await session.scalar(
            select(func.count())
            .select_from(LlmCallRow)
            .where(LlmCallRow.family_id == family_id, LlmCallRow.kind == "case_plan")
        )
    assert calls == 1


def test_no_case_before_the_worker_opens_it(live_client: TestClient) -> None:
    create_family(live_client)

    response = live_client.get("/api/v1/cases/current")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "case.not_found"


async def test_the_current_case_shows_only_what_was_played(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)

    case = live_client.get("/api/v1/cases/current").json()

    assert case["number"] == 1 and case["status"] == "active"
    assert [s["id"] for s in case["suspects"]] == ["s1", "s2", "s3"]
    assert case["clues"] == []
    # Episode 1 is written as soon as the case is planned; the rest wait.
    assert [(e["number"], e["status"]) for e in case["episodes"]] == [
        (1, "ready"), *((n, "locked") for n in range(2, 6)),
    ]  # fmt: skip
    assert case["episodes"][0]["id"] and case["episodes"][1]["id"] is None
    assert "culprit" not in str(case) and STUB_REVEAL not in str(case)

    progress = CaseProgress(partial(CasesUoW, sessionmaker))
    await progress.episode_played(FamilyRef(family_id), uuid.UUID(case["id"]), 2)
    after_two = live_client.get("/api/v1/cases/current").json()

    assert [(c["episode"], c["suspect_id"], c["rules_out"]) for c in after_two["clues"]] == [
        (1, CULPRIT, False),
        (2, INNOCENT, True),
    ]
    # The clue of episode 5 would give the culprit away.
    assert "hollow of the old oak" not in str(after_two)
    assert "culprit" not in str(after_two) and STUB_REVEAL not in str(after_two)


async def test_the_kids_accuse_until_they_find_the_culprit(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)
    case_id = live_client.get("/api/v1/cases/current").json()["id"]
    accuse = f"/api/v1/cases/{case_id}/accuse"

    early = live_client.post(accuse, json={"suspect_id": CULPRIT})
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "case.not_accusing"

    await play_all(sessionmaker, family_id, case_id)
    assert live_client.get("/api/v1/cases/current").json()["status"] == "accusing"

    unknown = live_client.post(accuse, json={"suspect_id": "s9"})
    assert unknown.status_code == 422
    assert unknown.json()["error"]["fields"] == {"suspect_id": "case.unknown_suspect"}

    wrong = live_client.post(accuse, json={"suspect_id": INNOCENT})
    assert wrong.status_code == 200
    assert wrong.json() == {
        "correct": False, "accusation_attempts": 1, "rank": None, "reveal": None,
        "culprit_id": None,
    }  # fmt: skip

    right = live_client.post(accuse, json={"suspect_id": CULPRIT}).json()
    assert (right["correct"], right["accusation_attempts"], right["rank"]) == (True, 2, "detective")
    assert right["culprit_id"] == CULPRIT and right["reveal"].startswith(STUB_REVEAL)
    assert await events(sessionmaker, family_id, CaseSolved.topic) == 1

    again = live_client.post(accuse, json={"suspect_id": CULPRIT})
    assert again.status_code == 409


async def test_the_certificate_of_a_solved_case(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)
    case_id = live_client.get("/api/v1/cases/current").json()["id"]
    certificate = f"/api/v1/cases/{case_id}/certificate"

    assert live_client.get(certificate).json()["error"]["code"] == "case.not_solved"

    await play_all(sessionmaker, family_id, case_id)
    live_client.post(f"/api/v1/cases/{case_id}/accuse", json={"suspect_id": CULPRIT})
    found = live_client.get(certificate).json()

    assert found["title"] == "Case 1: the missing honey cake"
    assert found["rank"] == "chief_detective"
    # The youngest kid first.
    assert found["nicknames"] == ["Aru", "Timur"]
    assert found["solved_at"]


async def test_another_family_cannot_touch_the_case(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    create_family(live_client)
    await deliver_all(sessionmaker)
    case_id = live_client.get("/api/v1/cases/current").json()["id"]

    create_family(live_client)  # the cookie is now the other family's
    for response in (
        live_client.post(f"/api/v1/cases/{case_id}/accuse", json={"suspect_id": CULPRIT}),
        live_client.get(f"/api/v1/cases/{case_id}/certificate"),
    ):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "case.not_found"


async def test_the_next_case_needs_a_solved_case_and_a_subscription(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)
    case_id = live_client.get("/api/v1/cases/current").json()["id"]

    unsolved = live_client.post("/api/v1/cases")
    assert unsolved.status_code == 409
    assert unsolved.json()["error"]["code"] == "case.not_solved"

    await play_all(sessionmaker, family_id, case_id)
    live_client.post(f"/api/v1/cases/{case_id}/accuse", json={"suspect_id": CULPRIT})
    unpaid = live_client.post("/api/v1/cases")
    assert unpaid.status_code == 402
    assert unpaid.json()["error"]["code"] == "billing.payment_required"

    settings = Settings()
    assert settings.stripe_webhook_secret is not None
    event = subscription_event(family_id, "active", subscription_id=f"sub_{uuid.uuid4().hex}")
    body, header = signed(event, settings.stripe_webhook_secret.get_secret_value())
    live_client.post(
        "/api/v1/billing/webhook",
        content=body,
        headers={"Stripe-Signature": header, CSRF_HEADER: ""},
    ).raise_for_status()

    started = live_client.post("/api/v1/cases")
    assert started.status_code == 201, started.text
    assert (started.json()["number"], started.json()["status"]) == (2, "planning")
    assert await events(sessionmaker, family_id, CaseOpened.topic) == 2

    await deliver_all(sessionmaker)
    assert live_client.get("/api/v1/cases/current").json()["status"] == "active"


def test_cases_need_a_family(live_client: TestClient) -> None:
    live_client.cookies.delete(FAMILY_COOKIE)
    assert live_client.get("/api/v1/cases/current").status_code == 401
