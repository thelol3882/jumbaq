from functools import partial
from typing import Annotated

from fastapi import Cookie, Depends

from jumbaq.core.context import family_id_var
from jumbaq.core.deps import ClockDep, SessionmakerDep, TaskQueueDep
from jumbaq.core.family import FamilyRef
from jumbaq.core.outbox import nudge_worker
from jumbaq.families.services.families import FamilyService
from jumbaq.families.uow import FamiliesUoW, FamiliesUoWFactory

FAMILY_COOKIE = "family_session"


def get_uow_factory(sessionmaker: SessionmakerDep, queue: TaskQueueDep) -> FamiliesUoWFactory:
    return partial(FamiliesUoW, sessionmaker, nudge=nudge_worker(queue))


FamiliesUoWFactoryDep = Annotated[FamiliesUoWFactory, Depends(get_uow_factory)]


def get_family_service(uow: FamiliesUoWFactoryDep, clock: ClockDep) -> FamilyService:
    return FamilyService(uow, clock)


FamilyServiceDep = Annotated[FamilyService, Depends(get_family_service)]


async def get_family(
    families: FamilyServiceDep,
    session_token: Annotated[str | None, Cookie(alias=FAMILY_COOKIE)] = None,
) -> FamilyRef:
    """The family of the session cookie. Every endpoint that acts for a family uses it."""
    family = await families.resolve(session_token)
    family_id_var.set(str(family.family_id))
    return family


FamilyDep = Annotated[FamilyRef, Depends(get_family)]
