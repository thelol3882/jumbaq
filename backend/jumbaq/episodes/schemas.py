import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from jumbaq.ai.public import AnswerType
from jumbaq.episodes.domain import CipherLevel, EpisodeStatus, EveningStep

# What the kids read off the object. The service also removes line breaks before the answer
# goes into the story.
Answer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
# A word or phrase picked from the buttons.
Word = Annotated[str, StringConstraints(strip_whitespace=True, max_length=60)]
# The same limits as the suspect id of an accusation in cases.
SuspectId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class RiddleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str
    answer_type: AnswerType
    # For the grown-up: where to look and what counts as an answer.
    parent_note: str


class EpisodeResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    resolution: str
    case_clue: str
    cliffhanger: str
    # What the kids decoded, once the evening is played. Null for the count level.
    decoded_word: str | None
    # True when the strike was given away after two wrong ones.
    revealed_suspect: bool
    struck_suspect_id: str | None
    # True when the clue rules the suspect out, false when it points at them, null if unknown.
    rules_out: bool | None


class AnsweredOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    answer: str
    resolution: str


class DecodeOut(BaseModel):
    """The secret is never here: only the cipher and the buttons to pick from."""

    model_config = ConfigDict(from_attributes=True)

    level: CipherLevel
    key: int
    # The number of the letter A in the number code. Null for the other levels.
    start: int | None
    # How far each letter moves in the shift level. Null for the other levels.
    shift: int | None
    # The cipher text. Null for count: the kids clap or hop `count` times.
    code: str | None
    count: int | None
    # The clue with the hidden word as ____. Null for count.
    clue_with_gap: str | None
    # The secret and two decoys in a fixed order for this episode. Empty for count.
    options: list[str]
    attempts: int


class StrikeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # The plain clue of the plan.
    clue: str
    # True: ask which suspect it points at. False: which one it rules out.
    points_at: bool
    attempts: int
    decoded_word: str | None
    # True when the decode was given away after two wrong picks.
    revealed_word: bool


class EpisodeContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recap: str
    read_aloud: list[str]
    # The riddle in use: the fallback one after a swap.
    riddle: RiddleOut
    hint: str
    swapped: bool
    step: EveningStep
    # Once answered, so the page keeps the resolution during decode and strike.
    answered: AnsweredOut | None
    # Only while step is decode.
    decode: DecodeOut | None
    # Only while step is strike.
    strike: StrikeOut | None
    # Only after the episode is played.
    result: EpisodeResultOut | None


class EpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    case_number: int
    number: int
    status: EpisodeStatus
    available_at: datetime | None
    # Null while the episode is written or not yet available.
    content: EpisodeContentOut | None


class AnswerIn(BaseModel):
    answer: Answer


class DecodeIn(BaseModel):
    # Null for the count level, where the kids only clap or hop.
    word: Word | None = None


class StrikeIn(BaseModel):
    suspect_id: SuspectId
