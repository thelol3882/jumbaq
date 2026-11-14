from functools import partial
from typing import Annotated

from fastapi import Depends

from jumbaq.billing.public import BillingAccess, build_billing_access
from jumbaq.cases.services.cases import CaseService
from jumbaq.cases.uow import CasesUoW, CasesUoWFactory
from jumbaq.core.deps import ClockDep, SessionmakerDep, SettingsDep, TaskQueueDep
from jumbaq.core.outbox import nudge_worker


def get_uow_factory(sessionmaker: SessionmakerDep, queue: TaskQueueDep) -> CasesUoWFactory:
    return partial(CasesUoW, sessionmaker, nudge=nudge_worker(queue))


CasesUoWFactoryDep = Annotated[CasesUoWFactory, Depends(get_uow_factory)]


def get_billing_access(sessionmaker: SessionmakerDep, settings: SettingsDep) -> BillingAccess:
    return build_billing_access(sessionmaker, settings)


BillingAccessDep = Annotated[BillingAccess, Depends(get_billing_access)]


def get_case_service(
    uow: CasesUoWFactoryDep, clock: ClockDep, access: BillingAccessDep
) -> CaseService:
    return CaseService(uow, clock, access)


CaseServiceDep = Annotated[CaseService, Depends(get_case_service)]
