"""The setup of a family and its session."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from jumbaq.core.clock import Clock
from jumbaq.core.family import FamilyRef
from jumbaq.families import domain
from jumbaq.families.domain import Family, NewFamily, NewKid
from jumbaq.families.errors import NoFamilySessionError
from jumbaq.families.events import FamilyCreated
from jumbaq.families.queries import KidView
from jumbaq.families.uow import FamiliesUoWFactory


@dataclass(frozen=True)
class CreatedFamily:
    family: Family
    # Goes only into the cookie. The database keeps its hash.
    session_token: str


@dataclass(frozen=True)
class FamilyState:
    """The family for its home screen, with what the screen needs to know about the server."""

    id: uuid.UUID
    rooms: list[str]
    objects: list[str]
    kids: list[KidView]
    created_at: datetime
    # The web app shows "open it now" only when this is true.
    demo_mode: bool


class FamilyService:
    def __init__(self, uow: FamiliesUoWFactory, clock: Clock, demo_mode: bool) -> None:
        self._uow = uow
        self._clock = clock
        self._demo_mode = demo_mode

    async def create(
        self, rooms: list[str], objects: list[str], kids: list[NewKid]
    ) -> CreatedFamily:
        domain.check_kids(tuple(kids))
        token = domain.new_session_token()
        new = NewFamily(
            rooms=tuple(rooms),
            objects=tuple(objects),
            kids=tuple(kids),
            session_token_hash=domain.hash_session_token(token),
            created_at=self._clock.now(),
        )
        async with self._uow() as uow:
            family = await uow.families.add(new)
            await uow.publish(FamilyCreated(family.id))
            await uow.commit()
        return CreatedFamily(family, token)

    async def get(self, family: FamilyRef) -> FamilyState:
        async with self._uow() as uow:
            found = await uow.queries.get(family.family_id)
        if found is None:
            raise NoFamilySessionError()
        return FamilyState(
            id=found.id,
            rooms=found.rooms,
            objects=found.objects,
            kids=found.kids,
            created_at=found.created_at,
            demo_mode=self._demo_mode,
        )

    async def resolve(self, session_token: str | None) -> FamilyRef:
        if not session_token:
            raise NoFamilySessionError()
        async with self._uow() as uow:
            family_id = await uow.families.id_by_session(domain.hash_session_token(session_token))
        if family_id is None:
            raise NoFamilySessionError()
        return FamilyRef(family_id)
