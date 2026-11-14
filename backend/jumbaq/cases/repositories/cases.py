"""What the services of cases need from storage."""

from typing import Protocol

from jumbaq.cases.domain import CaseStatus
from jumbaq.core.family import FamilyRef


class CaseRepository(Protocol):
    async def add_if_missing(self, family: FamilyRef, number: int, status: CaseStatus) -> bool:
        """False when the family already has a case with this number."""
        ...
