"""How far a family is in a case. The episodes module tells it, through an event, when an
episode is played."""

import uuid

from jumbaq.ai.public import EPISODES_PER_CASE
from jumbaq.cases import domain
from jumbaq.cases.uow import CasesUoWFactory
from jumbaq.core.family import FamilyRef


class CaseProgress:
    def __init__(self, uow: CasesUoWFactory) -> None:
        self._uow = uow

    async def episode_played(self, family: FamilyRef, case_id: uuid.UUID, number: int) -> None:
        """Safe to run twice and in any order. After the last episode the kids may accuse."""
        async with self._uow() as uow:
            case = await uow.cases.get(family, case_id, for_update=True)
            if case is None:
                return
            moved = domain.with_episode_played(case, number, EPISODES_PER_CASE)
            if moved != case:
                await uow.cases.update(moved)
            await uow.commit()
