from jumbaq.cases.services.planning import CasePlanning
from jumbaq.core.family import FamilyRef
from jumbaq.families.public import FamilyCreated


class CasesHandlers:
    def __init__(self, planning: CasePlanning) -> None:
        self._planning = planning

    async def family_created(self, event: FamilyCreated) -> None:
        await self._planning.open_first(FamilyRef(event.family_id))
