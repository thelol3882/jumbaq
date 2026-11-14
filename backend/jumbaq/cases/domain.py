"""A detective case of 5 episodes. Case 1 is free.

The plan is fixed when the case is planned: three suspects, one culprit and one clue per
episode, with one false trail that a later clue clears. The model writes it, these rules check
it, and a built-in plan stands in when the model fails twice.

The numbers of suspects and episodes come from ai.public through the caller: importing it here
would pull the database into the domain. So does the check for words unsafe for small kids,
which comes from episodes.public.
"""

import re
import uuid
from collections.abc import Callable, Collection
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
# The last episodes point at the culprit and nobody else.
POINTING_EPISODES = 2
# The false trail lives in the first two evenings and a clue by the end of the third explains
# it away: the kids are never left with a wrong idea for long, and the evenings that point at
# the culprit stay clean.
TRAIL_LAST_EPISODE = 2
CLEARED_BY_EPISODE = 3
_NAME_FILLER = {"the", "a", "an", "of"}


def _names_suspect(clue: Clue, suspect: Suspect) -> bool:
    """The clue says the suspect's name or one word of it (Felix for Felix the Fox)."""
    words = [w for w in re.findall(r"[\w-]+", suspect.name.casefold()) if w not in _NAME_FILLER]
    text = set(re.findall(r"[\w-]+", clue.text.casefold().replace("'s", " ")))
    return any(word in text for word in words)


def plan_problems(
    plan: Plan,
    suspects: int,
    episodes: int,
    unsafe_words: Callable[[str], list[str]],
    used_titles: Collection[str] = (),
    used_names: Collection[str] = (),
) -> list[str]:
    """Why the plan cannot be played. Empty when it is fine. `unsafe_words` returns the words
    of a text that a small kid must not hear: the episodes module owns that list. `used_titles`
    and `used_names` are what the family played before: a case must not look like an old one.

    The shape of the clues: one innocent suspect looks bad in evening 1 or 2 (the false trail)
    and a clue by evening 3 explains it away; the other innocent is ruled out in evenings 1 to
    3; the last evenings point at the culprit, and nothing rules the culprit out."""
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
    if plan.title.casefold() in {title.casefold() for title in used_titles}:
        problems.append(f'the title "{plan.title}" was used by an earlier case of this family')
    taken = {name.casefold() for name in used_names}
    for suspect in plan.suspects:
        if suspect.name.casefold() in taken:
            problems.append(
                f'the suspect name "{suspect.name}" was used by an earlier case of this family'
            )
    ids = [suspect.id for suspect in plan.suspects]
    if len(ids) != suspects or len(set(ids)) != len(ids):
        problems.append(f"needs {suspects} suspects with different ids")
    if plan.culprit_id not in ids:
        problems.append("the culprit is not a suspect")
    if sorted(clue.episode for clue in plan.clues) != list(range(1, episodes + 1)):
        problems.append(f"needs one clue for each of the {episodes} episodes")
    named = {suspect.id: suspect for suspect in plan.suspects}
    if any(clue.suspect_id not in named for clue in plan.clues):
        problems.append("a clue names someone who is not a suspect")
    for clue in plan.clues:
        suspect = named.get(clue.suspect_id)
        if suspect is not None and not _names_suspect(clue, suspect):
            problems.append(
                f"the clue of episode {clue.episode} does not say the name of {suspect.name}"
            )
    if plan.culprit_id in named and all(clue.suspect_id in named for clue in plan.clues):
        problems.extend(_clue_shape_problems(plan, list(named), episodes))
    return problems


def _clue_shape_problems(plan: Plan, ids: list[str], episodes: int) -> list[str]:
    problems = []
    innocents = [sid for sid in ids if sid != plan.culprit_id]
    first_pointing = episodes - POINTING_EPISODES + 1
    if any(clue.suspect_id == plan.culprit_id and not clue.points_at for clue in plan.clues):
        problems.append("a clue rules out the culprit")
    for clue in plan.clues:
        points_at_culprit = clue.points_at and clue.suspect_id == plan.culprit_id
        if clue.episode >= first_pointing and not points_at_culprit:
            problems.append(
                f"the clue of episode {clue.episode} must point at the culprit: episodes "
                f"{first_pointing} to {episodes} point at the culprit and at nobody else"
            )
        if clue.episode < first_pointing and points_at_culprit:
            problems.append(
                f"the clue of episode {clue.episode} points at the culprit: only episodes "
                f"{first_pointing} to {episodes} may do that"
            )
    trails = [c for c in plan.clues if c.points_at and c.suspect_id in innocents]
    if len(trails) != 1:
        problems.append(
            "needs exactly one false trail (a clue that points at an innocent suspect), "
            f"found {len(trails)}"
        )
        return problems
    trail = trails[0]
    if trail.episode > TRAIL_LAST_EPISODE:
        problems.append(
            f"the false trail is in episode {trail.episode}: it belongs to episode 1 or "
            f"{TRAIL_LAST_EPISODE}"
        )
    cleared = any(
        not c.points_at
        and c.suspect_id == trail.suspect_id
        and trail.episode < c.episode <= CLEARED_BY_EPISODE
        for c in plan.clues
    )
    if not cleared:
        problems.append(
            f"no clue after the false trail and by episode {CLEARED_BY_EPISODE} rules out "
            f"{trail.suspect_id}, the suspect the false trail points at"
        )
    for sid in innocents:
        ruled_out = any(
            not c.points_at and c.suspect_id == sid and c.episode <= CLEARED_BY_EPISODE
            for c in plan.clues
        )
        if sid != trail.suspect_id and not ruled_out:
            problems.append(
                f"the innocent suspect {sid} is not ruled out in episodes 1 to {CLEARED_BY_EPISODE}"
            )
    return problems


FALLBACK_PLAN = Plan(
    title="The lost birthday balloon",
    setting="The big red balloon for Granny Hedgehog's birthday has floated out of the "
    "forest school. Someone took it, and the party is tomorrow.",
    suspects=(
        Suspect("s1", "Rosa the Rabbit", "wants the balloon to float over her garden party"),
        Suspect("s2", "Milo the Magpie", "wants the balloon to brighten his cozy nest"),
        Suspect("s3", "Toby the Tortoise", "wants the balloon for his own birthday picnic"),
    ),
    culprit_id="s2",
    clues=(
        Clue(1, "Rosa left muddy paw prints right where the balloon was tied.", "s1", True),
        Clue(2, "Toby was at the carrot market all morning, and many saw him.", "s3", False),
        Clue(3, "Rosa dug carrots all morning, so that is the mud on her paws.", "s1", False),
        Clue(4, "A black and white feather lies where Milo's balloon was tied.", "s2", True),
        Clue(5, "A red ribbon hangs from the tall tree where Milo nests.", "s2", True),
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
