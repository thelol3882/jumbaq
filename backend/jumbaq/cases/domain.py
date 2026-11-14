"""A detective case of 5 episodes. Case 1 is free.

The plan is fixed when the case is planned: three suspects, one culprit and one clue per
episode. The model writes it, these rules check it, and a built-in plan stands in when the model
fails twice.

The numbers of suspects and episodes come from ai.public through the caller: importing it here
would pull the database into the domain. So does the check for words unsafe for small kids,
which comes from episodes.public.
"""

import uuid
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum

FIRST_CASE = 1


class CaseStatus(StrEnum):
    """planning -> active -> accusing -> solved, and planning -> failed."""

    PLANNING = "planning"
    ACTIVE = "active"
    ACCUSING = "accusing"
    SOLVED = "solved"
    FAILED = "failed"


_NEXT_STATUSES = {
    CaseStatus.PLANNING: {CaseStatus.ACTIVE, CaseStatus.FAILED},
    CaseStatus.ACTIVE: {CaseStatus.ACCUSING},
    CaseStatus.ACCUSING: {CaseStatus.SOLVED},
}


class Rank(StrEnum):
    """By the number of accusations it took. The values are translation keys of the web app,
    so a rename happens here and in its texts only."""

    FIRST_TRY = "chief_detective"
    SECOND_TRY = "detective"
    LATER = "junior_detective"


@dataclass(frozen=True)
class Suspect:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class Clue:
    episode: int
    text: str
    suspect_id: str
    # True: the clue points at this suspect. False: it rules the suspect out.
    points_at: bool


@dataclass(frozen=True)
class Plan:
    title: str
    setting: str
    suspects: tuple[Suspect, ...]
    culprit_id: str
    clues: tuple[Clue, ...]
    reveal: str


@dataclass(frozen=True)
class Case:
    id: uuid.UUID
    family_id: uuid.UUID
    number: int
    status: CaseStatus
    plan: Plan | None
    is_fallback: bool
    # How many episodes the family has played, so only their clues are shown.
    played_episodes: int
    accusation_attempts: int
    rank: Rank | None
    solved_at: datetime | None


@dataclass(frozen=True)
class EpisodeBrief:
    """What the episodes module needs to write one episode. Never the culprit."""

    case_id: uuid.UUID
    case_number: int
    title: str
    setting: str
    suspects: tuple[Suspect, ...]
    clue: Clue
    # The texts of the plan's other clues. Only the episode's cipher uses them, for wrong
    # buttons; they are never shown or sent to the model.
    other_clues: tuple[str, ...] = ()


# Every episode quotes its clue word for word to the kids, so a clue is one short sentence.
CLUE_MAX_CHARS = 140
# Only the last episodes may point at someone, and the culprit is the only one they point at: a
# clue that points at a suspect early would solve the game at once.
POINTING_EPISODES = 2


def plan_problems(
    plan: Plan, suspects: int, episodes: int, unsafe_words: Callable[[str], list[str]]
) -> list[str]:
    """Why the plan cannot be played. Empty when it is fine. `unsafe_words` returns the words
    of a text that a small kid must not hear: the episodes module owns that list."""
    problems = []
    texts = [("title", plan.title), ("setting", plan.setting), ("reveal", plan.reveal)]
    for suspect in plan.suspects:
        texts.append((f"the name of {suspect.id}", suspect.name))
        texts.append((f"the description of {suspect.id}", suspect.description))
    texts.extend((f"the clue of episode {clue.episode}", clue.text) for clue in plan.clues)
    for name, text in texts:
        found = sorted(set(unsafe_words(text)))
        if found:
            problems.append(
                f"unsafe for small kids: {', '.join(found)} in {name}; leave the word out entirely"
            )
    for clue in plan.clues:
        if len(clue.text) > CLUE_MAX_CHARS:
            problems.append(
                f"the clue of episode {clue.episode} has {len(clue.text)} characters, "
                f"the limit is {CLUE_MAX_CHARS}"
            )
    ids = [suspect.id for suspect in plan.suspects]
    if len(ids) != suspects or len(set(ids)) != len(ids):
        problems.append(f"needs {suspects} suspects with different ids")
    if plan.culprit_id not in ids:
        problems.append("the culprit is not a suspect")
    if sorted(clue.episode for clue in plan.clues) != list(range(1, episodes + 1)):
        problems.append(f"needs one clue for each of the {episodes} episodes")
    if any(clue.suspect_id not in ids for clue in plan.clues):
        problems.append("a clue names someone who is not a suspect")
    ruled_out = {clue.suspect_id for clue in plan.clues if not clue.points_at}
    if any(sid not in ruled_out for sid in ids if sid != plan.culprit_id):
        problems.append("an innocent suspect is never ruled out")
    if plan.culprit_id in ruled_out:
        problems.append("a clue rules out the culprit")
    # Small kids take a clue at its word, so a false trail would only confuse them.
    if any(clue.points_at and clue.suspect_id != plan.culprit_id for clue in plan.clues):
        problems.append("a clue points at an innocent suspect")
    first_pointing = episodes - POINTING_EPISODES + 1
    early = sorted(c.episode for c in plan.clues if c.points_at and c.episode < first_pointing)
    if early:
        problems.append(
            f"the clue of episode {early[0]} points at a suspect: only episodes "
            f"{first_pointing} to {episodes} may point, the earlier ones only rule suspects out"
        )
    return problems


FALLBACK_PLAN = Plan(
    title="The lost birthday balloon",
    setting="The big red balloon for Granny Hedgehog's birthday has floated out of the "
    "forest school. Someone took it, and the party is tomorrow.",
    suspects=(
        Suspect("s1", "Rosa the Rabbit", "fast and always in a hurry"),
        Suspect("s2", "Milo the Magpie", "loves shiny and colorful things"),
        Suspect("s3", "Toby the Tortoise", "slow, calm and very honest"),
    ),
    culprit_id="s2",
    clues=(
        Clue(1, "Rosa was at the carrot market all morning, many saw her.", "s1", False),
        Clue(2, "Toby is far too slow to catch a flying balloon.", "s3", False),
        Clue(3, "Rosa has no wings, so she could not reach the high branch.", "s1", False),
        Clue(4, "A black and white feather from Milo lies where the balloon was tied.", "s2", True),
        Clue(5, "A red ribbon hangs in Milo's nest in the tall tree.", "s2", True),
    ),
    reveal="Milo the Magpie took the balloon because it was the shiniest thing he had ever "
    "seen. He kept it safe in his nest and is glad to bring it to the party.",
)


_PICNIC_PLAN = Plan(
    title="The missing picnic cake",
    setting="The lemon cake for the big meadow picnic was left on the old stone table. "
    "Now only a few crumbs are there, and everyone is hungry.",
    suspects=(
        Suspect("s1", "Pip the Mouse", "tiny, quick and always nibbling"),
        Suspect("s2", "Bella the Bear", "big, sleepy and very fond of sweet things"),
        Suspect("s3", "Otto the Owl", "wise, quiet and awake all night"),
    ),
    culprit_id="s2",
    clues=(
        Clue(1, "Pip is so small that he cannot lift a whole cake.", "s1", False),
        Clue(2, "Otto was busy counting stars on the hill all evening.", "s3", False),
        Clue(3, "Pip was seen at the berry bush, far from the table.", "s1", False),
        Clue(4, "Big paw prints, just like Bella's, lead away from the table.", "s2", True),
        Clue(5, "Bella has a little lemon cream on her nose and a happy smile.", "s2", True),
    ),
    reveal="Bella the Bear was so hungry that she ate the cake in her sleep. She is sorry, "
    "and she helps everybody bake a new one for the picnic.",
)

_SCARF_PLAN = Plan(
    title="The runaway scarf",
    setting="The long blue scarf of Grandpa Goat hung on the garden fence. This morning "
    "it was gone, and the wind is cold today.",
    suspects=(
        Suspect("s1", "Fenny the Fox", "clever, curious and fond of games"),
        Suspect("s2", "Daisy the Duck", "cheerful and splashes in every puddle"),
        Suspect("s3", "Hugo the Hamster", "round, shy and a great collector"),
    ),
    culprit_id="s3",
    clues=(
        Clue(1, "Fenny spent the whole morning at the pond with her friends.", "s1", False),
        Clue(2, "Daisy was at the bakery, and the baker saw her there.", "s2", False),
        Clue(3, "Fenny cannot fit through the tiny hole in the fence.", "s1", False),
        Clue(4, "Soft blue threads lead to the little hole where Hugo lives.", "s3", True),
        Clue(5, "Hugo has a cozy new blue pillow in his burrow.", "s3", True),
    ),
    reveal="Hugo the Hamster wanted a soft bed for the winter and took the scarf by "
    "mistake. He gives it back with a hug and a thank you.",
)

FALLBACK_PLANS = (FALLBACK_PLAN, _PICNIC_PLAN, _SCARF_PLAN)


def fallback_plan(case_number: int) -> Plan:
    """The built-in plan of a case, so a family that falls back twice does not play the same
    case again. They cycle after the last one."""
    return FALLBACK_PLANS[(case_number - 1) % len(FALLBACK_PLANS)]


def can_move(current: CaseStatus, to: CaseStatus) -> bool:
    return to in _NEXT_STATUSES.get(current, set())


def rank_for(attempts: int) -> Rank:
    if attempts <= 1:
        return Rank.FIRST_TRY
    if attempts == 2:
        return Rank.SECOND_TRY
    return Rank.LATER


def visible_clues(case: Case) -> tuple[Clue, ...]:
    """Only the clues of episodes already played: the rest would give the case away."""
    if case.plan is None:
        return ()
    return tuple(clue for clue in case.plan.clues if clue.episode <= case.played_episodes)


def with_episode_played(case: Case, number: int, episodes: int) -> Case:
    """Safe to apply twice and in any order: the count never goes down. After the last episode
    the kids may accuse."""
    played = max(case.played_episodes, min(number, episodes))
    status = case.status
    if played == episodes and case.status == CaseStatus.ACTIVE:
        status = CaseStatus.ACCUSING
    return replace(case, played_episodes=played, status=status)


@dataclass(frozen=True)
class AccusationResult:
    case: Case
    correct: bool


def accuse(case: Case, suspect_id: str, now: datetime) -> AccusationResult:
    """The caller has checked the status and that the suspect exists. A wrong suspect only adds
    an attempt: there is no losing."""
    assert case.plan is not None
    attempts = case.accusation_attempts + 1
    if suspect_id != case.plan.culprit_id:
        return AccusationResult(replace(case, accusation_attempts=attempts), correct=False)
    solved = replace(
        case,
        accusation_attempts=attempts,
        status=CaseStatus.SOLVED,
        rank=rank_for(attempts),
        solved_at=now,
    )
    return AccusationResult(solved, correct=True)
