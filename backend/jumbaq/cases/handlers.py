from jumbaq.cases.events import CaseOpened
from jumbaq.cases.services.planning import CasePlanning
from jumbaq.cases.services.progress import CaseProgress
from jumbaq.core.family import FamilyRef
from jumbaq.episodes.public import EpisodePlayed
from jumbaq.families.public import FamilyCreated


class CasesHandlers:
    def __init__(self, planning: CasePlanning, progress: CaseProgress) -> None:
        self._planning = planning
        self._progress = progress

    async def family_created(self, event: FamilyCreated) -> None:
        await self._planning.open_first(FamilyRef(event.family_id))

    async def case_opened(self, event: CaseOpened) -> None:
        await self._planning.plan(FamilyRef(event.family_id), event.case_id)

    async def episode_played(self, event: EpisodePlayed) -> None:
        await self._progress.episode_played(FamilyRef(event.family_id), event.case_id, event.number)
