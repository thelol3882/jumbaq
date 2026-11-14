"""The three steps of an evening through the API: answer, decode a cipher, strike out a suspect.
The evening counts as played only after the third."""

import re
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.cases.models import CaseRow
from jumbaq.core.deps import get_settings
from jumbaq.core.outbox import OutboxRow
from jumbaq.episodes import domain
from jumbaq.episodes.models import EpisodeRow
from jumbaq.episodes.public import EpisodePlayed, EpisodeStatus
from jumbaq.families.deps import FAMILY_COOKIE
from tests.conftest import TEST_SETTINGS
from tests.flows import create_family, deliver_all, family_body, play_evening

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("quiet_outbox")]

Sessionmaker = async_sessionmaker[AsyncSession]
# The stub plans clue 1 about s1 and rules it out; the clue is the grey feather one.
RIGHT, WRONG = "s1", "s2"
SECRET = {"shift": "GREY FEATHER LIES", "number_code": "FEATHER", "count": "EMPTY"}


async def ready_episode(
    client: TestClient, sessionmaker: Sessionmaker, ages: tuple[int, ...] = (7, 9)
) -> tuple[str, str]:
    """The id of episode 1 and its path, with a family whose kids have these ages."""
    kids = [{"nickname": f"Kid{age}", "age": age} for age in ages]
    created = client.post("/api/v1/families", json=family_body(kids=kids))
    assert created.status_code == 201, created.text
    await deliver_all(sessionmaker)
    episode_id = client.get("/api/v1/episodes/current").json()["id"]
    return episode_id, f"/api/v1/episodes/{episode_id}"


async def stored(sessionmaker: Sessionmaker, episode_id: str) -> EpisodeRow:
    async with sessionmaker() as session:
        row = await session.get(EpisodeRow, uuid.UUID(episode_id))
    assert row is not None
    return row


def content(response: Any) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    body: dict[str, Any] = response.json()["content"]
    return body


def error_code(response: Any) -> str:
    assert response.status_code == 409, response.text
    return str(response.json()["error"]["code"])


def decode(client: TestClient, path: str, word: str | None) -> Any:
    return client.post(f"{path}/decode", json={"word": word})


def strike(client: TestClient, path: str, suspect_id: str) -> Any:
    return client.post(f"{path}/strike", json={"suspect_id": suspect_id})


async def test_the_whole_evening_answer_decode_strike(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    first = live_client.get(path).json()
    assert first["content"]["step"] == "answer"
    assert first["content"]["answered"] is None and first["content"]["decode"] is None

    answered = content(live_client.post(f"{path}/answer", json={"answer": "blue"}))

    # The answer alone does not play the evening: the story and the case wait.
    assert answered["step"] == "decode" and answered["result"] is None
    assert answered["answered"]["answer"] == "blue"
    assert "blue" in answered["answered"]["resolution"]
    row = await stored(sessionmaker, episode_id)
    assert (row.status, row.answered_at is None, row.played_at) == ("ready", False, None)
    await deliver_all(sessionmaker)
    assert live_client.get("/api/v1/cases/current").json()["clues"] == []

    secret = SECRET["shift"]
    cipher = answered["decode"]
    assert cipher["level"] == "shift" and cipher["attempts"] == 0
    assert cipher["key"] == 4 and cipher["count"] is None
    assert cipher["code"] == domain.shift_text(4, secret or "")
    assert cipher["clue_with_gap"] == "A ____ by the empty plate, and Felix has only fur."
    assert (cipher["start"], cipher["shift"]) == (None, domain.shift_amount(4))
    assert len(cipher["options"]) == 3 and secret in cipher["options"]
    assert cipher["options"] == sorted(cipher["options"])
    clue_words = set(cipher["clue_with_gap"].upper().replace(",", "").split())
    assert not clue_words & {w for o in cipher["options"] for w in o.split()}
    # The secret never travels apart from the buttons.
    assert secret not in (cipher["code"], cipher["clue_with_gap"])
    assert answered["strike"] is None

    decoded = content(decode(live_client, path, " grey  feather lies "))

    assert decoded["step"] == "strike" and decoded["decode"] is None
    assert decoded["strike"] == {
        "clue": "A grey feather lies by the empty plate, and Felix has only fur.",
        "points_at": False,
        "attempts": 0,
        "decoded_word": secret,
        "revealed_word": False,
    }

    played = live_client.post(f"{path}/strike", json={"suspect_id": RIGHT})

    result = content(played)["result"]
    assert content(played)["step"] == "done" and played.json()["status"] == "played"
    assert result["decoded_word"] == secret
    assert (result["revealed_suspect"], result["struck_suspect_id"]) == (False, RIGHT)
    assert result["rules_out"] is True
    assert result["case_clue"] == "A grey feather lies by the empty plate, and Felix has only fur."
    row = await stored(sessionmaker, episode_id)
    assert (row.status, row.decode_attempts, row.strike_attempts) == ("played", 0, 0)
    assert row.played_at is not None and row.decoded_at is not None

    await deliver_all(sessionmaker)
    case = live_client.get("/api/v1/cases/current").json()
    assert [clue["text"] for clue in case["clues"]] == [result["case_clue"]]
    second = live_client.get("/api/v1/episodes/current").json()
    assert (second["number"], second["status"], second["content"]) == (2, "ready", None)


async def test_two_wrong_words_give_the_word_away_and_move_on(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    live_client.post(f"{path}/answer", json={"answer": "blue"})

    once = content(decode(live_client, path, "NOPE"))

    assert once["step"] == "decode" and once["decode"]["attempts"] == 1
    assert once["strike"] is None

    twice = content(decode(live_client, path, None))

    assert twice["step"] == "strike"
    assert twice["strike"]["decoded_word"] == SECRET["shift"]
    assert (twice["strike"]["revealed_word"], twice["strike"]["attempts"]) == (True, 0)
    row = await stored(sessionmaker, episode_id)
    assert (row.status, row.decode_attempts) == ("ready", 2)
    assert row.decoded_at is not None


async def test_a_right_word_after_one_wrong_is_not_a_reveal(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker)
    live_client.post(f"{path}/answer", json={"answer": "blue"})
    decode(live_client, path, "NOPE")

    right = content(decode(live_client, path, SECRET["shift"]))

    assert right["strike"]["revealed_word"] is False


async def test_two_wrong_suspects_finish_the_evening_and_show_the_right_one(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    live_client.post(f"{path}/answer", json={"answer": "blue"})
    decode(live_client, path, SECRET["shift"])

    once = content(strike(live_client, path, WRONG))

    assert once["step"] == "strike" and once["strike"]["attempts"] == 1
    assert once["result"] is None
    row = await stored(sessionmaker, episode_id)
    assert (row.status, row.strike_attempts) == ("ready", 1)
    await deliver_all(sessionmaker)
    assert live_client.get("/api/v1/cases/current").json()["clues"] == []

    twice = strike(live_client, path, "s3")

    assert twice.json()["status"] == "played"
    result = content(twice)["result"]
    assert (result["revealed_suspect"], result["struck_suspect_id"]) == (True, RIGHT)
    assert result["rules_out"] is True
    row = await stored(sessionmaker, episode_id)
    assert (row.status, row.strike_attempts, row.played_at is None) == ("played", 2, False)
    await deliver_all(sessionmaker)
    assert len(live_client.get("/api/v1/cases/current").json()["clues"]) == 1
    assert live_client.get("/api/v1/episodes/current").json()["number"] == 2


async def test_a_step_out_of_order_gives_409_wrong_step(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker)

    assert error_code(decode(live_client, path, "FEATHER")) == "episode.wrong_step"
    assert error_code(strike(live_client, path, RIGHT)) == "episode.wrong_step"

    live_client.post(f"{path}/answer", json={"answer": "blue"})
    answer_again = live_client.post(f"{path}/answer", json={"answer": "red"})
    assert error_code(answer_again) == "episode.wrong_step"
    assert error_code(strike(live_client, path, RIGHT)) == "episode.wrong_step"
    assert error_code(live_client.post(f"{path}/swap")) == "episode.wrong_step"

    decode(live_client, path, SECRET["shift"])
    assert error_code(decode(live_client, path, SECRET["shift"])) == "episode.wrong_step"

    strike(live_client, path, RIGHT)
    assert error_code(strike(live_client, path, RIGHT)) == "episode.wrong_step"
    assert error_code(decode(live_client, path, "FEATHER")) == "episode.wrong_step"
    # A played episode gives the same error for every step, answer and swap included.
    assert error_code(live_client.post(f"{path}/answer", json={"answer": "x"})) == (
        "episode.wrong_step"
    )
    assert error_code(live_client.post(f"{path}/swap")) == "episode.wrong_step"


async def test_a_wrong_step_changes_nothing(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)

    strike(live_client, path, WRONG)
    decode(live_client, path, "NOPE")

    row = await stored(sessionmaker, episode_id)
    assert (row.strike_attempts, row.decode_attempts, row.answered_at) == (0, 0, None)


@pytest.mark.parametrize(
    ("ages", "level"), [((3, 5), "count"), ((5, 7), "number_code"), ((4, 8), "shift")]
)
async def test_the_oldest_kid_sets_the_level_of_the_stored_episode(
    live_client: TestClient, sessionmaker: Sessionmaker, ages: tuple[int, ...], level: str
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker, ages)

    row = await stored(sessionmaker, episode_id)
    assert row.payload is not None and row.payload["cipher_level"] == level
    assert row.payload["cipher_secret"] == SECRET[level]
    assert row.payload["clue_suspect_id"] == RIGHT and row.payload["clue_points_at"] is False
    cipher = content(live_client.post(f"{path}/answer", json={"answer": "42"}))["decode"]
    assert cipher["level"] == level and cipher["key"] == 42


@pytest.mark.parametrize("ages", [(4, 5), (6, 7), (8, 9)])
async def test_no_wrong_button_of_evening_1_comes_from_a_later_clue(
    live_client: TestClient, sessionmaker: Sessionmaker, ages: tuple[int, ...]
) -> None:
    episode_id, _ = await ready_episode(live_client, sessionmaker, ages)
    row = await stored(sessionmaker, episode_id)
    async with sessionmaker() as session:
        case = await session.get(CaseRow, row.case_id)
    assert case is not None and case.plan is not None

    later = {
        word
        for clue in case.plan["clues"]
        if clue["episode"] > 1
        for word in re.findall(r"[a-z]+", clue["text"].lower())
    }
    decoys = {word.lower() for decoy in row.payload["cipher_decoys"] for word in decoy.split()}
    assert row.payload["cipher_decoys"] and not decoys & later


async def test_the_number_code_level_shows_numbers_and_three_buttons(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker, (6, 7))

    cipher = content(live_client.post(f"{path}/answer", json={"answer": "blue"}))["decode"]

    assert cipher["code"] == domain.number_code(4, "FEATHER")
    assert cipher["clue_with_gap"] == "A grey ____ lies by the empty plate, and Felix has only fur."
    # The wrong buttons are kid words or earlier clues' words, never in the sentence with the gap.
    assert len(cipher["options"]) == 3 and "FEATHER" in cipher["options"]
    assert cipher["options"] == sorted(cipher["options"])
    assert not set(cipher["options"]) & set(cipher["clue_with_gap"].upper().split())
    assert (cipher["start"], cipher["shift"]) == (domain.number_start(4), None)
    wrong = content(decode(live_client, path, "GREY"))
    assert wrong["decode"]["attempts"] == 1
    assert content(decode(live_client, path, "FEATHER"))["step"] == "strike"


async def test_the_count_level_shows_five_numbered_boxes_with_the_secret_in_box_n(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker, (4, 5))

    cipher = content(live_client.post(f"{path}/answer", json={"answer": "seven 7"}))["decode"]

    assert cipher["level"] == "count" and cipher["key"] == 7 and cipher["count"] == 2
    assert (cipher["code"], cipher["clue_with_gap"]) == (None, None)
    assert len(cipher["options"]) == 5 and len(set(cipher["options"])) == 5
    assert cipher["options"][1] == SECRET["count"]
    # The same boxes after a reload.
    reloaded = content(live_client.get(path))["decode"]
    assert reloaded["options"] == cipher["options"]


async def test_the_count_level_checks_the_picked_box_like_the_other_levels(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker, (4, 5))
    live_client.post(f"{path}/answer", json={"answer": "blue"})

    wrong = content(decode(live_client, path, None))

    assert wrong["step"] == "decode" and wrong["decode"]["attempts"] == 1
    options = wrong["decode"]["options"]
    other = next(option for option in options if option != SECRET["count"])
    # A decoy is wrong too, and the second wrong pick gives the word away.
    after = content(decode(live_client, path, other))
    assert after["step"] == "strike"
    assert after["strike"]["revealed_word"] is True
    assert after["strike"]["decoded_word"] == SECRET["count"]
    row = await stored(sessionmaker, episode_id)
    assert row.decode_attempts == 2 and row.decoded_at is not None


async def test_the_count_level_passes_the_right_box(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker, (4, 5))
    live_client.post(f"{path}/answer", json={"answer": "seven 7"})

    after = content(decode(live_client, path, " empty "))

    assert after["step"] == "strike"
    assert after["strike"]["decoded_word"] == SECRET["count"]
    assert after["strike"]["revealed_word"] is False


async def test_a_count_episode_with_no_secret_takes_any_body(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker, (4,))
    async with sessionmaker() as session:
        await session.execute(
            text(
                "UPDATE episode SET payload = payload || "
                '\'{"cipher_secret": null, "cipher_decoys": []}\'::jsonb WHERE id = :id'
            ),
            {"id": uuid.UUID(episode_id)},
        )
        await session.commit()

    cipher = content(live_client.post(f"{path}/answer", json={"answer": "seven 7"}))["decode"]

    assert cipher["count"] == 2 and cipher["options"] == []
    after = content(live_client.post(f"{path}/decode", json={}))
    assert after["step"] == "strike"
    assert after["strike"]["decoded_word"] is None and after["strike"]["revealed_word"] is False


async def test_an_episode_written_before_the_steps_is_played_by_the_answer(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    async with sessionmaker() as session:
        await session.execute(
            text(
                "UPDATE episode SET payload = payload - ARRAY["
                "'clue_suspect_id', 'clue_points_at', 'cipher_level', 'cipher_secret',"
                " 'cipher_decoys'] WHERE id = :id"
            ),
            {"id": uuid.UUID(episode_id)},
        )
        await session.commit()
    assert content(live_client.get(path))["step"] == "answer"

    played = live_client.post(f"{path}/answer", json={"answer": "blue"})

    body = content(played)
    assert played.json()["status"] == EpisodeStatus.PLAYED
    assert body["step"] == "done" and body["decode"] is None and body["strike"] is None
    assert body["result"]["answer"] == "blue"
    assert body["result"]["decoded_word"] is None
    assert (body["result"]["revealed_suspect"], body["result"]["struck_suspect_id"]) == (
        False,
        None,
    )
    assert body["result"]["rules_out"] is None
    await deliver_all(sessionmaker)
    assert len(live_client.get("/api/v1/cases/current").json()["clues"]) == 1
    assert live_client.get("/api/v1/episodes/current").json()["number"] == 2
    # An older episode has no steps to take after the answer.
    assert error_code(decode(live_client, path, "FEATHER")) == "episode.wrong_step"
    assert error_code(live_client.post(f"{path}/answer", json={"answer": "x"})) == (
        "episode.wrong_step"
    )
    assert error_code(live_client.post(f"{path}/swap")) == "episode.wrong_step"


async def test_decode_and_strike_check_their_bodies(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker)

    assert live_client.post(f"{path}/decode", json={"word": "x" * 61}).status_code == 422
    assert live_client.post(f"{path}/strike", json={}).status_code == 422
    assert live_client.post(f"{path}/strike", json={"suspect_id": ""}).status_code == 422
    assert live_client.post(f"{path}/strike", json={"suspect_id": "s" * 21}).status_code == 422


def test_the_steps_need_a_family(live_client: TestClient) -> None:
    live_client.cookies.delete(FAMILY_COOKIE)
    any_id = uuid.uuid4()

    assert decode(live_client, f"/api/v1/episodes/{any_id}", "X").status_code == 401
    assert strike(live_client, f"/api/v1/episodes/{any_id}", "s1").status_code == 401


async def test_decode_and_strike_wait_for_the_evening(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, _ = await ready_episode(live_client, sessionmaker)
    await play_evening(live_client, sessionmaker, episode_id)
    await deliver_all(sessionmaker)
    second = live_client.get("/api/v1/episodes/current").json()
    assert second["number"] == 2 and second["status"] == "ready" and second["content"] is None
    later = f"/api/v1/episodes/{second['id']}"

    for response in (decode(live_client, later, "FEATHER"), strike(live_client, later, RIGHT)):
        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == "episode.not_available_yet"
    row = await stored(sessionmaker, second["id"])
    assert (row.decode_attempts, row.strike_attempts, row.answered_at) == (0, 0, None)


async def test_decode_and_strike_of_another_family_give_404(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker)
    live_client.post(f"{path}/answer", json={"answer": "blue"})
    create_family(live_client)  # the cookie is now the other family's

    for response in (decode(live_client, path, SECRET["shift"]), strike(live_client, path, RIGHT)):
        assert response.status_code == 404, response.text
        assert response.json()["error"]["code"] == "episode.not_found"


async def played_events(sessionmaker: Sessionmaker, episode_id: str) -> int:
    async with sessionmaker() as session:
        row = await session.get(EpisodeRow, uuid.UUID(episode_id))
        assert row is not None
        return (
            await session.scalar(
                select(func.count())
                .select_from(OutboxRow)
                .where(
                    OutboxRow.family_id == row.family_id,
                    OutboxRow.topic == EpisodePlayed.topic,
                )
            )
            or 0
        )


@pytest.mark.parametrize("done_steps", [0, 1, 2])
async def test_skip_plays_the_rest_of_the_evening_from_any_step(
    live_client: TestClient, sessionmaker: Sessionmaker, done_steps: int
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    if done_steps >= 1:
        live_client.post(f"{path}/answer", json={"answer": "blue"})
    if done_steps >= 2:
        decode(live_client, path, SECRET["shift"])

    skipped = live_client.post(f"{path}/skip")

    body = content(skipped)
    assert skipped.json()["status"] == EpisodeStatus.PLAYED
    assert body["step"] == "done" and body["result"]["struck_suspect_id"] == RIGHT
    assert body["result"]["revealed_suspect"] is False
    row = await stored(sessionmaker, episode_id)
    assert row.status == "played" and row.played_at is not None
    assert (row.decode_attempts, row.strike_attempts) == (0, 0)
    assert await played_events(sessionmaker, episode_id) == 1
    await deliver_all(sessionmaker)
    assert live_client.get("/api/v1/episodes/current").json()["number"] == 2


async def test_skip_with_demo_mode_off_gives_403(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    no_demo = TEST_SETTINGS.model_copy(update={"demo_mode": False})
    live_client.app.dependency_overrides[get_settings] = lambda: no_demo  # type: ignore[attr-defined]
    try:
        refused = live_client.post(f"{path}/skip")
    finally:
        live_client.app.dependency_overrides.clear()  # type: ignore[attr-defined]
    assert refused.status_code == 403
    assert refused.json()["error"]["code"] == "episode.demo_mode_off"
    assert (await stored(sessionmaker, episode_id)).status == "ready"


async def test_skip_of_another_family_gives_404_and_of_a_played_episode_409(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    _, path = await ready_episode(live_client, sessionmaker)
    assert content(live_client.post(f"{path}/skip"))["step"] == "done"
    assert error_code(live_client.post(f"{path}/skip")) == "episode.wrong_step"

    create_family(live_client)  # the cookie is now the other family's
    other = live_client.post(f"{path}/skip")
    assert other.status_code == 404, other.text
    assert other.json()["error"]["code"] == "episode.not_found"


@pytest.mark.parametrize("status", [EpisodeStatus.REQUESTED, EpisodeStatus.GENERATING])
async def test_an_episode_still_being_written_gives_409_not_ready(
    live_client: TestClient, sessionmaker: Sessionmaker, status: EpisodeStatus
) -> None:
    episode_id, path = await ready_episode(live_client, sessionmaker)
    async with sessionmaker() as session:
        await session.execute(
            update(EpisodeRow).where(EpisodeRow.id == uuid.UUID(episode_id)).values(status=status)
        )
        await session.commit()

    for response in (
        live_client.post(f"{path}/answer", json={"answer": "blue"}),
        decode(live_client, path, SECRET["shift"]),
        strike(live_client, path, RIGHT),
        live_client.post(f"{path}/skip"),
    ):
        assert error_code(response) == "episode.not_ready"
    assert (await stored(sessionmaker, episode_id)).answered_at is None
