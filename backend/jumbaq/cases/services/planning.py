from jumbaq.cases.domain import FIRST_CASE, CaseStatus
from jumbaq.cases.uow import CasesUoWFactory
from jumbaq.core.family import FamilyRef


class CasePlanning:
    def __init__(self, uow: CasesUoWFactory) -> None:
        self._uow = uow

    async def open_first(self, family: FamilyRef) -> None:
        """Safe to run twice: a family that has case 1 keeps it."""
        async with self._uow() as uow:
            await uow.cases.add_if_missing(family, FIRST_CASE, CaseStatus.PLANNING)
            await uow.commit()
