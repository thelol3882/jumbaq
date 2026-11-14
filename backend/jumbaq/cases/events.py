import uuid
from dataclasses import dataclass
from typing import ClassVar

from jumbaq.core.events import Event


@dataclass(frozen=True)
class CaseOpened(Event):
    """A case exists and waits for its plan. Planning calls the model, so it is its own step."""

    topic: ClassVar[str] = "cases.opened"
    case_id: uuid.UUID


@dataclass(frozen=True)
class CasePlanned(Event):
    """The plan is saved and the case is active: its first episode can be written."""

    topic: ClassVar[str] = "cases.planned"
    case_id: uuid.UUID


@dataclass(frozen=True)
class CaseSolved(Event):
    topic: ClassVar[str] = "cases.solved"
    case_id: uuid.UUID
