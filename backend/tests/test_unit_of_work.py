"""How a module unit of work saves its work."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.core.clock import SystemClock
from jumbaq.core.db import UnitOfWork
from jumbaq.families import domain
from jumbaq.families.domain import NewFamily, NewKid
from jumbaq.families.uow import FamiliesUoW

pytestmark = pytest.mark.integration

Sessionmaker = async_sessionmaker[AsyncSession]


def new_family() -> tuple[NewFamily, str]:
    token_hash = domain.hash_session_token(domain.new_session_token())
    family = NewFamily(
        ("kitchen",), ("fridge",), (NewKid("Aru", 7),), token_hash, SystemClock().now()
    )
    return family, token_hash


async def test_work_is_saved_only_after_commit(sessionmaker: Sessionmaker) -> None:
    forgotten, forgotten_hash = new_family()
    saved, saved_hash = new_family()

    async with FamiliesUoW(sessionmaker) as uow:
        await uow.families.add(forgotten)
    async with FamiliesUoW(sessionmaker) as uow:
        await uow.families.add(saved)
        await uow.commit()

    async with FamiliesUoW(sessionmaker) as uow:
        assert await uow.families.id_by_session(forgotten_hash) is None
        assert await uow.families.id_by_session(saved_hash) is not None


async def test_an_error_rolls_back_also_after_a_flush(sessionmaker: Sessionmaker) -> None:
    lost, lost_hash = new_family()

    with pytest.raises(RuntimeError):
        async with FamiliesUoW(sessionmaker) as uow:
            await uow.families.add(lost)
            await uow.session.flush()
            raise RuntimeError("the service failed")

    async with FamiliesUoW(sessionmaker) as uow:
        assert await uow.families.id_by_session(lost_hash) is None


async def test_a_unit_of_work_opens_once(sessionmaker: Sessionmaker) -> None:
    uow = UnitOfWork(sessionmaker)
    async with uow:
        with pytest.raises(RuntimeError, match="already open"):
            await uow.__aenter__()
