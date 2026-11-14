"""What the services of ai need from storage."""

from datetime import datetime
from typing import Protocol

from jumbaq.ai.domain import LlmCall
from jumbaq.core.family import FamilyRef


class LlmCallRepository(Protocol):
    async def add(self, call: LlmCall) -> None: ...

    async def count_all_between(self, start: datetime, end: datetime) -> int: ...

    async def count_between(self, family: FamilyRef, start: datetime, end: datetime) -> int: ...
