from dataclasses import dataclass
from typing import ClassVar

from jumbaq.core.events import Event


@dataclass(frozen=True)
class FamilyCreated(Event):
    """The setup is done. The family can start its first case."""

    topic: ClassVar[str] = "families.created"
