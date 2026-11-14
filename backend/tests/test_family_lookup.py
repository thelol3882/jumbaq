"""The read port other modules use to learn a family's home (families/public.py)."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.core.db import UnitOfWork
from jumbaq.core.family import FamilyRef
from jumbaq.families.public import FamilyLookup
from tests.flows import create_family

pytestmark = pytest.mark.integration


class LookupUoW(UnitOfWork):
    """As another module attaches the port in its own unit of work."""

    families: FamilyLookup

    def _attach(self, session: AsyncSession) -> None:
        self.families = FamilyLookup(session)


async def test_the_home_of_a_family(
    live_client: TestClient, sessionmaker: async_sessionmaker[AsyncSession]
) -> None:
    kids = [{"nickname": "Timur", "age": 9}, {"nickname": "Aru", "age": 7}]
    family_id, _ = create_family(live_client, kids=kids)

    async with LookupUoW(sessionmaker) as uow:
        family = await uow.families.get(FamilyRef(family_id))

    assert family is not None
    assert family.id == family_id
    # The youngest first, so a rule about the youngest kid reads the first one.
    assert [(kid.nickname, kid.age) for kid in family.kids] == [("Aru", 7), ("Timur", 9)]
    assert family.rooms == ("kitchen", "living room", "bedroom")
    assert family.objects == ("fridge", "sofa", "bookshelf", "kettle")


async def test_an_unknown_family_has_no_home(
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    async with LookupUoW(sessionmaker) as uow:
        assert await uow.families.get(FamilyRef(uuid.uuid4())) is None
