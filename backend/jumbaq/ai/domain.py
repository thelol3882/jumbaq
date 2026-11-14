"""What we ask the model, what it gives back and the record of every call.

The drafts only have the right shape. Whether a plan or an episode follows the rules of the
game is checked by the module that asked for it.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta, tzinfo
from enum import StrEnum
from zoneinfo import ZoneInfo

# The daily cap starts again at midnight for our families, not at midnight UTC.
FAMILY_TIME_ZONE = ZoneInfo("Asia/Almaty")


class TaskKind(StrEnum):
    CASE_PLAN = "case_plan"
    EPISODE = "episode"


class CallOutcome(StrEnum):
    OK = "ok"
    BAD_OUTPUT = "bad_output"
    UNAVAILABLE = "unavailable"


class AnswerType(StrEnum):
    """What the kids read off the household object."""

    NUMBER = "number"
    COLOUR = "colour"
    LETTER = "letter"
    SHAPE = "shape"
    WORD = "word"


@dataclass(frozen=True)
class KidInput:
    nickname: str
    age: int


@dataclass(frozen=True)
class HomeInput:
    """The family as the model may see it. Everything here was typed by the parent."""

    kids: tuple[KidInput, ...]
    rooms: tuple[str, ...]
    objects: tuple[str, ...]


@dataclass(frozen=True)
class CasePlanInput:
    home: HomeInput
    case_number: int
    # The longest clue the caller accepts. Episodes quote clues word for word, so they stay short.
    clue_max_chars: int | None = None
    # Picked by code, so cases of one family look different: where the case happens and what
    # goes missing there.
    world: str | None = None
    missing_thing: str | None = None
    # What the family played before. The new case must not reuse any of it.
    used_titles: tuple[str, ...] = ()
    used_suspect_names: tuple[str, ...] = ()
    # Why the previous plan was refused, so the next try fixes exactly that.
    fix: tuple[str, ...] = ()


@dataclass(frozen=True)
class SuspectDraft:
    id: str
    name: str
    description: str


@dataclass(frozen=True)
class ClueDraft:
    episode: int
    text: str
    suspect_id: str
    # True: the clue points at this suspect. False: it rules the suspect out.
    points_at: bool


@dataclass(frozen=True)
class CaseDraft:
    title: str
    setting: str
    suspects: tuple[SuspectDraft, ...]
    culprit_id: str
    clues: tuple[ClueDraft, ...]
    reveal: str


@dataclass(frozen=True)
class PlayedEpisode:
    number: int
    target_object: str
    # What the kids answered. Typed by the parent, so it is untrusted.
    answer: str


@dataclass(frozen=True)
class TextRules:
    """The limits the caller checks a draft against. The prompt states the same numbers, so the
    model knows the rules it is measured by."""

    paragraph_max_chars: int
    short_text_max_chars: int
    banned_words: tuple[str, ...]
    # The read-aloud budget for the youngest kid: all paragraphs together.
    words_min: int = 0
    words_max: int = 0
    paragraphs_min: int = 1
    paragraphs_max: int = 5


@dataclass(frozen=True)
class EpisodeInput:
    home: HomeInput
    case_title: str
    setting: str
    suspects: tuple[SuspectDraft, ...]
    number: int
    clue: ClueDraft
    played: tuple[PlayedEpisode, ...]
    rules: TextRules | None = None
    # The objects the riddles must point at tonight. Code picks them to use the whole home.
    target_object: str | None = None
    fallback_object: str | None = None
    # Why the previous draft was refused, so the next try fixes exactly that.
    fix: tuple[str, ...] = ()
    # Words of the clue the kids decode later: the story never uses them.
    secret_words: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiddleDraft:
    text: str
    target_object: str
    answer_type: AnswerType
    parent_note: str
    # Only the fallback riddle has them: a hint and a resolution written for this riddle, because
    # the family plays it instead of the first one. Empty for the first riddle, which uses the
    # hint and the resolution_template of the episode.
    hint: str = ""
    resolution_template: str = ""


@dataclass(frozen=True)
class EpisodeDraft:
    recap: str
    read_aloud: tuple[str, ...]
    riddle: RiddleDraft
    hint: str
    fallback_riddle: RiddleDraft
    resolution_template: str
    case_clue: str
    cliffhanger: str


@dataclass(frozen=True)
class LlmCall:
    family_id: uuid.UUID
    kind: TaskKind
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    outcome: CallOutcome
    created_at: datetime


def day_start(now: datetime, zone: tzinfo = FAMILY_TIME_ZONE) -> datetime:
    """The last midnight in the family time zone, as an aware time."""
    local = now.astimezone(zone)
    return datetime.combine(local.date(), time(), tzinfo=zone)


def day_end(now: datetime, zone: tzinfo = FAMILY_TIME_ZONE) -> datetime:
    """The next midnight in the family time zone: the day ends before it."""
    local = now.astimezone(zone)
    return datetime.combine(local.date() + timedelta(days=1), time(), tzinfo=zone)


def limit_reached(calls_today: int, daily_limit: int) -> bool:
    return calls_today >= daily_limit
