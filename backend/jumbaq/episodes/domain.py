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
# Every entry also matches its regular forms (see _forms), so only what is irregular is written
# out (knives, left the house). One list, easy to read and to extend. The stories are English
# only, so the words are too.
BANNED_WORDS = (
    "knife", "knives", "scissors", "blade", "medicine", "pill", "tablet", "stove", "oven", "hob",
    "matches", "matchbox", "lighter", "outlet", "socket", "plug", "wire", "street", "road",
    "outside", "leave the home", "leave the house", "leave home", "left the home",
    "left the house", "left home", "front door", "climb", "balcony", "window", "stranger",
)  # fmt: skip


def _forms(word: str) -> str:
    """The word and its regular forms as a regex: s, es, ed, ing, er, ers, y to ies and ied, a
    dropped final e (wiring) and a doubled final consonant (plugged)."""
    base = re.escape(word)
    if word.endswith("y"):
        return rf"(?:{base}(?:s|ing|er)?|{re.escape(word[:-1])}(?:ies|ied))"
    if word.endswith("e"):
        return rf"(?:{base}(?:s|d|r|rs)?|{re.escape(word[:-1])}ing)"
    last = re.escape(word[-1])
    return rf"(?:{base}(?:s|es|ed|ing|er|ers)?|{base}{last}(?:ed|ing|er|ers))"


def _banned_pattern(entry: str) -> str:
    # A phrase takes the forms on its first and last word, and any run of spaces between words.
    words = entry.split()
    if len(words) == 1:
        return _forms(words[0])
    middle = [re.escape(word) for word in words[1:-1]]
    return r"\s+".join([_forms(words[0]), *middle, _forms(words[-1])])


_BANNED = re.compile(
    r"\b(?:" + "|".join(_banned_pattern(entry) for entry in BANNED_WORDS) + r")\b", re.I
)

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
# Little words a secret phrase never starts or ends on, and never counts as a word to hide.
FILLER_WORDS = STOPWORDS | frozenset({
    "a", "an", "of", "to", "in", "on", "at", "is", "it", "as", "by", "or", "if", "so", "up",
    "he", "she", "his", "her", "its", "my", "me", "we", "us", "be", "am", "no", "do", "go",
    "all", "any", "can", "one", "two", "too", "only", "just", "also", "ever", "each",
})  # fmt: skip
# Wrong buttons of the number code when the other clues have too few words. Kid words of 4 to 7
# letters, so the length of the right button does not give it away.
KID_WORDS = (
    "APPLE", "CLOUD", "PENCIL", "BANANA", "GARDEN", "MONKEY", "ROCKET", "PUPPY", "BUTTER",
    "CANDLE", "BASKET", "PIRATE", "TIGER", "WINTER", "COOKIE", "JUMPER", "LEMON", "FOREST",
    "BUTTON", "PILLOW", "SPIDER", "DONKEY", "TRAIN", "ISLAND", "BOTTLE", "SUMMER", "TOWER",
    "ORANGE", "CARROT", "MAGNET", "WAGON", "PARROT", "DRAGON", "BRIDGE", "TEAPOT", "MARBLE",
)  # fmt: skip
# The same for the shift level, by number of words.
KID_PHRASES = {
    2: ("RED APPLE", "BLUE CLOUD", "GREEN PENCIL", "YELLOW DUCK", "OLD TREE", "APPLE CAKE",
        "SOFT PILLOW", "TALL TOWER"),
    3: ("RED APPLE PIE", "BIG BLUE CLOUD", "SOFT GREEN PENCIL", "LITTLE YELLOW DUCK",
        "TALL OLD TREE", "WARM APPLE CAKE", "FAST PAPER BOAT", "SMALL BROWN PUPPY"),
}  # fmt: skip
_APOSTROPHES = re.compile("['" + chr(0x2019) + "]")
_WORD = re.compile(r"[A-Za-z]+(?:['\u2019][A-Za-z]+)*")
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


def _named_short_texts(payload: Payload) -> list[tuple[str, str]]:
    # The names are the fields of the model's answer, so a refusal tells it what to fix.
    return [
        ("recap", payload.recap),
        ("hint", payload.hint),
        ("resolution_template", payload.resolution_template),
        ("case_clue", payload.case_clue),
        ("cliffhanger", payload.cliffhanger),
        ("riddle.text", payload.riddle.text),
        ("riddle.parent_note", payload.riddle.parent_note),
        ("fallback_riddle.text", payload.fallback_riddle.text),
        ("fallback_riddle.parent_note", payload.fallback_riddle.parent_note),
    ]


def text_limits(youngest_age: int) -> tuple[int, int]:
    """The longest read-aloud paragraph and the longest short text, in characters."""
    young = youngest_age < YOUNG_AGE
    return PARAGRAPH_LIMIT[young], SHORT_TEXT_LIMIT[young]


def banned_words(text: str) -> list[str]:
    return [" ".join(found.group(0).lower().split()) for found in _BANNED.finditer(text)]


def draft_problems(
    payload: Payload,
    objects: tuple[str, ...],
    youngest_age: int,
    slot: str,
    secret: str | None = None,
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
    paragraph_max, short_max = PARAGRAPH_LIMIT[young], SHORT_TEXT_LIMIT[young]
    for index, text in enumerate(payload.read_aloud, start=1):
        if len(text) > paragraph_max:
            problems.append(
                f"a read_aloud paragraph is too long: paragraph {index} has {len(text)} "
                f"characters, the limit is {paragraph_max}"
            )
    named = [(f"read_aloud paragraph {i}", text) for i, text in enumerate(payload.read_aloud, 1)]
    # The clue is the plan's text, checked when the case was planned: the episode cannot fix it.
    own = [(name, text) for name, text in _named_short_texts(payload) if name != "case_clue"]
    named += own
    for name, text in own:
        if len(text) > short_max:
            problems.append(
                f"a text is too long: {name} has {len(text)} characters, the limit is {short_max}"
            )
    for name, text in named:
        found = sorted(set(banned_words(text)))
        if found:
            problems.append(
                f"unsafe for small kids: {', '.join(found)} in {name}; leave the word out entirely"
            )
    hidden = set(secret_words(secret))
    for name, text in named:
        given_away = sorted({word for word in _spoken_words(text) if word in hidden})
        if given_away:
            problems.append(
                f"gives the clue away: {', '.join(word.lower() for word in given_away)} in "
                f"{name} is a word the kids decode later; tell the story without it"
            )
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
    riddle the model wrote for this home is kept. Only objects with safe names are used; a home
    with none gets the generic riddles, which need nothing from the home."""
    safe = safe_objects(objects)
    first = model_riddle or (
        _built_in_riddle(safe[(number - 1) % len(safe)]) if safe else _GENERIC_RIDDLES[0]
    )
    others = [obj for obj in safe if obj != first.target_object] or list(safe)
    second = _built_in_riddle(others[number % len(others)]) if others else _GENERIC_RIDDLES[1]
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


def safe_objects(objects: tuple[str, ...]) -> tuple[str, ...]:
    """The objects whose names pass the unsafe-words check: only these go to the model and to
    the built-in riddles."""
    return tuple(obj for obj in objects if not banned_words(obj))


# For a home with no safe object. They are not in the home's list, so nothing checks their
# target: it only has to be safe text, which a fixed sentence is. Any room has something soft
# and something round.
_GENERIC_RIDDLES = (
    Riddle(
        text="Look around the room you are in and find something soft. What colour is it?",
        target_object="something soft in the room",
        answer_type="colour",
        parent_note="Help the kids find something soft nearby. Any colour they say is right.",
    ),
    Riddle(
        text="Look around the room you are in and find something round. What colour is it?",
        target_object="something round in the room",
        answer_type="colour",
        parent_note="Help the kids find something round nearby. Any colour they say is right.",
    ),
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
        riddle.target_object in safe_objects(objects)
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


def _tokens(text: str) -> list[tuple[str, int, int]]:
    """The words of a text as (letters in upper case, start, end). "Grandma's" is one word,
    GRANDMAS: a lone "S" would turn up in the cipher."""
    return [
        (re.sub(r"['\u2019]", "", found.group(0)).upper(), found.start(), found.end())
        for found in _WORD.finditer(text)
    ]


def _spoken_words(text: str) -> set[str]:
    """The words of a text, and the word before a possessive: "feather's" says FEATHER."""
    words = set()
    for found in _WORD.finditer(text):
        raw = found.group(0).upper()
        words.add(_APOSTROPHES.sub("", raw))
        if raw.endswith(("'S", chr(0x2019) + "S")):
            words.add(raw[:-2])
    return words


def _clue_words(clue: str) -> list[str]:
    return [word for word, _, _ in _tokens(clue)]


def _secret_index(words: list[str]) -> int | None:
    """The longest word of 4 to 7 letters that is not a stopword; the first one on a tie."""
    best: int | None = None
    for index, word in enumerate(words):
        if len(word) not in SECRET_WORD_LENGTHS or word.lower() in STOPWORDS:
            continue
        if best is None or len(word) > len(words[best]):
            best = index
    return best


def _window(words: list[str], best: int, size: int, around: bool) -> int | None:
    """Where a window of `size` words starts: it does not start or end on a filler word. With
    `around` it holds the best word. The one with the fewest filler words inside wins, then the
    one with the best word nearest its middle; the first on a tie."""
    scored = []
    for start in range(len(words) - size + 1):
        part = words[start : start + size]
        if part[0].lower() in FILLER_WORDS or part[-1].lower() in FILLER_WORDS:
            continue
        inside = sum(word.lower() in FILLER_WORDS for word in part)
        middle = abs(best - (start + (size - 1) / 2))
        if around and not start <= best < start + size:
            continue
        scored.append((inside, middle, start))
    return min(scored)[2] if scored else None


def _length_order(texts: list[str], like: str) -> list[str]:
    """Distinct texts, the ones with the most letters like `like` first."""
    target = len(like.replace(" ", ""))
    return sorted(dict.fromkeys(texts), key=lambda text: abs(len(text.replace(" ", "")) - target))


def _decoys(
    candidates: list[str], fallback: tuple[str, ...], secret: str, seen: set[str]
) -> tuple[str, ...]:
    """Two wrong buttons. None of their words is in the clue, because the kids would see that
    it is not the missing one."""
    chosen: list[str] = []
    for text in _length_order(candidates, secret) + _length_order(list(fallback), secret):
        if text == secret or text in chosen or any(word in seen for word in text.split()):
            continue
        chosen.append(text)
        if len(chosen) == 2:
            break
    return tuple(chosen)


def plan_cipher(clue: str, oldest_age: int, other_clues: tuple[str, ...] = ()) -> CipherPlan:
    """The level for the kids' age and the secret and decoys from the plan's clue. The decoys
    come from the case's other clues, then from a list of kid words, and none of them is in
    this clue. A clue with no secret that works gives the level count, which needs none."""
    level = cipher_level_for(oldest_age)
    words = _clue_words(clue)
    index = _secret_index(words)
    if index is None:
        return CipherPlan(CipherLevel.COUNT, None, ())
    seen = set(words)
    others = [_clue_words(other) for other in other_clues]
    if level == CipherLevel.NUMBER_CODE:
        secret = words[index]
        found = [
            word
            for other in others
            for word in other
            if len(word) in SECRET_WORD_LENGTHS and word.lower() not in FILLER_WORDS
        ]
        return CipherPlan(level, secret, _decoys(found, KID_WORDS, secret, seen))
    if level == CipherLevel.SHIFT:
        # Three words around the best word, else two, and only then a window elsewhere.
        for around, size in ((True, 3), (True, 2), (False, 3), (False, 2)):
            start = _window(words, index, size, around)
            if start is None:
                continue
            secret = " ".join(words[start : start + size])
            found = [
                " ".join(other[s : s + size])
                for other in others
                for s in range(len(other) - size + 1)
                if other[s].lower() not in FILLER_WORDS
                and other[s + size - 1].lower() not in FILLER_WORDS
            ]
            return CipherPlan(level, secret, _decoys(found, KID_PHRASES[size], secret, seen))
    return CipherPlan(CipherLevel.COUNT, None, ())


def secret_words(secret: str | None) -> tuple[str, ...]:
    """The words of the secret that the story must not use before the kids decode the clue:
    little filler words in a phrase do not count."""
    return tuple(word for word in (secret or "").split() if word.lower() not in FILLER_WORDS)


def cipher_key(answer: str) -> int:
    """The number in the answer, else how many letters it has. At least 1."""
    digits = _DIGITS.search(answer)
    number = int(digits.group(0)) if digits else sum(char.isalpha() for char in answer)
    return max(number, 1)


def number_start(key: int) -> int:
    """The number of the letter A in the number code."""
    return (key - 1) % 9 + 1


def shift_amount(key: int) -> int:
    return (key - 1) % 25 + 1


def number_code(key: int, secret: str) -> str:
    """Each letter is its place in the alphabet plus a start that depends on the key: with a
    start of 3, A is 3, B is 4. Letters are joined by "-" and words by " / "."""
    start = number_start(key)
    return " / ".join(
        "-".join(str(ord(char) - ord("A") + start) for char in word) for word in secret.split()
    )


def shift_text(key: int, secret: str) -> str:
    shift = shift_amount(key)
    return "".join(
        chr((ord(char) - ord("A") + shift) % 26 + ord("A")) if char != " " else char
        for char in secret
    )


def count_target(key: int) -> int:
    return (key - 1) % 10 + 1


def clue_with_gap(clue: str, secret: str) -> str:
    """The clue with the secret word or words hidden, so the kids see the rest. The words are
    matched with apostrophes ignored, and the text of the clue stays as it was written."""
    wanted = secret.split()
    tokens = _tokens(clue)
    result: list[str] = []
    done = 0
    index = 0
    while index < len(tokens):
        run = [word for word, _, _ in tokens[index : index + len(wanted)]]
        if run == wanted:
            result.append(clue[done : tokens[index][1]] + GAP)
            done = tokens[index + len(wanted) - 1][2]
            index += len(wanted)
        else:
            index += 1
    return "".join(result) + clue[done:]


def same_word(guess: str, secret: str) -> bool:
    return " ".join(guess.upper().split()) == secret


def sorted_options(secret: str, decoys: tuple[str, ...]) -> list[str]:
    """In alphabetical order: any order that depends on the episode could be worked out."""
    return sorted([secret, *decoys])
