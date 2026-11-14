"""The rules of an episode: the riddles point at the home, the texts fit the kids, nothing
unsafe, the plan's clue, and a clean answer."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from jumbaq.ai.public import ANSWER_SLOT
from jumbaq.episodes import domain
from jumbaq.episodes.domain import Episode, EpisodeStatus, Payload, Riddle

OBJECTS = ("fridge", "sofa", "kettle")
NOW = datetime(2026, 11, 14, 18, 0, tzinfo=UTC)

GOOD = Payload(
    recap="Last time you found the first clue.",
    read_aloud=("The bakery was quiet.", "A note lay on the table."),
    riddle=Riddle("I keep the milk cold.", "fridge", "colour", "Look at the fridge door."),
    hint="It hums in the kitchen.",
    fallback_riddle=Riddle("You sit on me.", "sofa", "number", "Count the cushions."),
    resolution_template=f"The code was {ANSWER_SLOT}! The door opened.",
    case_clue="A grey feather lies by the plate.",
    cliffhanger="Who left the feather?",
)


def problems(payload: Payload, youngest: int = 7) -> list[str]:
    return domain.draft_problems(payload, OBJECTS, youngest, ANSWER_SLOT)


def test_a_good_episode_has_no_problems() -> None:
    assert problems(GOOD) == []
    assert problems(GOOD, youngest=4) == []


@pytest.mark.parametrize(
    ("payload", "problem"),
    [
        (replace(GOOD, riddle=replace(GOOD.riddle, target_object="piano")), "not in the home"),
        (replace(GOOD, fallback_riddle=replace(GOOD.fallback_riddle, target_object="car")),
         "not in the home"),
        (replace(GOOD, fallback_riddle=replace(GOOD.fallback_riddle, target_object="fridge")),
         "same object"),
        (replace(GOOD, resolution_template="The door opened."), "exactly once"),
        (replace(GOOD, resolution_template=f"{ANSWER_SLOT} and {ANSWER_SLOT}"), "exactly once"),
        (replace(GOOD, read_aloud=()), "paragraphs"),
        (replace(GOOD, read_aloud=("x",) * 7), "paragraphs"),
        (replace(GOOD, read_aloud=("word " * 130,)), "paragraph is too long"),
        (replace(GOOD, hint="word " * 90), "text is too long"),
    ],
)  # fmt: skip
def test_an_episode_that_breaks_a_rule_is_refused(payload: Payload, problem: str) -> None:
    assert any(problem in found for found in problems(payload)), problems(payload)


def test_texts_for_a_kid_under_6_are_shorter() -> None:
    medium = replace(GOOD, read_aloud=("word " * 100,))
    assert problems(medium, youngest=7) == []
    assert any("too long" in found for found in problems(medium, youngest=5))


@pytest.mark.parametrize(
    "payload",
    [
        replace(GOOD, read_aloud=("Take the KNIFE from the drawer.",)),
        replace(GOOD, hint="Look behind the stove."),
        replace(GOOD, cliffhanger="Tomorrow we go out to the street."),
        replace(GOOD, riddle=replace(GOOD.riddle, text="Climb up to find me.")),
        replace(
            GOOD, fallback_riddle=replace(GOOD.fallback_riddle, parent_note="Open the window.")
        ),
        replace(GOOD, recap="Your medicine is in the cupboard."),
    ],
)
def test_unsafe_words_anywhere_are_refused(payload: Payload) -> None:
    assert any("unsafe" in found for found in problems(payload)), problems(payload)


def test_safe_words_that_only_look_alike_pass() -> None:
    # "plugin" is not "plug", "climbs" is not in the list, "doorway" is not "front door".
    assert domain.banned_words("the cat walks in the doorway of the roadshow") == []


def test_the_clue_is_always_the_plan_s() -> None:
    assert domain.with_plan_clue(GOOD, "The plan's words.").case_clue == "The plan's words."


def test_an_answer_becomes_one_short_line() -> None:
    assert domain.clean_answer("  red \n\n and   blue ") == "red and blue"
    assert len(domain.clean_answer("a" * 500)) == domain.ANSWER_MAX_LENGTH


def test_the_resolution_puts_the_answer_in_the_slot_and_keeps_other_braces() -> None:
    template = f"{{The box}} said {ANSWER_SLOT}."
    assert domain.resolution(template, "{7}", ANSWER_SLOT) == "{The box} said {7}."


def episode(**changes: object) -> Episode:
    base = Episode(
        id=uuid.uuid4(), family_id=uuid.uuid4(), case_id=uuid.uuid4(), case_number=1, number=1,
        status=EpisodeStatus.READY, payload=GOOD, answer=None, resolution=None,
        available_at=NOW, played_at=None, is_fallback=False, used_fallback_riddle=False,
    )  # fmt: skip
    return replace(base, **changes)  # type: ignore[arg-type]


def test_the_next_evening_opens_after_the_gap() -> None:
    assert domain.available_after(NOW, 16) == NOW + timedelta(hours=16)
    assert domain.is_open(episode(available_at=NOW), NOW)
    assert not domain.is_open(episode(available_at=NOW + timedelta(seconds=1)), NOW)
    assert not domain.is_open(episode(available_at=None), NOW)


def test_the_swap_changes_the_riddle_in_use() -> None:
    assert episode().riddle == GOOD.riddle
    assert episode(used_fallback_riddle=True).riddle == GOOD.fallback_riddle


@pytest.mark.parametrize(("number", "last"), [(1, False), (5, True)])
def test_the_built_in_episode_is_always_playable(number: int, last: bool) -> None:
    payload = domain.built_in_payload(
        "A case", "The plan clue.", OBJECTS, number, last, ANSWER_SLOT
    )

    assert problems(payload, youngest=3) == []
    assert payload.case_clue == "The plan clue."


def test_the_built_in_episode_keeps_a_safe_riddle_of_the_model() -> None:
    model_riddle = Riddle("I boil water.", "kettle", "colour", "Look at the kettle.")
    payload = domain.built_in_payload(
        "A case", "Clue.", OBJECTS, 2, False, ANSWER_SLOT, model_riddle
    )

    assert payload.riddle == model_riddle
    assert payload.fallback_riddle.target_object != "kettle"
    assert problems(payload) == []


def test_a_riddle_is_safe_only_for_this_home() -> None:
    assert domain.is_safe_riddle(GOOD.riddle, OBJECTS, 7)
    assert not domain.is_safe_riddle(replace(GOOD.riddle, target_object="piano"), OBJECTS, 7)
    assert not domain.is_safe_riddle(replace(GOOD.riddle, text="Near the oven."), OBJECTS, 7)
