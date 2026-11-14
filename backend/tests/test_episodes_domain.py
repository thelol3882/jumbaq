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
    fallback_riddle=Riddle(
        "You sit on me.",
        "sofa",
        "number",
        "Count the cushions.",
        hint="It is soft and in the living room.",
        resolution_template=f"The cushions said {ANSWER_SLOT}! The door opened.",
    ),
    resolution_template=f"The code was {ANSWER_SLOT}! The door opened.",
    case_clue="A grey feather lies by the plate.",
    cliffhanger="Who was here before you?",
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
        (replace(GOOD, fallback_riddle=replace(GOOD.fallback_riddle, resolution_template="No.")),
         "fallback riddle's own resolution_template"),
        (replace(GOOD, fallback_riddle=replace(
            GOOD.fallback_riddle, resolution_template=f"{ANSWER_SLOT} {ANSWER_SLOT}")),
         "fallback riddle's own resolution_template"),
        (replace(GOOD, fallback_riddle=replace(GOOD.fallback_riddle, hint=" ")),
         "fallback riddle needs its own hint"),
        (replace(GOOD, read_aloud=()), "paragraphs"),
        (replace(GOOD, read_aloud=("x",) * 7), "paragraphs"),
        (replace(GOOD, read_aloud=("word " * 130,)), "paragraph is too long"),
        (replace(GOOD, hint="word " * 90), "text is too long"),
    ],
)  # fmt: skip
def test_an_episode_that_breaks_a_rule_is_refused(payload: Payload, problem: str) -> None:
    assert any(problem in found for found in problems(payload)), problems(payload)


def test_texts_for_a_kid_under_6_are_shorter() -> None:
    medium = replace(GOOD, read_aloud=("the cat sat " * 42,))
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
    # Only suffixes make a form: "plugin", "plughole" and "doorway" are other words.
    text = "the cat walks in the doorway of the roadshow, past the plugin and the plughole"
    assert domain.banned_words(text) == []


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("Find the scissor.", ["scissor"]),
        ("Two pairs of scissors", ["scissors"]),
        ("Go through the front-door now", ["front door"]),
        ("Go through the front door now", ["front door"]),
        ("Play outdoors today", ["outdoors"]),
        ("Take your medication", ["medication"]),
        ("a burnt matchstick", ["matchstick"]),
        ("the matchsticks", ["matchsticks"]),
    ],
)
def test_more_unsafe_words_and_their_forms_are_caught(text: str, found: list[str]) -> None:
    assert domain.banned_words(text) == found


def test_the_reviewer_s_text_is_caught_in_every_form() -> None:
    text = "windows, sockets and plugs; climbed; leave the house"
    assert domain.banned_words(text) == [
        "windows", "sockets", "plugs", "climbed", "leave the house",
    ]  # fmt: skip


@pytest.mark.parametrize(
    "text",
    [
        "Two Knives", "the matches", "ovens", "he plugged it", "she is climbing", "a climber",
        "balconies", "the wiring", "wired up", "front doors", "strangers", "pills and tablets",
        "medicines", "the scissors", "lighters", "streets", "It was outside", "WINDOW",
        "leaving home", "she leaves the house", "they left the house", "leave   the\nhome",
    ],
)  # fmt: skip
def test_plurals_and_regular_forms_of_unsafe_words_are_found(text: str) -> None:
    assert domain.banned_words(text) != [], text


def test_a_found_phrase_has_single_spaces_and_lower_case() -> None:
    assert domain.banned_words("Please LEAVE   the\n House now") == ["leave the house"]


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


def test_the_swap_also_changes_the_hint_and_the_resolution() -> None:
    assert episode().hint == GOOD.hint
    assert episode().resolution_template == GOOD.resolution_template
    swapped = episode(used_fallback_riddle=True)
    assert swapped.hint == GOOD.fallback_riddle.hint
    assert swapped.resolution_template == GOOD.fallback_riddle.resolution_template


def test_an_older_swapped_riddle_with_no_texts_of_its_own_uses_the_episode_s() -> None:
    bare = replace(GOOD.fallback_riddle, hint="", resolution_template="")
    old = replace(GOOD, fallback_riddle=bare)

    swapped = episode(payload=old, used_fallback_riddle=True)

    assert swapped.hint == GOOD.hint
    assert swapped.resolution_template == GOOD.resolution_template


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


def test_the_built_in_fallback_riddle_has_its_own_hint_and_resolution() -> None:
    payload = domain.built_in_payload("A case", "Clue.", OBJECTS, 1, False, ANSWER_SLOT)

    assert payload.fallback_riddle.hint
    assert payload.fallback_riddle.resolution_template.count(ANSWER_SLOT) == 1
    swapped = episode(payload=payload, used_fallback_riddle=True)
    assert swapped.hint == payload.hint


UNSAFE_HOME = ("kitchen knife", "gas stove", "windows", "fridge")


@pytest.mark.parametrize("number", range(1, 6))
def test_the_built_in_episode_never_points_at_an_unsafe_object(number: int) -> None:
    payload = domain.built_in_payload(
        "A case", "Clue.", UNSAFE_HOME, number, number == 5, ANSWER_SLOT
    )

    assert domain.banned_words(str(payload)) == []
    assert payload.riddle.target_object == "fridge"
    assert payload.fallback_riddle.target_object == "fridge"


@pytest.mark.parametrize("number", range(1, 6))
def test_the_built_in_episode_of_a_home_with_no_safe_object_needs_nothing_from_it(
    number: int,
) -> None:
    payload = domain.built_in_payload(
        "A case", "Clue.", ("kitchen knife", "oven", "front door"), number, False, ANSWER_SLOT
    )

    assert domain.banned_words(str(payload)) == []
    assert payload.riddle.target_object != payload.fallback_riddle.target_object
    assert payload.riddle.target_object not in ("kitchen knife", "oven", "front door")
    assert domain.built_in_payload("A", "C.", (), number, False, ANSWER_SLOT).riddle.text


def test_only_safe_objects_go_on() -> None:
    assert domain.safe_objects(UNSAFE_HOME) == ("fridge",)
    assert domain.safe_objects(OBJECTS) == OBJECTS


def test_a_riddle_about_an_unsafe_object_is_not_safe() -> None:
    riddle = Riddle("Find me.", "kitchen knife", "colour", "Look in the drawer.")
    assert not domain.is_safe_riddle(riddle, ("kitchen knife", "fridge"), 7)


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


OTHERS = (
    "Boris snored in the back room the whole night.",
    "Felix was at his grandma's all evening.",
)


def test_a_number_code_hides_the_longest_good_word() -> None:
    plan = domain.plan_cipher(CLUE, 7, OTHERS)

    assert plan.level == CipherLevel.NUMBER_CODE and plan.secret == "FEATHER"
    # The wrong buttons are words of the other clues, not of this one, and as long as the secret.
    assert plan.decoys == ("EVENING", "SNORED")


def test_no_decoy_is_a_word_of_the_clue() -> None:
    clue = "Grandma's grey feather lies by the empty plate."
    others = ("Grey feathers and the empty plate.", "Olive socks hide under pillows.")
    for age in (7, 9):
        plan = domain.plan_cipher(clue, age, others)
        words = {word for word in re.findall(r"[A-Z]+", clue.upper().replace("'", ""))}
        for decoy in plan.decoys:
            assert not words & set(decoy.split()), decoy


def test_the_first_of_two_longest_words_wins() -> None:
    assert domain.plan_cipher("The kettle and the pencil", 7).secret == "KETTLE"


def test_stopwords_and_odd_lengths_are_not_secrets() -> None:
    # "there" and "where" are stopwords, "elephants" is too long, "cat" too short for a cipher:
    # the level falls back to count, which hides a short word.
    plan = domain.plan_cipher("There where elephants cat", 7)

    assert plan.level == CipherLevel.COUNT and plan.secret == "CAT"
    assert domain.plan_cipher("There where elephants", 7) == CipherPlan(CipherLevel.COUNT, None, ())


def test_decoys_come_from_the_kid_words_when_the_other_clues_have_too_few() -> None:
    plan = domain.plan_cipher("Look at the kettle", 7)

    assert plan.secret == "KETTLE"
    assert plan.decoys == ("PENCIL", "BANANA")
    # Six letters like the secret, so the length does not give it away.
    assert {len(word) for word in plan.decoys} == {6}


def test_a_decoy_in_the_clue_is_left_out() -> None:
    plan = domain.plan_cipher("Look at the kettle and the garden pencil", 7)

    assert plan.secret == "KETTLE"
    assert "GARDEN" not in plan.decoys and "PENCIL" not in plan.decoys


def test_a_shift_secret_is_three_words_that_do_not_start_or_end_on_filler() -> None:
    plan = domain.plan_cipher(CLUE, 9, OTHERS)

    assert plan.level == CipherLevel.SHIFT
    assert plan.secret == "GREY FEATHER LIES"


def test_a_shift_secret_does_not_end_on_and() -> None:
    plan = domain.plan_cipher("Basil Bunny nibbles carrots and cakes", 9)

    assert plan.secret is not None
    first, last = plan.secret.split()[0], plan.secret.split()[-1]
    assert first not in ("AND", "THE", "A") and last not in ("AND", "THE", "A")
    assert plan.secret == "BUNNY NIBBLES CARROTS"


@pytest.mark.parametrize("filler", ["and", "the", "a", "of", "to", "in", "on", "at", "is", "was"])
def test_a_shift_window_never_ends_on_a_filler_word(filler: str) -> None:
    plan = domain.plan_cipher(f"Penny baked cookies {filler} {filler} kettle {filler}", 9)

    words = (plan.secret or "").split()
    assert not words or (words[0].lower() != filler and words[-1].lower() != filler)


def test_a_shift_secret_takes_two_words_when_three_do_not_fit() -> None:
    plan = domain.plan_cipher("Boris snored in the back", 9)

    assert plan.secret == "BORIS SNORED"
    assert len(plan.decoys) == 2 and all(len(d.split()) == 2 for d in plan.decoys)


def test_a_shift_clue_with_no_window_gives_count() -> None:
    assert domain.plan_cipher("Look at the kettle", 9) == CipherPlan(CipherLevel.COUNT, None, ())


def test_shift_decoys_are_phrases_of_the_other_clues_that_are_not_in_the_clue() -> None:
    plan = domain.plan_cipher(CLUE, 9, OTHERS)

    assert len(plan.decoys) == 2
    clue_words = set(CLUE.upper().rstrip(".").split())
    for decoy in plan.decoys:
        assert len(decoy.split()) == 3 and not clue_words & set(decoy.split())


def test_an_apostrophe_keeps_a_word_whole() -> None:
    plan = domain.plan_cipher("Grandma\u2019s hat hid under Bram's bed", 9)

    assert plan.secret == "HID UNDER BRAMS"
    assert "S" not in " ".join((plan.secret or "", *plan.decoys)).split()


def test_a_clue_of_one_word_gives_count_at_any_age() -> None:
    plan = domain.plan_cipher("Kettle", 9)

    assert (plan.level, plan.secret) == (CipherLevel.COUNT, "KETTLE")


def test_a_clue_of_two_words_gives_a_two_word_secret_at_the_shift_level() -> None:
    plan = domain.plan_cipher("Green kettle", 9)

    assert plan.secret == "GREEN KETTLE"
    assert all(len(decoy.split()) == 2 for decoy in plan.decoys)


def test_the_young_get_count_with_a_short_secret_and_four_decoys() -> None:
    plan = domain.plan_cipher(CLUE, 4)

    assert plan.level == CipherLevel.COUNT
    assert plan.secret == "EMPTY"
    assert len(plan.decoys) == 4 and len(set(plan.decoys)) == 4


def test_the_count_secret_is_short_and_not_a_filler_word() -> None:
    plan = domain.plan_cipher("The big FEATHER and the cat saw them", 5)

    # "feather" has 7 letters, "them" and "the" are filler words, "saw" and "cat" have 3.
    assert plan.secret in {"BIG", "CAT", "SAW"}
    assert 3 <= len(plan.secret or "") <= 6


def test_the_count_decoys_are_never_words_of_the_clue() -> None:
    clue = "The apple and the cloud sat by the moon and the star"

    plan = domain.plan_cipher(clue, 4)

    words = clue.upper().split()
    assert plan.secret in words
    assert len(plan.decoys) == 4
    assert not set(plan.decoys) & set(words)


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


@pytest.mark.parametrize(("key", "target"), [(1, 1), (5, 5), (6, 1), (10, 5), (11, 1), (42, 2)])
def test_the_count_target_is_between_1_and_5(key: int, target: int) -> None:
    assert domain.count_target(key) == target


@pytest.mark.parametrize("target", range(1, 6))
def test_the_count_boxes_keep_their_order_with_the_secret_in_the_target_box(target: int) -> None:
    decoys = ("A", "B", "C", "D")

    options = domain.count_options("X", decoys, target)

    assert len(options) == 5 and options[target - 1] == "X"
    assert [o for o in options if o != "X"] == list(decoys)


def test_the_gap_hides_the_secret_in_any_case_and_keeps_the_rest() -> None:
    assert domain.clue_with_gap(CLUE, "FEATHER") == "A grey ____ lies by the empty plate."
    assert domain.clue_with_gap(CLUE, "FEATHER LIES BY") == "A grey ____ the empty plate."
    assert domain.clue_with_gap("Feather, FEATHER!", "FEATHER") == "____, ____!"


def test_the_gap_hides_a_word_with_an_apostrophe() -> None:
    clue = "Felix was at his grandma's all evening"
    plan = domain.plan_cipher(clue, 9)

    assert plan.secret == "GRANDMAS ALL EVENING"
    assert domain.clue_with_gap(clue, plan.secret or "") == "Felix was at his ____"
    assert domain.clue_with_gap("Bram\u2019s bed", "BRAMS") == "____ bed"
    assert domain.clue_with_gap("Felix was at his grandma's all evening", "EVENING") == (
        "Felix was at his grandma's all ____"
    )


def test_the_gap_does_not_cut_a_longer_word() -> None:
    assert domain.clue_with_gap("A cat in a catalog", "CAT") == "A ____ in a catalog"


def test_a_pick_is_compared_in_upper_case_with_spaces_squeezed() -> None:
    assert domain.same_word(" feather   lies ", "FEATHER LIES")
    assert not domain.same_word("feathers", "FEATHER")


def test_options_are_in_alphabetical_order_whatever_the_secret() -> None:
    assert domain.sorted_options("PIG", ("MORNING", "PENNY")) == ["MORNING", "PENNY", "PIG"]
    assert domain.sorted_options("A", ("C", "B")) == ["A", "B", "C"]


def test_the_start_and_the_shift_are_the_numbers_of_the_ciphers() -> None:
    assert [domain.number_start(key) for key in (1, 9, 10, 4)] == [1, 9, 1, 4]
    assert [domain.shift_amount(key) for key in (1, 25, 26, 4)] == [1, 25, 1, 4]
    assert domain.number_code(4, "A") == str(domain.number_start(4))
    assert domain.shift_text(4, "A") == "E"


def test_the_words_to_keep_out_of_the_story_skip_filler() -> None:
    assert domain.secret_words("GREY FEATHER LIES") == ("GREY", "FEATHER", "LIES")
    assert domain.secret_words("GRANDMAS ALL EVENING") == ("GRANDMAS", "EVENING")
    assert domain.secret_words("FEATHER") == ("FEATHER",)
    assert domain.secret_words(None) == ()


def test_a_draft_that_uses_the_secret_is_refused_and_says_where() -> None:
    leaky = replace(GOOD, read_aloud=("The Feather was on the table.", "Quiet."))

    found = domain.draft_problems(leaky, OBJECTS, 7, ANSWER_SLOT, "FEATHER")

    assert len(found) == 1
    assert "feather" in found[0] and "read_aloud paragraph 1" in found[0]
    assert "gives the clue away" in found[0]


def test_the_secret_is_found_in_every_text_but_the_clue() -> None:
    for field in ("recap", "hint", "resolution_template", "cliffhanger"):
        text = f"A grey feather. {ANSWER_SLOT}" if field == "resolution_template" else "A feather"
        leaky = replace(GOOD, **{field: text})
        found = domain.draft_problems(leaky, OBJECTS, 7, ANSWER_SLOT, "FEATHER")
        assert any(f"in {field}" in problem for problem in found), field
    riddle = replace(GOOD.riddle, parent_note="Look for the feather's colour.")
    assert domain.draft_problems(replace(GOOD, riddle=riddle), OBJECTS, 7, ANSWER_SLOT, "FEATHER")


def test_the_clue_itself_may_hold_the_secret() -> None:
    assert domain.draft_problems(GOOD, OBJECTS, 7, ANSWER_SLOT, "FEATHER") == []


def test_only_whole_words_count_as_the_secret() -> None:
    text = replace(GOOD, recap="The feathers and the feathery hat.")

    assert domain.draft_problems(text, OBJECTS, 7, ANSWER_SLOT, "FEATHER") == []


def test_one_word_of_a_secret_phrase_is_enough_to_refuse_but_filler_is_not() -> None:
    by_filler = replace(GOOD, recap="She walked by the lake.")
    by_word = replace(GOOD, recap="Grey birds sat there.")

    assert domain.draft_problems(by_filler, OBJECTS, 7, ANSWER_SLOT, "GREY FEATHER LIES BY") == []
    assert domain.draft_problems(by_word, OBJECTS, 7, ANSWER_SLOT, "GREY FEATHER LIES BY")


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
    assert (stepped.cipher_secret, stepped.cipher_decoys) == (plan.secret, plan.decoys)


def test_the_plan_clue_is_not_measured_again() -> None:
    # The clue is quoted from the plan, which checks it; the episode cannot change it.
    assert problems(replace(GOOD, case_clue="word " * 80), youngest=4) == []


ENGLISH = (
    "Once upon a time the little fox went to the old barn. It was dark and she was not afraid, "
    "because her friend Zo\u00eb was with her and they had a lantern."
)
GERMAN = (
    "Es war einmal ein kleiner Fuchs, der in die alte Scheune ging. Es war dunkel, aber er "
    "hatte keine Angst, weil seine Freundin mit einer Laterne bei ihm war."
)
GERMAN_NO_UMLAUTS = (
    "Der kleine Fuchs ging mit seiner Freundin in die alte Scheune und sie fanden dort eine "
    "Laterne, die noch brannte."
)
RUSSIAN = "Жила-была маленькая лиса, которая пошла в старый сарай."


NICKNAMES = (
    "Маша, the bakery needs you. Маша and Диас "
    "will look at the table, and it is time to find the clue."
)


@pytest.mark.parametrize("text", [ENGLISH, NICKNAMES, "Hello there!", ""])
def test_an_english_text_passes_the_language_check(text: str) -> None:
    assert domain.is_english(text)


@pytest.mark.parametrize("text", [GERMAN, GERMAN_NO_UMLAUTS, RUSSIAN])
def test_a_text_in_another_language_fails_the_language_check(text: str) -> None:
    assert not domain.is_english(text)


def test_a_draft_in_german_is_refused_with_a_clear_message() -> None:
    assert problems(GOOD) == []
    found = problems(replace(GOOD, read_aloud=(GERMAN,)))
    assert any("write in English" in problem for problem in found), found
