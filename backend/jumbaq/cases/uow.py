from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.cases.repositories.cases import CaseRepository
from jumbaq.cases.repositories.sql import SqlCaseRepository
from jumbaq.core.db import UnitOfWork
from jumbaq.episodes.public import EpisodeLookup
from jumbaq.families.public import FamilyLookup


class CasesUoW(UnitOfWork):
    cases: CaseRepository
    # The read port of families: the kids, rooms and objects for the plan and the certificate.
    families: FamilyLookup
    # The read port of episodes: the episodes of a case for the case screen.
    episodes: EpisodeLookup

    def _attach(self, session: AsyncSession) -> None:
        self.cases = SqlCaseRepository(session)
        self.families = FamilyLookup(session)
        self.episodes = EpisodeLookup(session)


CasesUoWFactory = Callable[[], CasesUoW]
