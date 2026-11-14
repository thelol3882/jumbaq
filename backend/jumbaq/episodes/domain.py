"""An episode of a case: one evening of reading aloud with a riddle about the home.

The model writes it and these rules check it, because a parent reads it aloud to small kids
who then go and look at something in the home. The answer slot comes from ai.public through
the caller, so this module stays free of the database.
"""

import re
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum


class EpisodeStatus(StrEnum):
    REQUESTED = "requested"
    GENERATING = "generating"
    READY = "ready"
    PLAYED = "played"
    FAILED = "failed"


# Things a small child must never be sent to or asked to do, matched as whole words in any case.
# Plurals are listed on their own. One list, so it is easy to read and to extend. It is English:
# a story in another language is checked by the prompt's rules only.
BANNED_WORDS = (
    "knife", "knives", "scissors", "blade", "medicine", "pill", "pills", "tablet", "stove",
    "oven", "hob", "matches", "matchbox", "lighter", "outlet", "socket", "plug", "wire",
    "street", "road", "outside", "leave the home", "leave the house", "leave home",
    "front door", "climb", "climbing", "balcony", "window", "stranger", "strangers",
)  # fmt: skip
_BANNED = re.compile(r"\b(" + "|".join(re.escape(word) for word in BANNED_WORDS) + r")\b", re.I)

ANSWER_MAX_LENGTH = 60
# The youngest kid decides: under 6, the texts are shorter.
YOUNG_AGE = 6
PARAGRAPH_LIMIT = {False: 600, True: 400}
SHORT_TEXT_LIMIT = {False: 400, True: 250}
MAX_PARAGRAPHS = 6


@dataclass(frozen=True)
class Riddle:
    text: str
    target_object: str
    answer_type: str
    parent_note: str


@dataclass(frozen=True)
class Payload:
    recap: str
    read_aloud: tuple[str, ...]
    riddle: Riddle
    hint: str
    fallback_riddle: Riddle
    resolution_template: str
    case_clue: str
    cliffhanger: str


@dataclass(frozen=True)
class Episode:
    id: uuid.UUID
    family_id: uuid.UUID
    case_id: uuid.UUID
    case_number: int
    number: int
    status: EpisodeStatus
    payload: Payload | None
    answer: str | None
    resolution: str | None
    available_at: datetime | None
    played_at: datetime | None
    is_fallback: bool
    used_fallback_riddle: bool

    @property
    def riddle(self) -> Riddle | None:
        """The riddle in use: the fallback one after a swap."""
        if self.payload is None:
            return None
        return self.payload.fallback_riddle if self.used_fallback_riddle else self.payload.riddle


def _short_texts(payload: Payload) -> list[str]:
    riddles = (payload.riddle, payload.fallback_riddle)
    return [
        payload.recap,
        payload.hint,
        payload.resolution_template,
        payload.case_clue,
        payload.cliffhanger,
        *(text for riddle in riddles for text in (riddle.text, riddle.parent_note)),
    ]


def banned_words(text: str) -> list[str]:
    return [found.group(0).lower() for found in _BANNED.finditer(text)]


def draft_problems(
    payload: Payload, objects: tuple[str, ...], youngest_age: int, slot: str
) -> list[str]:
    """Why the episode cannot be read to the kids. Empty when it is fine."""
    problems = []
    for name, riddle in (("riddle", payload.riddle), ("fallback riddle", payload.fallback_riddle)):
        if riddle.target_object not in objects:
            problems.append(f"the {name} points at {riddle.target_object!r}, not in the home")
    if payload.riddle.target_object == payload.fallback_riddle.target_object:
        problems.append("both riddles point at the same object")
    if payload.resolution_template.count(slot) != 1:
        problems.append(f"the resolution needs {slot} exactly once")
    young = youngest_age < YOUNG_AGE
    if not payload.read_aloud or len(payload.read_aloud) > MAX_PARAGRAPHS:
        problems.append(f"needs 1 to {MAX_PARAGRAPHS} paragraphs")
    if any(len(text) > PARAGRAPH_LIMIT[young] for text in payload.read_aloud):
        problems.append("a paragraph is too long for the youngest kid")
    if any(len(text) > SHORT_TEXT_LIMIT[young] for text in _short_texts(payload)):
        problems.append("a text is too long for the youngest kid")
    texts = (*payload.read_aloud, *_short_texts(payload))
    found = sorted({word for text in texts for word in banned_words(text)})
    if found:
        problems.append(f"unsafe for small kids: {', '.join(found)}")
    return problems


def with_plan_clue(payload: Payload, clue: str) -> Payload:
    """The clue the family sees is always the plan's, never the model's wording of it."""
    return replace(payload, case_clue=clue)


def clean_answer(raw: str) -> str:
    """One short line: the answer goes into the story the parent reads aloud."""
    return " ".join(raw.split())[:ANSWER_MAX_LENGTH].strip()


def resolution(template: str, answer: str, slot: str) -> str:
    # A plain replace: the model's text may hold other braces, which str.format would break on.
    return template.replace(slot, answer)


def available_after(played_at: datetime, gap_hours: int) -> datetime:
    return played_at + timedelta(hours=gap_hours)


def is_open(episode: Episode, now: datetime) -> bool:
    return episode.available_at is not None and episode.available_at <= now


def built_in_payload(
    title: str,
    clue: str,
    objects: tuple[str, ...],
    number: int,
    last: bool,
    slot: str,
    model_riddle: Riddle | None = None,
) -> Payload:
    """A plain episode for when the model fails: always safe and always playable. A safe
    riddle the model wrote for this home is kept."""
    first = model_riddle or _built_in_riddle(objects[(number - 1) % len(objects)])
    others = [obj for obj in objects if obj != first.target_object] or list(objects)
    second = _built_in_riddle(others[number % len(others)])
    ending = (
        "Now think about all the clues together. Who do you think did it?"
        if last
        else "But the case is not solved yet. More clues are waiting for tomorrow."
    )
    return Payload(
        recap=f"Welcome back to {title}, detectives.",
        read_aloud=(
            "The detectives open their notebook and read the notes once more.",
            "Something in this home is hiding a secret code. Can you find it?",
        ),
        riddle=first,
        hint="Walk slowly through the home and look carefully.",
        fallback_riddle=second,
        resolution_template=f"You found it: {slot}. Great detective work!",
        case_clue=clue,
        cliffhanger=ending,
    )


def _built_in_riddle(target: str) -> Riddle:
    return Riddle(
        text=f"Find the {target}. What colour is it?",
        target_object=target,
        answer_type="colour",
        parent_note=f"Help the kids find the {target}. Any colour they say is right.",
    )


def is_safe_riddle(riddle: Riddle, objects: tuple[str, ...], youngest_age: int) -> bool:
    young = youngest_age < YOUNG_AGE
    texts = (riddle.text, riddle.parent_note)
    return (
        riddle.target_object in objects
        and not any(banned_words(text) for text in texts)
        and all(len(text) <= SHORT_TEXT_LIMIT[young] for text in texts)
    )
