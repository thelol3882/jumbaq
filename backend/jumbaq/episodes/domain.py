"""An episode of a case: one evening of reading aloud with a riddle about the home.

The model writes it and these rules check it, because a parent reads it aloud to small kids
who then go and look at something in the home. The answer slot comes from ai.public through
the caller, so this module stays free of the database.
"""

import random
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


class EveningStep(StrEnum):
    ANSWER = "answer"
    DECODE = "decode"
    STRIKE = "strike"
    DONE = "done"


class CipherLevel(StrEnum):
    COUNT = "count"
    NUMBER_CODE = "number_code"
    SHIFT = "shift"


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

# The oldest kid decides how hard the cipher is.
NUMBER_CODE_AGE = 6
SHIFT_AGE = 8
# Wrong picks in one step before the server shows the right answer and moves on.
MAX_ATTEMPTS = 2
SECRET_WORD_LENGTHS = range(4, 8)
GAP = "____"
STOPWORDS = frozenset({
    "the", "and", "was", "were", "with", "from", "that", "this", "they", "there", "where",
    "when", "what", "have", "been", "into", "very", "some", "their", "then", "than", "them",
    "these", "those", "would", "could", "should", "about", "after", "before", "because", "while",
    "which", "who", "whom", "whose", "does", "did", "has", "had", "are", "but", "for", "not",
    "you", "your", "our", "out", "off", "over", "under",
})  # fmt: skip
FALLBACK_WORDS = ("APPLE", "CLOUD", "PENCIL", "BANANA", "GARDEN")
FALLBACK_PHRASES = ("RED APPLE PIE", "BIG BLUE CLOUD", "SOFT GREEN PENCIL")
_LETTERS = re.compile(r"[A-Za-z]+")
_DIGITS = re.compile(r"\d{1,9}")


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
    # The evening steps, set when the episode is written. An older episode has none of them
    # and is played in one step, the answer.
    clue_suspect_id: str | None = None
    clue_points_at: bool | None = None
    cipher_level: CipherLevel | None = None
    cipher_secret: str | None = None
    cipher_decoys: tuple[str, ...] = ()


@dataclass(frozen=True)
class CipherPlan:
    level: CipherLevel
    secret: str | None
    decoys: tuple[str, ...]


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
    answered_at: datetime | None = None
    decode_attempts: int = 0
    decoded_at: datetime | None = None
    strike_attempts: int = 0

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


def has_evening_steps(payload: Payload) -> bool:
    return payload.cipher_level is not None and payload.clue_suspect_id is not None


def evening_step(episode: Episode) -> EveningStep:
    if episode.status == EpisodeStatus.PLAYED:
        return EveningStep.DONE
    if episode.answered_at is None:
        return EveningStep.ANSWER
    if episode.decoded_at is None:
        return EveningStep.DECODE
    return EveningStep.STRIKE


def with_evening_steps(
    payload: Payload, suspect_id: str, points_at: bool, plan: CipherPlan
) -> Payload:
    return replace(
        payload,
        clue_suspect_id=suspect_id,
        clue_points_at=points_at,
        cipher_level=plan.level,
        cipher_secret=plan.secret,
        cipher_decoys=plan.decoys,
    )


def cipher_level_for(oldest_age: int) -> CipherLevel:
    if oldest_age < NUMBER_CODE_AGE:
        return CipherLevel.COUNT
    if oldest_age < SHIFT_AGE:
        return CipherLevel.NUMBER_CODE
    return CipherLevel.SHIFT


def _clue_words(clue: str) -> list[str]:
    return [word.upper() for word in _LETTERS.findall(clue)]


def _secret_index(words: list[str]) -> int | None:
    """The longest word of 4 to 7 letters that is not a stopword; the first one on a tie."""
    best: int | None = None
    for index, word in enumerate(words):
        if len(word) not in SECRET_WORD_LENGTHS or word.lower() in STOPWORDS:
            continue
        if best is None or len(word) > len(words[best]):
            best = index
    return best


def _fill(found: list[str], fallback: tuple[str, ...], secret: str) -> tuple[str, ...]:
    chosen = list(dict.fromkeys(text for text in found if text != secret))[:2]
    for text in fallback:
        if len(chosen) == 2:
            break
        if text != secret and text not in chosen:
            chosen.append(text)
    return tuple(chosen)


def plan_cipher(clue: str, oldest_age: int) -> CipherPlan:
    """The level for the kids' age and the secret and decoys from the plan's clue. A clue with
    no word that works gives the level count, which needs none."""
    level = cipher_level_for(oldest_age)
    words = _clue_words(clue)
    index = _secret_index(words)
    if level == CipherLevel.NUMBER_CODE and index is not None:
        secret = words[index]
        others = [
            word
            for i, word in enumerate(words)
            if i != index and len(word) >= 3 and word.lower() not in STOPWORDS
        ]
        return CipherPlan(level, secret, _fill(others, FALLBACK_WORDS, secret))
    if level == CipherLevel.SHIFT and index is not None and len(words) >= 3:
        start = min(index, len(words) - 3)
        secret = " ".join(words[start : start + 3])
        starts = range(len(words) - 2)
        # Windows that share no word with the secret come first.
        ordered = sorted(starts, key=lambda s: abs(s - start) < 3)
        windows = [" ".join(words[s : s + 3]) for s in ordered if s != start]
        return CipherPlan(level, secret, _fill(windows, FALLBACK_PHRASES, secret))
    return CipherPlan(CipherLevel.COUNT, None, ())


def cipher_key(answer: str) -> int:
    """The number in the answer, else how many letters it has. At least 1."""
    digits = _DIGITS.search(answer)
    number = int(digits.group(0)) if digits else sum(char.isalpha() for char in answer)
    return max(number, 1)


def number_code(key: int, secret: str) -> str:
    """Each letter is its place in the alphabet plus a start that depends on the key: with a
    start of 3, A is 3, B is 4. Letters are joined by "-" and words by " / "."""
    start = (key - 1) % 9 + 1
    return " / ".join(
        "-".join(str(ord(char) - ord("A") + start) for char in word) for word in secret.split()
    )


def shift_text(key: int, secret: str) -> str:
    shift = (key - 1) % 25 + 1
    return "".join(
        chr((ord(char) - ord("A") + shift) % 26 + ord("A")) if char != " " else char
        for char in secret
    )


def count_target(key: int) -> int:
    return (key - 1) % 10 + 1


def clue_with_gap(clue: str, secret: str) -> str:
    """The clue with the secret word or words hidden, so the kids see the rest."""
    parts = [re.escape(word) for word in secret.split()]
    pattern = re.compile(r"\b" + r"[^A-Za-z]+".join(parts) + r"\b", re.I)
    return pattern.sub(GAP, clue)


def same_word(guess: str, secret: str) -> bool:
    return " ".join(guess.upper().split()) == secret


def shuffled_options(secret: str, decoys: tuple[str, ...], seed: uuid.UUID) -> list[str]:
    """The same order every time for the same episode, so a reload keeps the buttons in place."""
    options = [secret, *decoys]
    random.Random(seed.int).shuffle(options)
    return options
