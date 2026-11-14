import uuid
from dataclasses import dataclass
from typing import ClassVar

from jumbaq.core.events import Event


@dataclass(frozen=True)
class EpisodeRequested(Event):
    """An episode waits to be written. The model call is its own step in the worker."""

    topic: ClassVar[str] = "episodes.requested"
    episode_id: uuid.UUID


@dataclass(frozen=True)
class EpisodePlayed(Event):
    """The kids answered. cases counts it, and after the last one they may accuse."""

    topic: ClassVar[str] = "episodes.played"
    case_id: uuid.UUID
    number: int
