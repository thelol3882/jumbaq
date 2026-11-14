"""A new family gets case 1 through the outbox and the worker."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.cases.models import CaseRow
from jumbaq.core.outbox import OutboxDelivery, OutboxRow
from jumbaq.families.public import FamilyCreated
from tests.flows import create_family, stub_handlers

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("quiet_outbox")]

Sessionmaker = async_sessionmaker[AsyncSession]


async def cases_of(sessionmaker: Sessionmaker, family_id: uuid.UUID) -> list[tuple[int, str]]:
    async with sessionmaker() as session:
        rows = await session.execute(
            select(CaseRow.number, CaseRow.status).where(CaseRow.family_id == family_id)
        )
        return [tuple(row) for row in rows]


async def test_a_new_family_gets_case_1_after_the_worker_runs(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)

    async with sessionmaker() as session:
        topics = await session.scalars(
            select(OutboxRow.topic).where(
                OutboxRow.family_id == family_id, OutboxRow.processed_at.is_(None)
            )
        )
        assert list(topics) == [FamilyCreated.topic]
    assert await cases_of(sessionmaker, family_id) == []

    await OutboxDelivery(sessionmaker, stub_handlers(sessionmaker)).deliver_due()

    assert await cases_of(sessionmaker, family_id) == [(1, "planning")]
    live_client.get("/api/v1/family").raise_for_status()


async def test_the_handler_is_safe_to_run_twice(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    family_id, _ = create_family(live_client)
    family_created = stub_handlers(sessionmaker)[FamilyCreated][0]

    await family_created(FamilyCreated(family_id))
    await family_created(FamilyCreated(family_id))

    assert await cases_of(sessionmaker, family_id) == [(1, "planning")]
