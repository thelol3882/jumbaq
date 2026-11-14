"""The rules of an episode: the riddles point at the home, the texts fit the kids, nothing
unsafe, the plan's clue, and a clean answer."""

import re
import uuid
from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from jumbaq.ai.public import ANSWER_SLOT
from jumbaq.episodes import domain
from jumbaq.episodes.domain import (
    CipherLevel,
    CipherPlan,
    Episode,
    EpisodeStatus,
    EveningStep,
    Payload,
    Riddle,
)

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


CLUE = "A grey feather lies by the empty plate."


@pytest.mark.parametrize(
    ("age", "level"),
    [
        (3, CipherLevel.COUNT),
        (5, CipherLevel.COUNT),
        (6, CipherLevel.NUMBER_CODE),
        (7, CipherLevel.NUMBER_CODE),
        (8, CipherLevel.SHIFT),
        (12, CipherLevel.SHIFT),
    ],
)
def test_the_oldest_kid_sets_the_level(age: int, level: CipherLevel) -> None:
    assert domain.cipher_level_for(age) == level


def test_a_number_code_hides_the_longest_good_word() -> None:
    plan = domain.plan_cipher(CLUE, 7)

    assert plan == CipherPlan(CipherLevel.NUMBER_CODE, "FEATHER", ("GREY", "LIES"))


def test_the_first_of_two_longest_words_wins() -> None:
    assert domain.plan_cipher("The kettle and the pencil", 7).secret == "KETTLE"


def test_stopwords_and_odd_lengths_are_not_secrets() -> None:
    # "there" and "where" are stopwords, "elephants" is too long, "cat" too short.
    plan = domain.plan_cipher("There where elephants cat", 7)

    assert plan == CipherPlan(CipherLevel.COUNT, None, ())


def test_decoys_come_from_the_fallback_list_when_the_clue_has_too_few_words() -> None:
    plan = domain.plan_cipher("Look at the kettle", 7)

    assert plan.secret == "KETTLE"
    assert plan.decoys == ("LOOK", "APPLE")


def test_a_shift_secret_is_three_words_around_the_best_word() -> None:
    plan = domain.plan_cipher(CLUE, 9)

    assert plan.level == CipherLevel.SHIFT
    assert plan.secret == "FEATHER LIES BY"
    assert plan.decoys == ("THE EMPTY PLATE", "A GREY FEATHER")


def test_a_shift_window_that_does_not_fit_moves_back() -> None:
    plan = domain.plan_cipher("Look near the kettle", 9)

    assert plan.secret == "NEAR THE KETTLE"
    assert plan.decoys == ("LOOK NEAR THE", "RED APPLE PIE")


def test_a_clue_of_two_words_gives_count_at_any_age() -> None:
    assert domain.plan_cipher("Green kettle", 9) == CipherPlan(CipherLevel.COUNT, None, ())


def test_the_young_get_count_with_no_secret() -> None:
    assert domain.plan_cipher(CLUE, 4) == CipherPlan(CipherLevel.COUNT, None, ())


def test_secret_and_decoys_are_distinct_upper_case_letters() -> None:
    plan = domain.plan_cipher("A pencil, a pencil, a pencil.", 9)

    options = [plan.secret, *plan.decoys]
    assert len(set(options)) == 3
    assert all(re.fullmatch(r"[A-Z ]+", option or "") for option in options)


@pytest.mark.parametrize(
    ("answer", "key"),
    [("blue", 4), ("a b c", 3), ("42", 42), ("room 12 and 7", 12), ("0", 1), ("!!!", 1), ("", 1)],
)
def test_the_key_is_the_number_in_the_answer_or_its_letters(answer: str, key: int) -> None:
    assert domain.cipher_key(answer) == key


def test_a_very_long_number_is_cut_to_nine_digits() -> None:
    assert domain.cipher_key("9" * 40) == 999_999_999


def test_a_number_code_starts_at_the_key() -> None:
    assert domain.number_code(1, "ABC") == "1-2-3"
    assert domain.number_code(3, "AB CD") == "3-4 / 5-6"
    assert domain.number_code(9, "A") == "9"
    # The start repeats after 9.
    assert domain.number_code(10, "ABC") == domain.number_code(1, "ABC")


def test_a_shift_moves_letters_forward_and_keeps_spaces() -> None:
    assert domain.shift_text(1, "ABC XYZ") == "BCD YZA"
    assert domain.shift_text(3, "FEATHER LIES") == "IHDWKHU OLHV"
    assert domain.shift_text(25, "B") == "A"
    # The shift repeats after 25.
    assert domain.shift_text(26, "ABC") == domain.shift_text(1, "ABC")


@pytest.mark.parametrize(("key", "target"), [(1, 1), (10, 10), (11, 1), (25, 5)])
def test_the_count_target_is_between_1_and_10(key: int, target: int) -> None:
    assert domain.count_target(key) == target


def test_the_gap_hides_the_secret_in_any_case_and_keeps_the_rest() -> None:
    assert domain.clue_with_gap(CLUE, "FEATHER") == "A grey ____ lies by the empty plate."
    assert domain.clue_with_gap(CLUE, "FEATHER LIES BY") == "A grey ____ the empty plate."
    assert domain.clue_with_gap("Feather, FEATHER!", "FEATHER") == "____, ____!"


def test_the_gap_does_not_cut_a_longer_word() -> None:
    assert domain.clue_with_gap("A cat in a catalog", "CAT") == "A ____ in a catalog"


def test_a_pick_is_compared_in_upper_case_with_spaces_squeezed() -> None:
    assert domain.same_word(" feather   lies ", "FEATHER LIES")
    assert not domain.same_word("feathers", "FEATHER")


def test_options_hold_every_word_and_keep_their_order_for_one_episode() -> None:
    episode_id = uuid.uuid4()

    options = domain.shuffled_options("A", ("B", "C"), episode_id)

    assert sorted(options) == ["A", "B", "C"]
    assert options == domain.shuffled_options("A", ("B", "C"), episode_id)


def test_the_evening_goes_answer_decode_strike_done() -> None:
    assert domain.evening_step(episode()) == EveningStep.ANSWER
    assert domain.evening_step(episode(answered_at=NOW)) == EveningStep.DECODE
    assert domain.evening_step(episode(answered_at=NOW, decoded_at=NOW)) == EveningStep.STRIKE
    played = episode(status=EpisodeStatus.PLAYED, answered_at=NOW, decoded_at=NOW)
    assert domain.evening_step(played) == EveningStep.DONE


def test_an_older_payload_has_no_steps_and_the_new_one_has() -> None:
    assert not domain.has_evening_steps(GOOD)
    plan = domain.plan_cipher(CLUE, 7)

    stepped = domain.with_evening_steps(GOOD, "s2", True, plan)

    assert domain.has_evening_steps(stepped)
    assert (stepped.clue_suspect_id, stepped.clue_points_at) == ("s2", True)
    assert (stepped.cipher_secret, stepped.cipher_decoys) == ("FEATHER", ("GREY", "LIES"))
