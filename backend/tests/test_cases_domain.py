"""The rules of a case: a playable plan, the status order, the rank, and what a family sees."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from jumbaq.ai.public import EPISODES_PER_CASE, SUSPECTS_PER_CASE
from jumbaq.cases import domain
from jumbaq.cases.domain import (
    FALLBACK_PLAN,
    FALLBACK_PLANS,
    Case,
    CaseStatus,
    Clue,
    Plan,
    Rank,
    Suspect,
)
from jumbaq.episodes.domain import banned_words

NOW = datetime(2026, 11, 14, 18, 0, tzinfo=UTC)
S = CaseStatus

# s1 did it. Clue 1 is the false trail at s2, clue 3 clears s2, clue 2 rules out s3, and only
# clues 4 and 5 point at the culprit.
GOOD = Plan(
    title="The missing cake",
    setting="A bakery",
    suspects=(
        Suspect("s1", "Fox", "quick"),
        Suspect("s2", "Owl", "wise"),
        Suspect("s3", "Bear the Baker", "big"),
    ),
    culprit_id="s1",
    clues=(
        Clue(1, "Owl left muddy prints by the cake", "s2", True),
        Clue(2, "Bear was asleep", "s3", False),
        Clue(3, "Owl was at the pond, so the mud is from there", "s2", False),
        Clue(4, "Fox paw prints", "s1", True),
        Clue(5, "Crumbs at the Fox den", "s1", True),
    ),
    reveal="The fox did it.",
)


def problems(plan: Plan) -> list[str]:
    return domain.plan_problems(plan, SUSPECTS_PER_CASE, EPISODES_PER_CASE, banned_words)


def with_clue_of(plan: Plan, index: int, clue: Clue) -> Plan:
    clues = list(plan.clues)
    clues[index] = clue
    return replace(plan, clues=tuple(clues))


def with_clue(index: int, clue: Clue) -> Plan:
    return with_clue_of(GOOD, index, clue)


def test_a_good_plan_is_playable() -> None:
    assert problems(GOOD) == []


@pytest.mark.parametrize("plan", FALLBACK_PLANS)
def test_every_built_in_plan_is_playable_and_names_its_suspects(plan: Plan) -> None:
    assert problems(plan) == []
    names = {suspect.id: suspect.name.split()[0] for suspect in plan.suspects}
    assert all(names[clue.suspect_id] in clue.text for clue in plan.clues)
    assert all(clue.text.isascii() for clue in plan.clues)


def test_the_built_in_plan_follows_the_case_number_and_cycles() -> None:
    first, second, third = (domain.fallback_plan(number) for number in (1, 2, 3))
    assert first is FALLBACK_PLAN
    assert len({first.title, second.title, third.title}) == 3
    assert domain.fallback_plan(4) is first and domain.fallback_plan(5) is second


@pytest.mark.parametrize(
    ("plan", "problem"),
    [
        (replace(GOOD, suspects=GOOD.suspects[:2]), "suspects"),
        (replace(GOOD, suspects=(*GOOD.suspects[:2], Suspect("s1", "Twin", "x"))), "suspects"),
        (replace(GOOD, culprit_id="s9"), "culprit is not a suspect"),
        (replace(GOOD, clues=GOOD.clues[:4]), "one clue for each"),
        (with_clue(4, Clue(4, "Fox again", "s1", True)), "one clue for each"),
        (with_clue(4, Clue(5, "a stranger", "s9", True)), "not a suspect"),
        (with_clue(4, Clue(5, "Fox was away", "s1", False)), "rules out the culprit"),
        (with_clue(4, Clue(5, "Crumbs at a den", "s1", True)), "does not say the name of Fox"),
        (with_clue(2, Clue(3, "Bear is sleepy", "s3", False)), "no clue after"),
    ],
)
def test_a_plan_that_breaks_a_rule_is_not_playable(plan: Plan, problem: str) -> None:
    assert any(problem in found for found in problems(plan)), problems(plan)


def test_a_clue_names_its_suspect_by_one_word_of_the_name_in_any_case() -> None:
    assert problems(with_clue(1, Clue(2, "the BAKER slept", "s3", False))) == []
    assert problems(with_clue(1, Clue(2, "Bear's bed was cold", "s3", False))) == []
    assert any("Bear the Baker" in f for f in problems(with_clue(1, Clue(2, "A bed", "s3", False))))


def test_a_plan_without_a_false_trail_is_not_playable() -> None:
    found = problems(with_clue(0, Clue(1, "Owl was at the pond", "s2", False)))
    assert any("exactly one false trail" in f and "found 0" in f for f in found), found


def test_a_plan_with_two_false_trails_is_not_playable() -> None:
    found = problems(with_clue(1, Clue(2, "Bear left big marks", "s3", True)))
    assert any("exactly one false trail" in f and "found 2" in f for f in found), found


def test_the_false_trail_is_in_evening_1_or_2() -> None:
    plan = replace(
        GOOD,
        clues=(
            Clue(1, "Bear was asleep", "s3", False),
            Clue(2, "Owl was at the pond", "s2", False),
            Clue(3, "Owl left muddy prints", "s2", True),
            *GOOD.clues[3:],
        ),
    )
    found = problems(plan)
    assert any("the false trail is in episode 3" in f for f in found), found


def test_the_false_trail_is_cleared_after_it_and_by_evening_3() -> None:
    # The rule-out comes before the trail: it does not explain it.
    before = replace(
        GOOD,
        clues=(
            Clue(1, "Owl was at the pond", "s2", False),
            Clue(2, "Owl left muddy prints", "s2", True),
            Clue(3, "Bear was asleep", "s3", False),
            *GOOD.clues[3:],
        ),
    )
    assert any("no clue after the false trail" in f for f in problems(before))
    # Cleared in evening 4 is too late, and evening 4 must point at the culprit anyway.
    late = with_clue(2, Clue(3, "Bear snores", "s3", False))
    late = with_clue_of(late, 3, Clue(4, "Owl was at the pond", "s2", False))
    assert any("no clue after the false trail" in f for f in problems(late))


def test_the_other_innocent_is_ruled_out_in_evenings_1_to_3() -> None:
    plan = with_clue(1, Clue(2, "Owl was at the mill", "s2", False))
    assert any("s3 is not ruled out" in f for f in problems(plan)), problems(plan)


def test_the_last_two_evenings_point_at_the_culprit_and_nobody_else() -> None:
    innocent = with_clue(3, Clue(4, "Owl feathers", "s2", True))
    assert any("episode 4 must point at the culprit" in f for f in problems(innocent))
    ruled_out = with_clue(4, Clue(5, "Bear was asleep", "s3", False))
    assert any("episode 5 must point at the culprit" in f for f in problems(ruled_out))


def test_the_culprit_is_not_pointed_at_before_evening_4() -> None:
    plan = with_clue(1, Clue(2, "Fox paw prints", "s1", True))
    assert any("episode 2 points at the culprit" in f for f in problems(plan)), problems(plan)


def test_a_title_or_a_suspect_name_the_family_used_is_refused_in_any_case() -> None:
    again = domain.plan_problems(
        GOOD, SUSPECTS_PER_CASE, EPISODES_PER_CASE, banned_words, ["THE MISSING cake"], ["owl"]
    )
    assert any('title "The missing cake" was used' in f for f in again), again
    assert any('suspect name "Owl" was used' in f for f in again), again
    assert not any("Fox" in f or "Bear" in f for f in again)
    fresh = domain.plan_problems(
        GOOD, SUSPECTS_PER_CASE, EPISODES_PER_CASE, banned_words, ["Another case"], ["Penny"]
    )
    assert fresh == []


@pytest.mark.parametrize(
    ("plan", "where"),
    [
        (with_clue(1, Clue(2, "Bear was near the window", "s3", False)), "episode 2"),
        (with_clue(4, Clue(5, "Crumbs lead out of the front doors", "s1", True)), "episode 5"),
        (replace(GOOD, title="Climbing the hill"), "title"),
        (replace(GOOD, setting="A bakery next to the road"), "setting"),
        (replace(GOOD, reveal="The fox took a knife"), "reveal"),
        (replace(GOOD, suspects=(Suspect("s1", "Fox", "plugs sockets"), *GOOD.suspects[1:])),
         "the description of s1"),
        (replace(GOOD, suspects=(*GOOD.suspects[:2], Suspect("s3", "Knife Bear", "big"))),
         "the name of s3"),
    ],
)  # fmt: skip
def test_a_plan_with_an_unsafe_word_anywhere_is_not_playable(plan: Plan, where: str) -> None:
    assert any("unsafe" in found and where in found for found in problems(plan)), problems(plan)


def test_the_unsafe_words_are_named_once_each() -> None:
    found = problems(with_clue(1, Clue(2, "Windows, a window and a stove", "s3", False)))
    assert [f for f in found if "unsafe" in f] == [
        "unsafe for small kids: stove, window, windows in the clue of episode 2; "
        "leave the word out entirely"
    ]


def test_a_clue_over_the_length_limit_is_not_playable() -> None:
    long = Clue(2, "Bear " + "x" * (domain.CLUE_MAX_CHARS - 4), "s3", False)
    assert any("the limit is 140" in found for found in problems(with_clue(1, long)))
    assert problems(with_clue(1, replace(long, text=long.text[:-1]))) == []


@pytest.mark.parametrize("plan", domain.FALLBACK_PLANS, ids=lambda plan: plan.title)
def test_every_built_in_plan_is_playable(plan: Plan) -> None:
    assert problems(plan) == []


def test_the_built_in_plans_have_their_own_worlds_titles_and_suspects() -> None:
    plans = domain.FALLBACK_PLANS
    assert len(plans) >= 3
    assert len({plan.title for plan in plans}) == len(plans)
    names = [suspect.name for plan in plans for suspect in plan.suspects]
    assert len(set(names)) == len(names)
    assert len({plan.culprit_id for plan in plans}) > 1


def test_a_built_in_plan_is_written_in_american_english() -> None:
    british = ("colour", "favourite", "cosy", "grey", "neighbour", "realise", "mum ")
    for plan in domain.FALLBACK_PLANS:
        texts = [plan.title, plan.setting, plan.reveal]
        texts += [s.description for s in plan.suspects] + [c.text for c in plan.clues]
        text = " ".join(texts).lower()
        assert not [word for word in british if word in text]


def test_the_built_in_plan_follows_the_case_number_and_wraps_round() -> None:
    plans = domain.FALLBACK_PLANS
    assert [domain.fallback_plan(n) for n in (1, 2, 3)] == list(plans)
    assert domain.fallback_plan(len(plans) + 1) == plans[0]


def test_the_rank_depends_on_the_attempts() -> None:
    assert [domain.rank_for(n) for n in (1, 2, 3, 7)] == [
        Rank.FIRST_TRY, Rank.SECOND_TRY, Rank.LATER, Rank.LATER,
    ]  # fmt: skip


def case(**changes: object) -> Case:
    base = Case(
        id=uuid.uuid4(), family_id=uuid.uuid4(), number=1, status=S.ACTIVE, plan=GOOD,
        is_fallback=False, played_episodes=0, accusation_attempts=0, rank=None, solved_at=None,
    )  # fmt: skip
    return replace(base, **changes)  # type: ignore[arg-type]


def test_only_the_clues_of_played_episodes_are_visible() -> None:
    assert domain.visible_clues(case(played_episodes=0)) == ()
    assert [c.episode for c in domain.visible_clues(case(played_episodes=2))] == [1, 2]
    assert domain.visible_clues(case(plan=None, status=S.PLANNING)) == ()


def test_the_last_episode_opens_the_accusation() -> None:
    after_four = domain.with_episode_played(case(played_episodes=3), 4, EPISODES_PER_CASE)
    assert (after_four.played_episodes, after_four.status) == (4, S.ACTIVE)

    after_five = domain.with_episode_played(after_four, 5, EPISODES_PER_CASE)
    assert (after_five.played_episodes, after_five.status) == (5, S.ACCUSING)


def test_an_old_or_repeated_episode_changes_nothing() -> None:
    accusing = case(played_episodes=5, status=S.ACCUSING)
    assert domain.with_episode_played(accusing, 3, EPISODES_PER_CASE) == accusing
    assert domain.with_episode_played(accusing, 5, EPISODES_PER_CASE) == accusing


def test_a_wrong_suspect_only_adds_an_attempt() -> None:
    result = domain.accuse(case(status=S.ACCUSING), "s2", NOW)

    assert not result.correct
    assert result.case.accusation_attempts == 1
    assert (result.case.status, result.case.rank, result.case.solved_at) == (S.ACCUSING, None, None)


def test_the_right_suspect_solves_the_case_with_a_rank() -> None:
    result = domain.accuse(case(status=S.ACCUSING, accusation_attempts=1), "s1", NOW)

    assert result.correct
    assert result.case.status == S.SOLVED
    assert result.case.rank == Rank.SECOND_TRY
    assert result.case.solved_at == NOW


def test_a_clue_is_one_short_sentence() -> None:
    long = with_clue(1, Clue(2, "Bear " + "word " * 29, "s3", False))
    assert any("the clue of episode 2 has 150 characters" in found for found in problems(long))
    assert problems(GOOD) == []


def test_there_are_many_kid_friendly_worlds_each_with_things_to_lose() -> None:
    assert len(domain.WORLDS) >= 12
    assert len({world.place for world in domain.WORLDS}) == len(domain.WORLDS)
    for world in domain.WORLDS:
        assert len(world.things) >= 3
        assert banned_words(world.place) == []
        assert all(banned_words(thing) == [] for thing in world.things)


def test_the_world_of_a_case_is_stable_and_cases_differ() -> None:
    case_id = uuid.uuid4()
    assert domain.world_for(case_id) == domain.world_for(case_id)
    chosen = {domain.world_for(uuid.UUID(int=n)) for n in range(300)}
    assert len({place for place, _ in chosen}) == len(domain.WORLDS)
    for place, thing in chosen:
        world = next(w for w in domain.WORLDS if w.place == place)
        assert thing in world.things
