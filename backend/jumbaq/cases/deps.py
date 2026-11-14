from functools import partial
from typing import Annotated

from fastapi import Depends

from jumbaq.cases.services.cases import CaseService
from jumbaq.cases.uow import CasesUoW, CasesUoWFactory
from jumbaq.core.deps import ClockDep, SessionmakerDep, TaskQueueDep
from jumbaq.core.outbox import nudge_worker


def get_uow_factory(sessionmaker: SessionmakerDep, queue: TaskQueueDep) -> CasesUoWFactory:
    return partial(CasesUoW, sessionmaker, nudge=nudge_worker(queue))


CasesUoWFactoryDep = Annotated[CasesUoWFactory, Depends(get_uow_factory)]


def get_case_service(uow: CasesUoWFactoryDep, clock: ClockDep) -> CaseService:
    return CaseService(uow, clock)


CaseServiceDep = Annotated[CaseService, Depends(get_case_service)]
