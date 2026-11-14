"""What a family does with its cases: read the current one, accuse, get the certificate and
start the next case."""

import uuid
from typing import NoReturn

from jumbaq.cases.uow import CasesUoWFactory
from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef


class CaseService:
    def __init__(self, uow: CasesUoWFactory, clock: Clock) -> None:
        self._uow = uow
        self._clock = clock

    async def current(self, family: FamilyRef) -> NoReturn:
        raise NotImplementedError

    async def start_next(self, family: FamilyRef) -> NoReturn:
        raise NotImplementedError

    async def accuse(self, family: FamilyRef, case_id: uuid.UUID, suspect_id: str) -> NoReturn:
        raise NotImplementedError

    async def certificate(self, family: FamilyRef, case_id: uuid.UUID) -> NoReturn:
        raise NotImplementedError
