from dataclasses import dataclass
from typing import ClassVar

from jumbaq.core.events import Event


@dataclass(frozen=True)
class SubscriptionActivated(Event):
    """The family has paid and can start the cases after the free ones."""

    topic: ClassVar[str] = "billing.subscription_activated"
