import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from jumbaq.ai.public import AnswerType
from jumbaq.episodes.domain import EpisodeStatus

# What the kids read off the object. The service also removes line breaks before the answer
# goes into the story.
Answer = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]


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


class EpisodeContentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    recap: str
    read_aloud: list[str]
    # The riddle in use: the fallback one after a swap.
    riddle: RiddleOut
    hint: str
    swapped: bool
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
