"""What the services of cases need from storage."""

import uuid
from typing import Protocol

from jumbaq.cases.domain import Case, CaseStatus
from jumbaq.core.family import FamilyRef


class CaseRepository(Protocol):
    async def add_if_missing(
        self, family: FamilyRef, number: int, status: CaseStatus
    ) -> uuid.UUID | None:
        """The id of the new case. None when the family already has a case with this number."""
        ...

    async def get(
        self, family: FamilyRef, case_id: uuid.UUID, *, for_update: bool = False
    ) -> Case | None: ...

    async def newest(self, family: FamilyRef) -> Case | None: ...

    async def update(self, case: Case) -> None:
        """Saves what can change: status, plan, progress, accusation and rank."""
        ...
