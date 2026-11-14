from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.core.db import UnitOfWork
from jumbaq.families.queries import FamilyQueries
from jumbaq.families.repositories.families import FamilyRepository
from jumbaq.families.repositories.sql import SqlFamilyRepository


class FamiliesUoW(UnitOfWork):
    families: FamilyRepository
    queries: FamilyQueries

    def _attach(self, session: AsyncSession) -> None:
        self.families = SqlFamilyRepository(session)
        self.queries = FamilyQueries(session)


FamiliesUoWFactory = Callable[[], FamiliesUoW]
