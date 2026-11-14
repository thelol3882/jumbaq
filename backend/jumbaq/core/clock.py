"""The time for services. Every time that users see or rules use comes from a Clock, never
from `datetime.now()` or `now()` in PostgreSQL, so tests can set it."""

from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """The current time, always with a time zone (UTC)."""
        ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


class FixedClock:
    """Stands still until a test moves it."""

    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None:
            raise ValueError("the time needs a time zone")
        self._at = at

    def now(self) -> datetime:
        return self._at

    def advance(self, by: timedelta) -> None:
        self._at += by
