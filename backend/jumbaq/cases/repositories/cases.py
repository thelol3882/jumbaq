"""What the services of cases need from storage."""

import uuid
from typing import Protocol

from jumbaq.cases.domain import Case, CaseStatus, Plan
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

    async def earlier_plans(self, family: FamilyRef, case_id: uuid.UUID) -> list[Plan]:
        """The plans of the family's other cases, for titles and names not to repeat."""
        ...
