"""An episode of a case: one evening of reading aloud with a riddle about the home.

The model writes it and these rules check it, because a parent reads it aloud to small kids
who then go and look at something in the home. The answer slot comes from ai.public through
the caller, so this module stays free of the database.
"""

import re
import uuid
from collections import Counter
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
    "knife", "knives", "scissor", "scissors", "blade", "medicine", "medication", "pill",
    "tablet", "stove", "oven", "hob", "matches", "matchbox", "matchstick", "lighter", "outlet",
    "socket", "plug", "wire", "street", "road", "outside", "outdoor", "leave the home",
    "leave the house", "leave home", "left the home", "left the house", "left home",
    "front door", "climb", "balcony", "window", "stranger",
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
    # A phrase takes the forms on its first and last word, and any run of spaces or hyphens
    # between words ("front door", "front-door").
    words = entry.split()
    if len(words) == 1:
        return _forms(words[0])
    middle = [re.escape(word) for word in words[1:-1]]
    return r"[\s-]+".join([_forms(words[0]), *middle, _forms(words[-1])])


_BANNED = re.compile(
    r"\b(?:" + "|".join(_banned_pattern(entry) for entry in BANNED_WORDS) + r")\b", re.I
)

ANSWER_MAX_LENGTH = 60
# The youngest kid decides: under 6, the texts are shorter.
YOUNG_AGE = 6
PARAGRAPH_LIMIT = {False: 600, True: 400}
SHORT_TEXT_LIMIT = {False: 400, True: 250}


# The words a parent reads aloud in one evening, set by the youngest kid: a small child loses the
# thread of a long story. All paragraphs of read_aloud together, and how many paragraphs.
@dataclass(frozen=True)
class ReadAloudBudget:
    words_min: int
    words_max: int
    paragraphs_min: int
    paragraphs_max: int


UNDER_6_BUDGET = ReadAloudBudget(50, 80, 2, 3)
AGE_6_TO_7_BUDGET = ReadAloudBudget(80, 120, 3, 4)
AGE_8_UP_BUDGET = ReadAloudBudget(110, 160, 3, 5)
OLDER_BUDGET_AGE = 8

# The oldest kid decides how hard the cipher is.
NUMBER_CODE_AGE = 6
SHIFT_AGE = 8
# Wrong picks in one step before the server shows the right answer and moves on.
MAX_ATTEMPTS = 2
SECRET_WORD_LENGTHS = range(4, 8)
CONTENT_WORD_LENGTH = 4
# The count level hides a short word: the kids point at a box, not read a cipher.
COUNT_WORD_LENGTHS = range(3, 7)
COUNT_BOXES = 5
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
# Wrong buttons of the number code when the earlier clues have too few words. Kid words of 4 to 7
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
    # Written for this riddle. Empty: the hint and the resolution_template of the payload.
    # Only the fallback riddle has its own, and an older payload has none.
    hint: str = ""
    resolution_template: str = ""


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

    @property
    def hint(self) -> str | None:
        """The hint of the riddle in use, so it never talks about the other object."""
        riddle = self.riddle
        return None if riddle is None or self.payload is None else riddle.hint or self.payload.hint

    @property
    def resolution_template(self) -> str | None:
        riddle = self.riddle
        if riddle is None or self.payload is None:
            return None
        return riddle.resolution_template or self.payload.resolution_template


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
        ("fallback_riddle.hint", payload.fallback_riddle.hint),
        ("fallback_riddle.resolution_template", payload.fallback_riddle.resolution_template),
    ]


def read_aloud_budget(youngest_age: int) -> ReadAloudBudget:
    if youngest_age < YOUNG_AGE:
        return UNDER_6_BUDGET
    if youngest_age < OLDER_BUDGET_AGE:
        return AGE_6_TO_7_BUDGET
    return AGE_8_UP_BUDGET


def word_count(paragraphs: tuple[str, ...]) -> int:
    return sum(len(text.split()) for text in paragraphs)


def text_limits(youngest_age: int) -> tuple[int, int]:
    """The longest read-aloud paragraph and the longest short text, in characters."""
    young = youngest_age < YOUNG_AGE
    return PARAGRAPH_LIMIT[young], SHORT_TEXT_LIMIT[young]


def banned_words(text: str) -> list[str]:
    found = (match.group(0).lower() for match in _BANNED.finditer(text))
    return [" ".join(re.split(r"[\s-]+", word)) for word in found]


_WORDS = re.compile(r"[^\W\d_]+")
COMMON_ENGLISH = frozenset({
    "the", "and", "a", "to", "is", "you", "it", "of", "in", "was", "he", "she", "that", "they",
    "her", "his", "with", "for", "on", "at", "as", "we", "i", "an", "are", "this", "but", "not",
})  # fmt: skip
# Under this many words a text says too little to judge.
ENGLISH_MIN_WORDS = 8
# Of the words of a story, at least this share are very common English ones (real stories have
# about a third; German or French stories with a few of the same short words stay far below).
ENGLISH_MIN_SHARE = 0.2
# Accents on lower-case words are rare in English; a story in another language has many.
ENGLISH_MAX_NON_ASCII = 0.02


def is_english(text: str) -> bool:
    """A cheap check, not a language detector: the prompt asks for English and this catches a
    story in another language. Texts too short to judge pass."""
    # A capitalized word with accents or in another script is a name, like Zoë or a kid's
    # nickname: it counts for nothing either way.
    words = [w for w in _WORDS.findall(text) if w.isascii() or not w[0].isupper()]
    letters = sum(len(word) for word in words)
    if not letters:
        return True
    non_ascii = sum(1 for word in words for char in word if not char.isascii())
    if non_ascii / letters > ENGLISH_MAX_NON_ASCII:
        return False
    if len(words) < ENGLISH_MIN_WORDS:
        return True
    common = sum(1 for word in words if word.lower() in COMMON_ENGLISH)
    return common / len(words) >= ENGLISH_MIN_SHARE


# Letters only, so "Daisy's" is Daisy and a lone s.
_PLAIN_WORD = re.compile(r"[A-Za-z]+")


@dataclass(frozen=True)
class DraftContext:
    """What the episode writer knows beyond the home: the brief of the evening. The checks that
    need a part of it are skipped when it is missing."""

    clue_text: str = ""
    clue_suspect: str = ""
    suspect_names: tuple[str, ...] = ()
    # The objects code chose for tonight's riddles.
    target_object: str | None = None
    fallback_object: str | None = None


def pick_targets(objects: tuple[str, ...], earlier: list[Episode]) -> tuple[str | None, str | None]:
    """The objects of tonight's riddle and fallback riddle: the safe objects of the home in
    turn, each time one used the fewest times in the earlier evenings of the family (the riddle
    that was played counts). The same history always gives the same pick."""
    safe = safe_objects(objects)
    if not safe:
        return None, None
    used = Counter(e.riddle.target_object for e in earlier if e.riddle is not None)
    start = len(earlier) % len(safe)
    turn = [safe[(start + i) % len(safe)] for i in range(len(safe))]
    target = min(turn, key=lambda obj: used[obj])
    others = [obj for obj in turn if obj != target] or turn
    return target, min(others, key=lambda obj: used[obj])


# British spellings a story must not use, as (British stem, American stem, regular endings).
# Only the stored enum value AnswerType.COLOUR keeps its spelling.
_OUR_ENDINGS = "(?:s|ed|ing|ful|ite|ites|less|ly)?"
_BRITISH = (
    *(
        (british, american, _OUR_ENDINGS)
        for british, american in (
            ("colour", "color"), ("favour", "favor"), ("flavour", "flavor"),
            ("honour", "honor"), ("humour", "humor"), ("labour", "labor"),
            ("neighbour", "neighbor"), ("rumour", "rumor"), ("savour", "savor"),
            ("behaviour", "behavior"), ("harbour", "harbor"), ("odour", "odor"),
            ("vapour", "vapor"), ("armour", "armor"),
        )
    ),
    ("realis", "realiz", "(?:e|es|ed|ing|ation)"),
    ("recognis", "recogniz", "(?:e|es|ed|ing|ation)"),
    ("organis", "organiz", "(?:e|es|ed|ing|ation)"),
    ("apologis", "apologiz", "(?:e|es|ed|ing)"),
    ("cosy", "cozy", "(?:ly)?"),
    ("grey", "gray", "(?:s|er|est|ish)?"),
    ("centre", "center", "(?:s|d)?"),
    ("metre", "meter", "s?"),
    ("litre", "liter", "s?"),
    ("theatre", "theater", "s?"),
    ("mum", "mom", "s?"),
    ("pyjamas", "pajamas", ""),
    ("tyre", "tire", "s?"),
    ("programme", "program", "s?"),
    ("jewellery", "jewelry", ""),
    ("aeroplane", "airplane", "s?"),
)  # fmt: skip
_BRITISH_PATTERNS = tuple(
    (re.compile(rf"\b({british})({endings})\b", re.I), american)
    for british, american, endings in _BRITISH
)


def british_spellings(text: str) -> list[str]:
    """The British spellings in a text, each with the American one: "colour (color)"."""
    found = []
    for pattern, american in _BRITISH_PATTERNS:
        for match in pattern.finditer(text):
            found.append(f"{match.group(0).lower()} ({american}{match.group(2).lower()})")
    return found


# What a riddle asks for, by answer type. The stored type "colour" keeps its spelling; "colour"
# in a text is a British spelling and is refused on its own.
_ASK = {
    "number": (re.compile(r"\b(?:numbers?|how many)\b", re.I), "number or how many"),
    "colour": (re.compile(r"\bcolou?rs?\b", re.I), "color"),
    "letter": (re.compile(r"\bletters?\b", re.I), "letter"),
    "shape": (re.compile(r"\bshapes?\b", re.I), "shape"),
    "word": (re.compile(r"\bwords?\b", re.I), "word"),
}


def asks_for_answer(riddle: Riddle) -> bool:
    """The riddle text has the word that asks for its answer type: "What am I?" alone does not."""
    ask = _ASK.get(riddle.answer_type)
    return ask is None or ask[0].search(riddle.text) is not None


def _name_words(names: tuple[str, ...]) -> set[str]:
    # "Felix the Fox" is Felix and Fox: a story names a suspect by either.
    return {
        word.lower()
        for name in names
        for word in _PLAIN_WORD.findall(name)
        if len(word) >= 3 and word.lower() not in STOPWORDS
    }


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 4 else word


def clue_content_words(clue: str, suspect_names: tuple[str, ...]) -> set[str]:
    """The words that carry the clue: 4 letters or more, no filler word, no suspect name."""
    names = _name_words(suspect_names)
    return {
        _stem(word.lower())
        for word in _PLAIN_WORD.findall(clue)
        if len(word) >= CONTENT_WORD_LENGTH
        and word.lower() not in STOPWORDS
        and word.lower() not in names
    }


def retold_clue(paragraphs: tuple[str, ...], context: DraftContext) -> list[str]:
    """The story must not give away the clue before the kids decode it: a paragraph that names
    the suspect of the clue together with a word of the clue tells what the clue tells."""
    if not context.clue_suspect or not context.clue_text:
        return []
    suspect = _name_words((context.clue_suspect,))
    content = clue_content_words(context.clue_text, context.suspect_names)
    found = []
    for index, text in enumerate(paragraphs, start=1):
        words = [word.lower() for word in _PLAIN_WORD.findall(text)]
        if not suspect.intersection(words):
            continue
        shared = sorted(content.intersection(_stem(word) for word in words))
        if shared:
            found.append(
                f"the story tells the clue before the kids decode it: read_aloud paragraph "
                f"{index} names {context.clue_suspect} together with {', '.join(shared)}; the "
                "clue is found only after the strike, so say nothing about that suspect "
                "being cleared or suspected tonight"
            )
    return found


def draft_problems(
    payload: Payload,
    objects: tuple[str, ...],
    youngest_age: int,
    slot: str,
    secret: str | None = None,
    context: DraftContext | None = None,
) -> list[str]:
    """Why the episode cannot be read to the kids. Empty when it is fine."""
    problems = []
    context = context or DraftContext()
    for name, riddle, wanted in (
        ("riddle", payload.riddle, context.target_object),
        ("fallback riddle", payload.fallback_riddle, context.fallback_object),
    ):
        if wanted is not None and riddle.target_object != wanted:
            problems.append(
                f"the {name} must point at {wanted!r} tonight, not {riddle.target_object!r}"
            )
    for name, riddle in (("riddle", payload.riddle), ("fallback riddle", payload.fallback_riddle)):
        if riddle.target_object not in objects:
            problems.append(f"the {name} points at {riddle.target_object!r}, not in the home")
        if not asks_for_answer(riddle):
            word = _ASK[riddle.answer_type][1]
            problems.append(
                f"the {name} asks for nothing: its answer_type is {riddle.answer_type}, so its "
                f"text must end with a question that has the word {word} in it"
            )
    if payload.riddle.target_object == payload.fallback_riddle.target_object:
        problems.append("both riddles point at the same object")
    if payload.resolution_template.count(slot) != 1:
        problems.append(f"the resolution needs {slot} exactly once")
    if payload.fallback_riddle.resolution_template.count(slot) != 1:
        problems.append(f"the fallback riddle's own resolution_template needs {slot} exactly once")
    if not payload.fallback_riddle.hint.strip():
        problems.append("the fallback riddle needs its own hint")
    young = youngest_age < YOUNG_AGE
    budget = read_aloud_budget(youngest_age)
    count = len(payload.read_aloud)
    if not budget.paragraphs_min <= count <= budget.paragraphs_max:
        problems.append(
            f"read_aloud needs {budget.paragraphs_min} to {budget.paragraphs_max} paragraphs "
            f"for a {youngest_age}-year-old, it has {count}"
        )
    words = word_count(payload.read_aloud)
    if words < budget.words_min:
        problems.append(
            f"read_aloud is too short: {words} words, the budget for a {youngest_age}-year-old "
            f"is {budget.words_min} to {budget.words_max} words"
        )
    elif words > budget.words_max:
        problems.append(
            f"read_aloud is too long: {words} words, the budget for a {youngest_age}-year-old "
            f"is {budget.words_min} to {budget.words_max} words; cut it"
        )
    paragraph_max, short_max = PARAGRAPH_LIMIT[young], SHORT_TEXT_LIMIT[young]
    for index, text in enumerate(payload.read_aloud, start=1):
        if len(text) > paragraph_max:
            problems.append(
                f"a read_aloud paragraph is too long: paragraph {index} has {len(text)} "
                f"characters, the limit is {paragraph_max}"
            )
    problems += retold_clue(payload.read_aloud, context)
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
    for name, text in named:
        british = british_spellings(text)
        if british:
            problems.append(
                f"british spelling: {', '.join(british)} in {name}; "
                "write american english, with the american spelling in the brackets"
            )
    hidden = set(secret_words(secret))
    for name, text in named:
        given_away = sorted({word for word in _spoken_words(text) if word in hidden})
        if given_away:
            problems.append(
                f"gives the clue away: {', '.join(word.lower() for word in given_away)} in "
                f"{name} is a word the kids decode later; tell the story without it"
            )
    if not is_english(" ".join(payload.read_aloud)):
        problems.append("write in English: the read_aloud text is not English")
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
    youngest_age: int = YOUNG_AGE,
    target_object: str | None = None,
    fallback_object: str | None = None,
) -> Payload:
    """A plain episode for when the model fails: always safe and always playable. A safe
    riddle the model wrote for this home is kept. Only objects with safe names are used; a home
    with none gets the generic riddles, which need nothing from the home."""
    safe = safe_objects(objects)
    # The model's riddle keeps only its object and texts: its own hint and resolution were not
    # checked and the built-in ones fit any riddle.
    if model_riddle is not None:
        model_riddle = replace(model_riddle, hint="", resolution_template="")
    chosen = target_object if target_object in safe else None
    first = model_riddle or (
        _built_in_riddle(chosen or safe[(number - 1) % len(safe)]) if safe else _GENERIC_RIDDLES[0]
    )
    others = [obj for obj in safe if obj != first.target_object] or list(safe)
    wanted = fallback_object if fallback_object in others else None
    second = (
        _built_in_riddle(wanted or others[number % len(others)]) if others else _GENERIC_RIDDLES[1]
    )
    ending = (
        "Now think about all the clues together. Who do you think did it?"
        if last
        else "But the case is not solved yet. More clues are waiting for tomorrow."
    )
    hint = "Walk slowly through the home and look carefully."
    resolution_template = f"You found it: {slot}. Great detective work!"
    return Payload(
        recap=f"Welcome back to {title}, detectives.",
        read_aloud=_built_in_story(read_aloud_budget(youngest_age)),
        riddle=first,
        hint=hint,
        fallback_riddle=replace(second, hint=hint, resolution_template=resolution_template),
        resolution_template=resolution_template,
        case_clue=clue,
        cliffhanger=ending,
    )


_STORY_START = "The detectives open their notebook and read the notes once more."
_STORY_END = "Something in this home is hiding a secret code. Can you find it?"
_STORY_MIDDLE = (
    "The lamp is warm and the room is quiet.",
    "A small clock ticks on the shelf.",
    "The detectives sit close together and think.",
    "Every clue is a little piece of the puzzle.",
    "Good detectives look slowly and listen well.",
    "The pencil is sharp and the page is clean.",
    "Somewhere in the home a secret is waiting.",
    "The first clue is easy to miss.",
    "The detectives smile because they love a mystery.",
    "A cozy blanket lies on the couch.",
    "Everyone takes a deep breath together.",
    "The notebook has room for one more note.",
    "A friendly cat watches from the corner.",
    "The detectives are brave and kind.",
    "They whisper and share their ideas.",
    "A soft light shines on the notebook.",
    "The night is calm and the home is safe.",
    "Each detective has a very important job.",
    "The puzzle is a little tricky tonight.",
    "But the detectives never give up.",
)  # fmt: skip


def _built_in_story(budget: ReadAloudBudget) -> tuple[str, ...]:
    """Sentences up to the middle of the word budget, in the fewest paragraphs it allows."""
    target = (budget.words_min + budget.words_max) // 2
    sentences = [_STORY_START]
    for sentence in _STORY_MIDDLE:
        if len(" ".join([*sentences, _STORY_END]).split()) >= target:
            break
        sentences.append(sentence)
    sentences.append(_STORY_END)
    size = -(-len(sentences) // budget.paragraphs_min)
    return tuple(" ".join(sentences[i : i + size]) for i in range(0, len(sentences), size))


def safe_objects(objects: tuple[str, ...]) -> tuple[str, ...]:
    """The objects whose names pass the unsafe-words check: only these go to the model and to
    the built-in riddles."""
    return tuple(obj for obj in objects if not banned_words(obj))


# For a home with no safe object. They are not in the home's list, so nothing checks their
# target: it only has to be safe text, which a fixed sentence is. Any room has something soft
# and something round.
_GENERIC_RIDDLES = (
    Riddle(
        text="Look around the room you are in and find something soft. What color is it?",
        target_object="something soft in the room",
        answer_type="colour",
        parent_note="Help the kids find something soft nearby. Any color they say is right.",
    ),
    Riddle(
        text="Look around the room you are in and find something round. What color is it?",
        target_object="something round in the room",
        answer_type="colour",
        parent_note="Help the kids find something round nearby. Any color they say is right.",
    ),
)


def _built_in_riddle(target: str) -> Riddle:
    return Riddle(
        text=f"Find the {target}. What color is it?",
        target_object=target,
        answer_type="colour",
        parent_note=f"Help the kids find the {target}. Any color they say is right.",
    )


def is_safe_riddle(riddle: Riddle, objects: tuple[str, ...], youngest_age: int) -> bool:
    young = youngest_age < YOUNG_AGE
    texts = (riddle.text, riddle.parent_note)
    return (
        riddle.target_object in safe_objects(objects)
        and not any(banned_words(text) or british_spellings(text) for text in texts)
        and all(len(text) <= SHORT_TEXT_LIMIT[young] for text in texts)
        and asks_for_answer(riddle)
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
    candidates: list[str],
    fallback: tuple[str, ...],
    secret: str,
    seen: set[str],
    how_many: int = 2,
) -> tuple[str, ...]:
    """The wrong buttons, two unless told otherwise. None of their words is in the clue,
    because the kids would see that it is not the missing one."""
    chosen: list[str] = []
    for text in _length_order(candidates, secret) + _length_order(list(fallback), secret):
        if text == secret or text in chosen or any(word in seen for word in text.split()):
            continue
        chosen.append(text)
        if len(chosen) == how_many:
            break
    return tuple(chosen)


def _count_plan(words: list[str], others: list[list[str]]) -> CipherPlan:
    """The longest short word of the clue is the secret; the four other boxes hold short words
    of the case's earlier clues, then kid words, and none of them is in this clue. A clue with no
    such word gives a count level with no secret: any pick passes."""
    best: str | None = None
    for word in words:
        if len(word) not in COUNT_WORD_LENGTHS or word.lower() in FILLER_WORDS:
            continue
        if best is None or len(word) > len(best):
            best = word
    if best is None:
        return CipherPlan(CipherLevel.COUNT, None, ())
    found = [
        word
        for other in others
        for word in other
        if len(word) in COUNT_WORD_LENGTHS and word.lower() not in FILLER_WORDS
    ]
    short = tuple(word for word in KID_WORDS if len(word) in COUNT_WORD_LENGTHS)
    decoys = _decoys(found, short, best, set(words), COUNT_BOXES - 1)
    return CipherPlan(CipherLevel.COUNT, best, decoys)


def plan_cipher(clue: str, oldest_age: int, earlier_clues: tuple[str, ...] = ()) -> CipherPlan:
    """The level for the kids' age and the secret and decoys from the plan's clue. The decoys
    come from the clues of earlier episodes, then from a list of kid words, and none of them is
    in this clue. A clue with no secret that works gives the level count, which needs none."""
    level = cipher_level_for(oldest_age)
    words = _clue_words(clue)
    others = [_clue_words(other) for other in earlier_clues]
    index = _secret_index(words)
    if level == CipherLevel.COUNT or index is None:
        return _count_plan(words, others)
    seen = set(words)
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
    return _count_plan(words, others)


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
    """How many claps, and the number of the box to point at: 1 to 5."""
    return (key - 1) % COUNT_BOXES + 1


def count_options(secret: str, decoys: tuple[str, ...], target: int) -> list[str]:
    """The words of boxes 1 to 5 in this order, the secret in box `target`."""
    options = list(decoys)
    options.insert(target - 1, secret)
    return options


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
