"""What the services of families need from storage."""

import uuid
from typing import Protocol

from jumbaq.families.domain import Family, NewFamily


class FamilyRepository(Protocol):
    async def add(self, family: NewFamily) -> Family:
        """The family and its kids."""
        ...

    async def id_by_session(self, session_token_hash: str) -> uuid.UUID | None: ...
