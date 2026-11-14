from jumbaq.cases.public import CasePlanned
from jumbaq.core.family import FamilyRef
from jumbaq.episodes.events import EpisodeRequested
from jumbaq.episodes.services.writing import EpisodeWriting


class EpisodesHandlers:
    def __init__(self, writing: EpisodeWriting) -> None:
        self._writing = writing

    async def case_planned(self, event: CasePlanned) -> None:
        await self._writing.case_planned(FamilyRef(event.family_id), event.case_id)

    async def episode_requested(self, event: EpisodeRequested) -> None:
        await self._writing.write(FamilyRef(event.family_id), event.episode_id)
