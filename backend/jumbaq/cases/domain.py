"""A detective case of 5 episodes. Case 1 is free.

The plan is fixed when the case is planned: three suspects, one culprit and one clue per
episode, with one false trail that a later clue clears. The model writes it, these rules check
it, and a built-in plan stands in when the model fails twice.

The numbers of suspects and episodes come from ai.public through the caller: importing it here
would pull the database into the domain. So does the check for words unsafe for small kids,
which comes from episodes.public.
"""

import hashlib
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
    # The texts of the clues of earlier episodes. Only the episode's cipher uses them, for wrong
    # buttons; a later clue's words on a button would hint at an evening not played yet.
    earlier_clues: tuple[str, ...] = ()


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


@dataclass(frozen=True)
class World:
    """Where a case happens and what may go missing there."""

    place: str
    things: tuple[str, ...]


# Code picks the world, not the model: left alone, the model writes the same bakery every time.
WORLDS = (
    World("a lighthouse by the sea", ("the brass bell", "the golden lantern", "the sea map")),
    World("a space station", ("the glowing moon rock", "the star map", "the robot's silver key")),
    World("a forest school", ("the big storybook", "the rainbow paint set", "the school drum")),
    World("a little train", ("the red whistle", "the picnic basket", "the conductor's hat")),
    World("a farm", ("the blue ribbon", "the basket of eggs", "the big dinner bell")),
    World("a toy shop", ("the wind-up music box", "the shiny top hat", "the tiny drum")),
    World("a zoo at night", ("the golden whistle", "the keeper's lantern", "the big banana")),
    World("a castle kitchen", ("the royal pie", "the silver spoon", "the jar of cinnamon")),
    World("a pirate ship", ("the treasure map", "the parrot's bell", "the captain's hat")),
    World("a snowy village", ("the star for the tree", "the sled bell", "the big scarf")),
    World("a museum", ("the little dinosaur bone", "the painted vase", "the glass marble")),
    World("a circus", ("the juggling balls", "the clown's red nose", "the magic wand")),
    World("a beach town", ("the giant sandcastle flag", "the ice cream bell", "the kite")),
    World("a mountain hut", ("the warm blanket", "the wooden flute", "the trail map")),
)


def world_for(case_id: uuid.UUID) -> tuple[str, str]:
    """The world and the missing thing of a case. A stable hash of the id, so a retry of the
    planning keeps the same choice and different cases of a family differ."""
    digest = int.from_bytes(hashlib.sha256(case_id.bytes).digest()[:8], "big")
    world = WORLDS[digest % len(WORLDS)]
    return world.place, world.things[digest // len(WORLDS) % len(world.things)]


# Built-in plans for when the model fails: each follows every rule of plan_problems, in a world
# of its own, so a family that falls back twice does not get the same case twice.
FALLBACK_PLANS = (
    Plan(
        title="The bell of Pebble Lighthouse",
        setting="The little brass bell of Pebble Lighthouse is gone from its hook. Without it "
        "the fishing boats cannot hear the lighthouse in the morning fog.",
        suspects=(
            Suspect("s1", "Gus the Gull", "wants the bell to call his chicks home for supper"),
            Suspect("s2", "Mabel the Mouse", "wants the bell for the music show on her stage"),
            Suspect("s3", "Carlo the Crab", "wants the bell as a cozy bed for his baby shells"),
        ),
        culprit_id="s3",
        clues=(
            Clue(1, "Gus left wet, webbed footprints right under the empty bell hook.", "s1", True),
            Clue(
                2,
                "Mabel was rehearsing her show on the rocks, and the whole beach clapped.",
                "s2",
                False,
            ),
            Clue(
                3,
                "Gus walks the beach every dawn, so those footprints are just from his stroll.",
                "s1",
                False,
            ),
            Clue(
                4,
                "Tiny claw marks lead from the bell hook down to Carlo's tide pool.",
                "s3",
                True,
            ),
            Clue(
                5,
                "A soft ringing comes from Carlo's shell house under the big rock.",
                "s3",
                True,
            ),
        ),
        reveal="Carlo the Crab took the bell to keep his baby shells warm and cozy, and he did "
        "not know the boats needed it. Gus only walked by at dawn. Carlo hung the bell back on "
        "its hook, and the boats heard the lighthouse again.",
    ),
    Plan(
        title="The moon rock of Star Station Nine",
        setting="The glowing moon rock has vanished from its stand in the big hall of Star "
        "Station Nine, and the visitors arrive soon.",
        suspects=(
            Suspect("s1", "Pip the Robot", "wants the moon rock to light up his new workshop"),
            Suspect("s2", "Zuzu the Alien", "wants the moon rock to remind her of her home planet"),
            Suspect("s3", "Captain Luna", "wants the moon rock to show the visitors on her tour"),
        ),
        culprit_id="s1",
        clues=(
            Clue(
                1,
                "Zuzu was in the garden dome all morning, picking space tomatoes with friends.",
                "s2",
                False,
            ),
            Clue(
                2,
                "Captain Luna's glove lies right next to the empty moon rock stand.",
                "s3",
                True,
            ),
            Clue(
                3,
                "Captain Luna dropped that glove earlier, while she gave the morning tour.",
                "s3",
                False,
            ),
            Clue(4, "Shiny drops of oil lead from the stand to Pip's workshop door.", "s1", True),
            Clue(5, "A soft blue glow shines from under Pip's workshop door.", "s1", True),
        ),
        reveal="Pip the Robot took the moon rock because he wanted a glowing light for his "
        "workshop. He forgot to ask first. The drops of oil and the blue glow showed the way, "
        "and Pip happily put the moon rock back on its stand.",
    ),
    Plan(
        title="The star of Snowy Hollow",
        setting="The golden star that tops the big tree of Snowy Hollow has disappeared. The "
        "village lights the tree tonight.",
        suspects=(
            Suspect("s1", "Fern the Fox", "wants the star for the trophy of the sled race"),
            Suspect("s2", "Hank the Hare", "wants the star to shine over his snowy burrow"),
            Suspect("s3", "Dot the Deer", "wants the star for the snow lantern party"),
        ),
        culprit_id="s2",
        clues=(
            Clue(1, "Fern's gray fur is stuck on the empty hook where the star hung.", "s1", True),
            Clue(
                2,
                "Fern helped hang the tree lights yesterday, so her fur was left there then.",
                "s1",
                False,
            ),
            Clue(
                3,
                "Dot was building snow animals in the square, and the whole village saw her.",
                "s3",
                False,
            ),
            Clue(4, "Hank's tiny hare tracks hop from the tree to his snowy burrow.", "s2", True),
            Clue(5, "A golden glow shines out of Hank's burrow under the hill.", "s2", True),
        ),
        reveal="Hank the Hare took the star because it was the prettiest light he had ever "
        "seen, and he wanted it over his burrow. Fern's fur was only left from hanging the "
        "lights. Hank brought the star back, and the village lit the tree.",
    ),
)

# Kept for code that wants one built-in plan.
FALLBACK_PLAN = FALLBACK_PLANS[0]


def fallback_plan(case_number: int) -> Plan:
    """The built-in plan for this case number: the cases of a family take turns."""
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
