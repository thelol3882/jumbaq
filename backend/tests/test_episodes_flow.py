"""Episodes through the worker and the API, and the whole game on the stub model."""

import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.ai.models import LlmCallRow
from jumbaq.ai.prompts import EPISODE_SCHEMA, Prompt
from jumbaq.ai.providers.base import Reply
from jumbaq.ai.providers.stub import StubProvider
from jumbaq.ai.public import AiUnavailableError, Provider, build_story_writer
from jumbaq.cases.public import CasePlanned
from jumbaq.core.clock import SystemClock
from jumbaq.core.csrf import CSRF_HEADER
from jumbaq.core.deps import get_settings
from jumbaq.core.outbox import MAX_ATTEMPTS, OutboxDelivery, OutboxRow
from jumbaq.episodes.models import EpisodeRow
from jumbaq.episodes.public import EpisodeRequested
from jumbaq.families.deps import FAMILY_COOKIE
from tests.conftest import TEST_SETTINGS
from tests.flows import create_family, deliver_all, make_due, play_evening, stub_handlers
from tests.stripe_events import signed, subscription_event

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("quiet_outbox")]

Sessionmaker = async_sessionmaker[AsyncSession]
# The stub plans a case where s2 did it; family_body has these objects.
CULPRIT, INNOCENT = "s2", "s1"
OBJECTS = ["fridge", "sofa", "bookshelf", "kettle"]


class EpisodeChanger:
    """The stub, with every episode changed by `change`. Case plans stay the stub's."""

    name, model = "episode-changer", "test"

    def __init__(self, change: Any) -> None:
        self._change = change
        self.episode_calls = 0

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        reply = await StubProvider().complete_json(prompt, schema)
        if schema is EPISODE_SCHEMA:
            self.episode_calls += 1
            self._change(reply.data)
        return reply


class EpisodesDown:
    """The stub, but every episode call fails as a model that is down."""

    name, model = "episodes-down", "test"
    error: Exception = AiUnavailableError("timeout")

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        if schema is EPISODE_SCHEMA:
            raise self.error
        return await StubProvider().complete_json(prompt, schema)


class EpisodesBroken(EpisodesDown):
    """Every episode call fails with something that is not an AI error, like a bad reply body."""

    name = "episodes-broken"
    error = RuntimeError("not json")


def unsafe(data: dict[str, Any]) -> None:
    data["hint"] = "Climb on the chair by the window."


def retells_the_clue(data: dict[str, Any]) -> None:
    data["read_aloud"][0] += " Felix the Fox said that the feather was nothing."


def wrong_shape(data: dict[str, Any]) -> None:
    data.clear()


class UnsafeFirstDraft:
    """The stub, with the first episode draft unsafe. Keeps every episode prompt it gets."""

    name, model = "unsafe-first-draft", "test"

    def __init__(self) -> None:
        self.episode_prompts: list[Prompt] = []

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        reply = await StubProvider().complete_json(prompt, schema)
        if schema is EPISODE_SCHEMA:
            self.episode_prompts.append(prompt)
            if len(self.episode_prompts) == 1:
                unsafe(reply.data)
        return reply


class LeakyFirstDraft(UnsafeFirstDraft):
    """The stub, with the secret word of episode 1 (FEATHER, at the shift level GREY FEATHER
    LIES) in the first draft."""

    async def complete_json(self, prompt: Prompt, schema: dict[str, Any]) -> Reply:
        reply = await StubProvider().complete_json(prompt, schema)
        if schema is EPISODE_SCHEMA:
            self.episode_prompts.append(prompt)
            if len(self.episode_prompts) == 1:
                reply.data["read_aloud"][1] = "A grey feather fell on the floor."
        return reply


def handlers_with(sessionmaker: Sessionmaker, provider: Provider, daily_limit: int = 40) -> Any:
    settings = TEST_SETTINGS.model_copy(update={"ai_daily_calls_per_family": daily_limit})
    writer = build_story_writer(sessionmaker, settings, SystemClock(), provider)
    return stub_handlers(sessionmaker, writer)


async def episode_1(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> EpisodeRow:
    async with sessionmaker() as session:
        return (
            await session.scalars(
                select(EpisodeRow).where(EpisodeRow.family_id == family_id, EpisodeRow.number == 1)
            )
        ).one()


def subscribe(client: TestClient, family_id: uuid.UUID) -> None:
    secret = TEST_SETTINGS.stripe_webhook_secret
    assert secret is not None
    event = subscription_event(family_id, "active", subscription_id=f"sub_{uuid.uuid4().hex}")
    body, header = signed(event, secret.get_secret_value())
    client.post(
        "/api/v1/billing/webhook",
        content=body,
        headers={"Stripe-Signature": header, CSRF_HEADER: ""},
    ).raise_for_status()


async def count(sessionmaker: Sessionmaker, query: Any) -> int:
    async with sessionmaker() as session:
        return await session.scalar(query) or 0


async def test_the_whole_game_on_the_stub(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)

    for number in range(1, 6):
        current = live_client.get("/api/v1/episodes/current").json()
        assert (current["number"], current["status"]) == (number, "ready"), current
        if current["content"] is None:
            # Evenings 2 to 5 wait for the gap; the demo opens them at once.
            opened = live_client.post(f"/api/v1/episodes/{current['id']}/open-now")
            assert opened.status_code == 200, opened.text
            current = opened.json()
        content = current["content"]
        assert content["riddle"]["text"] and content["read_aloud"] and content["result"] is None

        played = await play_evening(
            live_client, sessionmaker, current["id"], answer=f" blue {number}\n"
        )
        result = played["content"]["result"]
        assert result["answer"] == f"blue {number}"
        assert f"blue {number}" in result["resolution"]
        await deliver_all(sessionmaker)

        case = live_client.get("/api/v1/cases/current").json()
        assert len(case["clues"]) == number
        assert result["case_clue"] == case["clues"][-1]["text"]

    assert case["status"] == "accusing"
    assert [e["status"] for e in case["episodes"]] == ["played"] * 5

    accuse = f"/api/v1/cases/{case['id']}/accuse"
    wrong = live_client.post(accuse, json={"suspect_id": INNOCENT}).json()
    assert (wrong["correct"], wrong["accusation_attempts"]) == (False, 1)
    right = live_client.post(accuse, json={"suspect_id": CULPRIT}).json()
    assert (right["correct"], right["rank"]) == (True, "detective")

    certificate = live_client.get(f"/api/v1/cases/{case['id']}/certificate").json()
    assert certificate["nicknames"] == ["Aru", "Timur"]
    # Five evenings ended the case: no sixth episode was requested.
    assert live_client.get("/api/v1/episodes/current").json()["number"] == 5

    # The second case is planned: its evenings do not exist yet, and evening 5 of case 1 is not
    # the current one any more.
    subscribe(live_client, family_id)
    assert live_client.post("/api/v1/cases").status_code == 201
    planning = live_client.get("/api/v1/episodes/current")
    assert planning.status_code == 404, planning.json()
    assert planning.json()["error"]["code"] == "episode.not_found"

    await deliver_all(sessionmaker)
    second = live_client.get("/api/v1/episodes/current").json()
    assert (second["case_number"], second["number"]) == (2, 1)


async def test_the_stub_episode_follows_the_rules(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)

    row = await episode_1(sessionmaker, family_id)
    assert (row.status, row.is_fallback) == ("ready", False)
    assert row.payload is not None and row.payload["riddle"]["target_object"] in OBJECTS


async def test_the_next_evening_waits_without_the_demo(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    create_family(live_client)
    await deliver_all(sessionmaker)
    first = live_client.get("/api/v1/episodes/current").json()
    await play_evening(live_client, sessionmaker, first["id"])
    await deliver_all(sessionmaker)

    second = live_client.get("/api/v1/episodes/current").json()
    assert second["number"] == 2 and second["content"] is None
    early = live_client.post(f"/api/v1/episodes/{second['id']}/answer", json={"answer": "7"})
    assert early.status_code == 409
    assert early.json()["error"]["code"] == "episode.not_available_yet"

    no_demo = TEST_SETTINGS.model_copy(update={"demo_mode": False})
    live_client.app.dependency_overrides[get_settings] = lambda: no_demo  # type: ignore[attr-defined]
    try:
        refused = live_client.post(f"/api/v1/episodes/{second['id']}/open-now")
    finally:
        live_client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
    assert refused.status_code == 403
    assert refused.json()["error"]["code"] == "episode.demo_mode_off"


async def test_an_episode_is_answered_once_and_swapped_once(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    create_family(live_client)
    await deliver_all(sessionmaker)
    episode = live_client.get("/api/v1/episodes/current").json()
    path = f"/api/v1/episodes/{episode['id']}"

    swapped = live_client.post(f"{path}/swap").json()
    assert swapped["content"]["swapped"] is True
    assert swapped["content"]["riddle"] != episode["content"]["riddle"]
    # The story and the hint go with the riddle that is played.
    assert swapped["content"]["hint"] != episode["content"]["hint"]
    again = live_client.post(f"{path}/swap")
    assert again.json()["error"]["code"] == "episode.already_swapped"

    answered = live_client.post(f"{path}/answer", json={"answer": "red"})
    assert answered.status_code == 200
    assert answered.json()["content"]["answered"]["resolution"].startswith("Second riddle solved")
    twice = live_client.post(f"{path}/answer", json={"answer": "red"})
    assert twice.status_code == 409
    assert twice.json()["error"]["code"] == "episode.wrong_step"


@pytest.mark.parametrize("change", [unsafe, wrong_shape, retells_the_clue])
async def test_two_bad_episodes_give_the_built_in_one(
    live_client: TestClient, sessionmaker: Sessionmaker, change: Any
) -> None:
    family_id, _ = create_family(live_client)
    provider = EpisodeChanger(change)

    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))

    row = await episode_1(sessionmaker, family_id)
    assert provider.episode_calls == 2
    assert (row.status, row.is_fallback) == ("ready", True)
    assert row.payload is not None and "window" not in str(row.payload).lower()
    # The family still sees the plan's clue.
    assert row.payload["case_clue"].startswith("A grey feather lies by the empty plate")


async def test_the_daily_cap_gives_the_built_in_episode(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    # One call plans the case; the episode finds the cap reached.
    await deliver_all(sessionmaker, handlers_with(sessionmaker, StubProvider(), daily_limit=1))

    row = await episode_1(sessionmaker, family_id)
    assert (row.status, row.is_fallback) == ("ready", True)


@pytest.mark.parametrize("provider_class", [EpisodesDown, EpisodesBroken])
async def test_a_model_that_stays_down_gives_the_built_in_episode_on_the_last_attempt(
    live_client: TestClient, sessionmaker: Sessionmaker, provider_class: type[EpisodesDown]
) -> None:
    family_id, _ = create_family(live_client)
    delivery = OutboxDelivery(sessionmaker, handlers_with(sessionmaker, provider_class()))
    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider_class()))  # first try
    row = await episode_1(sessionmaker, family_id)
    assert row.status == "generating"

    for _ in range(MAX_ATTEMPTS - 2):
        await make_due(sessionmaker, family_id)
        await delivery.deliver_due()
    assert (await episode_1(sessionmaker, family_id)).status == "generating"

    await make_due(sessionmaker, family_id)
    await delivery.deliver_due()  # the last attempt

    row = await episode_1(sessionmaker, family_id)
    assert (row.status, row.is_fallback) == ("ready", True)
    assert row.payload is not None and row.payload["cipher_secret"]


async def test_handlers_run_twice_give_the_same_result(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)
    case_id = uuid.UUID(live_client.get("/api/v1/cases/current").json()["id"])
    first = await episode_1(sessionmaker, family_id)

    handlers = stub_handlers(sessionmaker)
    await handlers[CasePlanned][0](CasePlanned(family_id, case_id))
    await handlers[EpisodeRequested][0](EpisodeRequested(family_id, first.id))

    episodes = select(func.count()).select_from(EpisodeRow).where(EpisodeRow.family_id == family_id)
    assert await count(sessionmaker, episodes) == 1
    assert (await episode_1(sessionmaker, family_id)).payload == first.payload
    requested = (
        select(func.count())
        .select_from(OutboxRow)
        .where(OutboxRow.family_id == family_id, OutboxRow.topic == EpisodeRequested.topic)
    )
    assert await count(sessionmaker, requested) == 1
    calls = (
        select(func.count())
        .select_from(LlmCallRow)
        .where(LlmCallRow.family_id == family_id, LlmCallRow.kind == "episode")
    )
    assert await count(sessionmaker, calls) == 1


async def test_another_family_gets_404(live_client: TestClient, sessionmaker: Sessionmaker) -> None:
    create_family(live_client)
    await deliver_all(sessionmaker)
    episode_id = live_client.get("/api/v1/episodes/current").json()["id"]

    create_family(live_client)  # the cookie is now the other family's
    for response in (
        live_client.get(f"/api/v1/episodes/{episode_id}"),
        live_client.post(f"/api/v1/episodes/{episode_id}/answer", json={"answer": "7"}),
        live_client.post(f"/api/v1/episodes/{episode_id}/decode", json={"word": "FEATHER"}),
        live_client.post(f"/api/v1/episodes/{episode_id}/strike", json={"suspect_id": "s2"}),
        live_client.post(f"/api/v1/episodes/{episode_id}/swap"),
        live_client.post(f"/api/v1/episodes/{episode_id}/open-now"),
    ):
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "episode.not_found"


def test_no_episode_while_the_case_is_planned(live_client: TestClient) -> None:
    create_family(live_client)

    response = live_client.get("/api/v1/episodes/current")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "episode.not_found"


def test_episodes_need_a_family(live_client: TestClient) -> None:
    live_client.cookies.delete(FAMILY_COOKIE)
    assert live_client.get("/api/v1/episodes/current").status_code == 401


async def test_the_second_try_learns_why_the_first_draft_was_refused(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = UnsafeFirstDraft()

    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))

    first, second = provider.episode_prompts
    assert "Hard limits" in first.system and "refused" not in first.user
    assert "unsafe for small kids" in second.user and "in hint" in second.user
    episode = await episode_1(sessionmaker, family_id)
    assert episode.status == "ready" and not episode.is_fallback


async def test_a_draft_that_gives_the_clue_away_is_refused_and_the_second_try_learns_it(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = LeakyFirstDraft()

    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))

    first, second = provider.episode_prompts
    # The model is told the words before the first try, and why the draft was refused after it.
    assert '"grey", "feather", "lies"' in first.system and "gives the clue away" not in first.user
    assert "gives the clue away: feather, grey in read_aloud paragraph 2" in second.user
    episode = await episode_1(sessionmaker, family_id)
    assert episode.status == "ready" and not episode.is_fallback
    assert episode.payload is not None
    assert "feather" not in str(episode.payload["read_aloud"]).lower()


async def test_an_older_episode_without_texts_in_its_fallback_riddle_still_swaps(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    await deliver_all(sessionmaker)
    row = await episode_1(sessionmaker, family_id)
    async with sessionmaker() as session:
        await session.execute(
            text(
                "UPDATE episode SET payload = jsonb_set(payload, '{fallback_riddle}',"
                " (payload->'fallback_riddle') - 'hint' - 'resolution_template') WHERE id = :id"
            ),
            {"id": row.id},
        )
        await session.commit()
    path = f"/api/v1/episodes/{row.id}"

    swapped = live_client.post(f"{path}/swap").json()["content"]
    answered = live_client.post(f"{path}/answer", json={"answer": "red"}).json()["content"]

    assert row.payload is not None and swapped["hint"] == row.payload["hint"]
    assert answered["answered"]["resolution"] == "You said red. That is exactly the secret code!"


async def test_each_evening_points_at_the_next_unused_object_of_the_home(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    provider = UnsafeFirstDraft()
    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))
    first = live_client.get("/api/v1/episodes/current").json()
    assert '"required_target_object": "fridge"' in provider.episode_prompts[0].user
    assert '"required_fallback_target_object": "sofa"' in provider.episode_prompts[0].user

    await play_evening(live_client, sessionmaker, first["id"])
    await deliver_all(sessionmaker, handlers_with(sessionmaker, provider))
    second = live_client.get("/api/v1/episodes/current").json()
    live_client.post(f"/api/v1/episodes/{second['id']}/open-now")

    shown = live_client.get(f"/api/v1/episodes/{second['id']}").json()
    assert shown["number"] == 2 and shown["content"] is not None
    async with sessionmaker() as session:
        row = (
            await session.scalars(
                select(EpisodeRow).where(EpisodeRow.family_id == family_id, EpisodeRow.number == 2)
            )
        ).one()
    assert row.payload is not None and row.payload["riddle"]["target_object"] == "sofa"
    assert row.payload["fallback_riddle"]["target_object"] == "bookshelf"
