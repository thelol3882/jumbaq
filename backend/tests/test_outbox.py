"""The outbox claims a row, runs its handlers with no transaction open, then marks it."""

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jumbaq.core.context import is_last_attempt
from jumbaq.core.db import UnitOfWork
from jumbaq.core.events import Event
from jumbaq.core.outbox import LEASE, MAX_ATTEMPTS, Handler, OutboxDelivery, OutboxRow
from tests.flows import create_family, stub_handlers

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("quiet_outbox")]

Sessionmaker = async_sessionmaker[AsyncSession]


@dataclass(frozen=True)
class Ping(Event):
    topic: ClassVar[str] = "tests.ping"


async def row_of(sessionmaker: Sessionmaker, row_id: uuid.UUID) -> OutboxRow:
    async with sessionmaker() as session:
        return await session.get_one(OutboxRow, row_id)


async def make_due(sessionmaker: Sessionmaker, row_id: uuid.UUID) -> None:
    async with sessionmaker() as session:
        await session.execute(
            text("UPDATE outbox SET next_attempt_at = now() WHERE id = :id"), {"id": row_id}
        )
        await session.commit()


async def deliver(delivery: OutboxDelivery, row_id: uuid.UUID) -> None:
    """Delivers this one row. Other tests share the database and may run `deliver_due()` at the
    same time, with handlers that do not know the ping: a row left due is counted as failed by
    them, so the tests do not wait for the selection of due rows."""
    await delivery._deliver(row_id)


async def ping_with(
    sessionmaker: Sessionmaker, live_client: TestClient, handler: Handler
) -> tuple[OutboxDelivery, uuid.UUID]:
    """A delivery that runs `handler` for a new ping row. It has the app's handlers too, so rows
    of other tests running now are not harmed."""
    family_id, _ = create_family(live_client)
    async with UnitOfWork(sessionmaker) as uow:
        await uow.publish(Ping(family_id))
        await uow.commit()
    async with sessionmaker() as session:
        row_id = await session.scalar(
            select(OutboxRow.id).where(
                OutboxRow.family_id == family_id, OutboxRow.topic == Ping.topic
            )
        )
    assert row_id is not None
    return OutboxDelivery(sessionmaker, stub_handlers(sessionmaker) | {Ping: [handler]}), row_id


async def test_a_processed_row_is_marked_and_counted(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    async def handler(event: Event) -> None:
        pass

    delivery, row_id = await ping_with(sessionmaker, live_client, handler)

    await deliver(delivery, row_id)

    row = await row_of(sessionmaker, row_id)
    assert row.processed_at is not None and row.attempts == 1 and row.last_error is None


async def test_a_row_that_is_running_is_not_taken_by_a_second_delivery(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    runs: list[int] = []
    during: list[OutboxRow] = []

    async def handler(event: Event) -> None:
        runs.append(1)
        # A second worker looks while the first one runs: the lease hides the row.
        await delivery.deliver_due()
        during.append(await row_of(sessionmaker, row_id))

    delivery, row_id = await ping_with(sessionmaker, live_client, handler)

    await deliver(delivery, row_id)

    assert runs == [1]
    # The claim was committed before the handler ran: the attempt is counted and leased.
    assert during[0].attempts == 1 and during[0].processed_at is None
    assert during[0].next_attempt_at > during[0].created_at + LEASE - timedelta(minutes=1)
    assert (await row_of(sessionmaker, row_id)).processed_at is not None


async def test_a_run_counts_its_attempt_even_if_the_handler_raises(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    async def handler(event: Event) -> None:
        raise RuntimeError("boom")

    delivery, row_id = await ping_with(sessionmaker, live_client, handler)

    await deliver(delivery, row_id)

    row = await row_of(sessionmaker, row_id)
    assert (row.attempts, row.last_error, row.processed_at) == (1, "RuntimeError", None)
    # The wait of the first failure, not the lease.
    assert row.next_attempt_at < row.created_at + timedelta(minutes=1)
    assert row.failed_at is None


async def test_the_handler_knows_the_last_attempt_and_the_row_dies_after_it(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    seen: list[bool] = []

    async def handler(event: Event) -> None:
        seen.append(is_last_attempt())
        raise RuntimeError("boom")

    delivery, row_id = await ping_with(sessionmaker, live_client, handler)

    for _ in range(MAX_ATTEMPTS):
        await make_due(sessionmaker, row_id)
        await deliver(delivery, row_id)

    assert seen == [False] * (MAX_ATTEMPTS - 1) + [True]
    row = await row_of(sessionmaker, row_id)
    assert row.attempts == MAX_ATTEMPTS and row.failed_at is not None
    assert not is_last_attempt()


async def test_a_row_whose_last_attempt_was_lost_is_dead_and_not_run_again(
    live_client: TestClient, sessionmaker: Sessionmaker
) -> None:
    runs: list[int] = []

    async def handler(event: Event) -> None:
        runs.append(1)

    delivery, row_id = await ping_with(sessionmaker, live_client, handler)
    async with sessionmaker() as session:
        await session.execute(
            text("UPDATE outbox SET attempts = :n WHERE id = :id"),
            {"n": MAX_ATTEMPTS, "id": row_id},
        )
        await session.commit()

    await deliver(delivery, row_id)

    assert runs == []
    row = await row_of(sessionmaker, row_id)
    assert row.failed_at is not None and row.last_error == "LeaseExpired"
