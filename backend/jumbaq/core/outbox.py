"""The transactional outbox.

`UnitOfWork.publish` writes a row in the transaction of the change. The worker delivers it in
three steps, and no transaction is open while the handlers run, because they call the model
and can take minutes:

1. Claim: a short unit of work locks the row with SKIP LOCKED, so two workers never take the
   same row, counts the attempt and moves `next_attempt_at` a lease ahead. Then it commits.
2. Run the handlers.
3. Finish: a new short unit of work marks the row processed, or on a failure stores the error
   and the wait for the next attempt. After the last attempt the row gets `failed_at`: our
   dead letter queue.

A worker that dies in step 2 leaves the row with its lease, so another worker takes it when
the lease ends, and the attempt has already been counted. If the one that died was running the
last attempt, the row gets one more run (attempt MAX_ATTEMPTS + 1) as a last attempt, so the
handlers still give their built-in result. That run is never repeated: if it fails or is lost
too, the row gets `failed_at`.

Handlers must be safe to run twice: the worker can stop after a handler and before the row
is marked.
"""

import logging
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.core.context import family_id_var, last_attempt_var
from jumbaq.core.db import UUID_V7, Base, UnitOfWork
from jumbaq.core.events import Event
from jumbaq.core.tasks import DELIVER_OUTBOX, TaskQueue

logger = logging.getLogger(__name__)

Handler = Callable[[Event], Awaitable[None]]

# The wait after the 1st, 2nd, 3rd and 4th failure. The 5th failure is the last.
BACKOFF = (
    timedelta(seconds=10),
    timedelta(minutes=1),
    timedelta(minutes=5),
    timedelta(minutes=30),
)
MAX_ATTEMPTS = len(BACKOFF) + 1
# How long a claimed row belongs to its worker. Longer than the arq job timeout (5 minutes) and
# the model call (up to 4 minutes), so a row that is still running is not taken by a second
# worker, and short enough that a row of a dead worker is not forgotten for long.
LEASE = timedelta(minutes=10)


class OutboxRow(Base):
    __tablename__ = "outbox"
    __table_args__ = (
        Index(
            None,
            "next_attempt_at",
            postgresql_where=text("processed_at IS NULL AND failed_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"))
    topic: Mapped[str]
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    attempts: Mapped[int] = mapped_column(server_default=text("0"))
    next_attempt_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # The class of the last error only: a message can hold a secret.
    last_error: Mapped[str | None]
    processed_at: Mapped[datetime | None]
    failed_at: Mapped[datetime | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


def nudge_worker(queue: TaskQueue) -> Callable[[], Awaitable[None]]:

    async def nudge() -> None:
        await queue.enqueue_job(DELIVER_OUTBOX)

    return nudge


class OutboxDelivery:
    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        handlers: Mapping[type[Event], Sequence[Handler]],
    ) -> None:
        self._sessionmaker = sessionmaker
        self._events = {event.topic: (event, tuple(found)) for event, found in handlers.items()}

    async def deliver_due(self, limit: int = 100) -> int:
        async with self._sessionmaker() as session:
            due = (
                await session.execute(
                    text(
                        "SELECT id, family_id FROM outbox"
                        " WHERE processed_at IS NULL AND failed_at IS NULL"
                        " AND next_attempt_at <= now()"
                        " ORDER BY next_attempt_at LIMIT :limit"
                    ),
                    {"limit": limit},
                )
            ).all()
        delivered = 0
        for row_id, family_id in due:
            family_id_var.set(str(family_id))
            delivered += await self._deliver(row_id)
        family_id_var.set("-")
        return delivered

    async def _deliver(self, row_id: uuid.UUID) -> bool:
        claimed = await self._claim(row_id)
        if claimed is None:
            return False  # another worker has it, it is leased, or it is done
        topic, payload, attempts = claimed
        # Tells the handlers whether a failure now is the end, so they can give a built-in
        # result instead of raising.
        token = last_attempt_var.set(attempts >= MAX_ATTEMPTS)
        try:
            await self._run_handlers(topic, payload)
        except Exception as error:
            await self._failed(row_id, topic, attempts, error)
            return False
        finally:
            last_attempt_var.reset(token)
        async with UnitOfWork(self._sessionmaker) as uow:
            await uow.session.execute(
                text("UPDATE outbox SET processed_at = now() WHERE id = :id"), {"id": row_id}
            )
            await uow.commit()
        return True

    async def _claim(self, row_id: uuid.UUID) -> tuple[str, dict[str, Any], int] | None:
        """Counts the attempt and leases the row. None when there is nothing to run."""
        async with UnitOfWork(self._sessionmaker) as uow:
            row = (
                await uow.session.execute(
                    text(
                        "SELECT topic, payload, attempts FROM outbox"
                        " WHERE id = :id AND processed_at IS NULL AND failed_at IS NULL"
                        " AND next_attempt_at <= now()"
                        " FOR UPDATE SKIP LOCKED"
                    ),
                    {"id": row_id},
                )
            ).first()
            if row is None:
                return None
            topic, payload, attempts = row
            if attempts > MAX_ATTEMPTS:
                # The extra run was lost too. It never runs a second time.
                logger.error("event %s %s lost its extra run and is dead", topic, row_id)
                await uow.session.execute(
                    text(
                        "UPDATE outbox SET failed_at = now(), last_error = 'LeaseExpired'"
                        " WHERE id = :id"
                    ),
                    {"id": row_id},
                )
                await uow.commit()
                return None
            await uow.session.execute(
                text(
                    "UPDATE outbox SET attempts = attempts + 1,"
                    " next_attempt_at = now() + :lease WHERE id = :id"
                ),
                {"id": row_id, "lease": LEASE},
            )
            await uow.commit()
            return topic, payload, attempts + 1

    async def _run_handlers(self, topic: str, payload: dict[str, Any]) -> None:
        if topic not in self._events:
            raise LookupError(f"no event class for the topic {topic}")
        event_class, handlers = self._events[topic]
        event = event_class.from_payload(payload)
        for handler in handlers:
            await handler(event)

    async def _failed(self, row_id: uuid.UUID, topic: str, attempts: int, error: Exception) -> None:
        """`attempts` is already counted by the claim."""
        values: dict[str, Any] = {"id": row_id, "error": type(error).__name__}
        if attempts >= MAX_ATTEMPTS:
            logger.error(
                "event %s %s failed %s times and is dead", topic, row_id, attempts, exc_info=error
            )
            sql = "failed_at = now()"
        else:
            logger.warning(
                "event %s %s failed, attempt %s", topic, row_id, attempts, exc_info=error
            )
            sql = "next_attempt_at = now() + :wait"
            values["wait"] = BACKOFF[attempts - 1]
        async with UnitOfWork(self._sessionmaker) as uow:
            await uow.session.execute(
                text(f"UPDATE outbox SET last_error = :error, {sql} WHERE id = :id"), values
            )
            await uow.commit()
