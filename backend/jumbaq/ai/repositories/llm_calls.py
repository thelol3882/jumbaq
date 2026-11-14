"""What the services of ai need from storage."""

from datetime import datetime
from typing import Protocol

from jumbaq.ai.domain import LlmCall
from jumbaq.core.family import FamilyRef


class LlmCallRepository(Protocol):
    async def add(self, call: LlmCall) -> None: ...

    async def count_all_since(self, since: datetime) -> int: ...

    async def count_since(self, family: FamilyRef, since: datetime) -> int: ...
