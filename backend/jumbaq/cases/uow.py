from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.cases.repositories.cases import CaseRepository
from jumbaq.cases.repositories.sql import SqlCaseRepository
from jumbaq.core.db import UnitOfWork


class CasesUoW(UnitOfWork):
    cases: CaseRepository

    def _attach(self, session: AsyncSession) -> None:
        self.cases = SqlCaseRepository(session)


CasesUoWFactory = Callable[[], CasesUoW]
