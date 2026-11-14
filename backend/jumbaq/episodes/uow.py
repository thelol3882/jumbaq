from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from jumbaq.cases.public import CaseLookup
from jumbaq.core.db import UnitOfWork
from jumbaq.episodes.repositories.episodes import EpisodeRepository
from jumbaq.episodes.repositories.sql import SqlEpisodeRepository
from jumbaq.families.public import FamilyLookup


class EpisodesUoW(UnitOfWork):
    episodes: EpisodeRepository
    # Read ports: the home for the prompt, and the case's title, suspects and clue.
    families: FamilyLookup
    cases: CaseLookup

    def _attach(self, session: AsyncSession) -> None:
        self.episodes = SqlEpisodeRepository(session)
        self.families = FamilyLookup(session)
        self.cases = CaseLookup(session)


EpisodesUoWFactory = Callable[[], EpisodesUoW]
