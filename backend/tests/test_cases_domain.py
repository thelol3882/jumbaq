"""The rules of a case: a playable plan, the status order, the rank, and what a family sees."""

import uuid
from dataclasses import replace
from datetime import UTC, datetime

import pytest

from jumbaq.ai.public import EPISODES_PER_CASE, SUSPECTS_PER_CASE
from jumbaq.cases import domain
from jumbaq.cases.domain import FALLBACK_PLAN, Case, CaseStatus, Clue, Plan, Rank, Suspect

NOW = datetime(2026, 11, 14, 18, 0, tzinfo=UTC)
S = CaseStatus

# s1 did it. Clue 2 rules out s2, clue 3 rules out s3.
GOOD = Plan(
    title="The missing cake",
    setting="A bakery",
    suspects=(
        Suspect("s1", "Fox", "quick"),
        Suspect("s2", "Owl", "wise"),
        Suspect("s3", "Bear", "big"),
    ),
    culprit_id="s1",
    clues=(
        Clue(1, "Red fur", "s1", True),
        Clue(2, "Owl was away", "s2", False),
        Clue(3, "Bear was asleep", "s3", False),
        Clue(4, "Fox paw prints", "s1", True),
        Clue(5, "Crumbs at the den", "s1", True),
    ),
    reveal="The fox did it.",
)


def problems(plan: Plan) -> list[str]:
    return domain.plan_problems(plan, SUSPECTS_PER_CASE, EPISODES_PER_CASE)


def with_clue(index: int, clue: Clue) -> Plan:
    clues = list(GOOD.clues)
    clues[index] = clue
    return replace(GOOD, clues=tuple(clues))


def test_a_good_plan_and_the_fallback_plan_are_playable() -> None:
    assert problems(GOOD) == []
    assert problems(FALLBACK_PLAN) == []


@pytest.mark.parametrize(
    ("plan", "problem"),
    [
        (replace(GOOD, suspects=GOOD.suspects[:2]), "suspects"),
        (replace(GOOD, suspects=(*GOOD.suspects[:2], Suspect("s1", "Twin", "x"))), "suspects"),
        (replace(GOOD, culprit_id="s9"), "culprit is not a suspect"),
        (replace(GOOD, clues=GOOD.clues[:4]), "one clue for each"),
        (with_clue(4, Clue(4, "again", "s1", True)), "one clue for each"),
        (with_clue(4, Clue(5, "a stranger", "s9", True)), "not a suspect"),
        (with_clue(2, Clue(3, "Bear is big", "s1", True)), "never ruled out"),
        (with_clue(4, Clue(5, "Fox was away", "s1", False)), "rules out the culprit"),
        (with_clue(0, Clue(1, "Owl feathers", "s2", True)), "points at an innocent"),
    ],
)
def test_a_plan_that_breaks_a_rule_is_not_playable(plan: Plan, problem: str) -> None:
    assert any(problem in found for found in problems(plan)), problems(plan)


def test_the_status_moves_only_forward() -> None:
    assert domain.can_move(S.PLANNING, S.ACTIVE)
    assert domain.can_move(S.PLANNING, S.FAILED)
    assert domain.can_move(S.ACTIVE, S.ACCUSING)
    assert domain.can_move(S.ACCUSING, S.SOLVED)
    assert not domain.can_move(S.ACTIVE, S.FAILED)
    assert not domain.can_move(S.SOLVED, S.ACTIVE)
    assert not domain.can_move(S.PLANNING, S.SOLVED)


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
    long = with_clue(1, Clue(2, "word " * 30, "s2", False))
    assert any("the clue of episode 2 has 150 characters" in found for found in problems(long))
    assert problems(GOOD) == []
