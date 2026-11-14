import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from jumbaq.cases.domain import CaseStatus, Rank

SuspectId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]


class EpisodeSlotStatus(StrEnum):
    """The statuses of an episode, plus `locked` for one that does not exist yet."""

    LOCKED = "locked"
    REQUESTED = "requested"
    GENERATING = "generating"
    READY = "ready"
    PLAYED = "played"
    FAILED = "failed"


class SuspectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str


class ClueOut(BaseModel):
    """A clue of an episode already played. Clues of later episodes are never sent."""

    model_config = ConfigDict(from_attributes=True)

    episode: int
    text: str
    suspect_id: str
    # True: this suspect is ruled out. False: the clue points at this suspect.
    rules_out: bool


class CaseEpisodeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    # Null while the episode is locked.
    id: uuid.UUID | None
    status: EpisodeSlotStatus
    available_at: datetime | None


class CaseOut(BaseModel):
    """The culprit and the reveal are never part of it: they come only with the right
    accusation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    status: CaseStatus
    # Null while the case is planned.
    title: str | None
    # Empty while the case is planned.
    suspects: list[SuspectOut]
    clues: list[ClueOut]
    # Always one item per episode of the case, in order.
    episodes: list[CaseEpisodeOut]
    accusation_attempts: int
    # Set when the case is solved.
    rank: Rank | None


class AccuseIn(BaseModel):
    suspect_id: SuspectId


class AccusationOut(BaseModel):
    """A wrong suspect is not an error: `correct` is false and the kids try again."""

    model_config = ConfigDict(from_attributes=True)

    correct: bool
    accusation_attempts: int
    # These three only when correct.
    rank: Rank | None
    reveal: str | None
    culprit_id: str | None


class CertificateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    case_id: uuid.UUID
    number: int
    title: str
    rank: Rank
    nicknames: list[str]
    solved_at: datetime
