"""Database access and the unit of work, the one place that opens a transaction."""

import json
import logging
from collections.abc import Awaitable, Callable, Iterable
from datetime import datetime
from enum import StrEnum
from types import TracebackType
from typing import Any, ClassVar, Self

from sqlalchemy import CheckConstraint, DateTime, MetaData, Text, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from jumbaq.core.events import Event

logger = logging.getLogger(__name__)

Nudge = Callable[[], Awaitable[None]]

# Names for constraints and indexes, so migrations can drop and change them by name.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# PostgreSQL 18 makes time-ordered ids.
UUID_V7 = text("uuidv7()")


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        str: Text(),
        datetime: DateTime(timezone=True),
    }


def check_in(column: str, values: Iterable[StrEnum]) -> CheckConstraint:
    """A CHECK that the text column has one of the values of the enum."""
    allowed = ", ".join(f"'{value}'" for value in values)
    return CheckConstraint(f"{column} IN ({allowed})", name=column)


def create_engine(url: str) -> AsyncEngine:
    # Connects lazily, so the API starts even if PostgreSQL is still booting.
    return create_async_engine(url, pool_pre_ping=True, connect_args={"timeout": 5})


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


class UnitOfWork:
    """One transaction.

        async with FamiliesUoW(sessionmaker) as uow:
            await uow.families.add(family)
            await uow.commit()

    A module subclasses it and attaches its repositories in `_attach`. `await uow.commit()`
    is the only way to save: leaving the block without it, or with an error, rolls back.

    `publish` saves an event in the outbox in the same transaction, and after the commit the
    unit of work nudges the worker to deliver it.
    """

    session: AsyncSession

    def __init__(
        self,
        sessionmaker: async_sessionmaker[AsyncSession],
        *,
        nudge: Nudge | None = None,
    ) -> None:
        self._sessionmaker = sessionmaker
        self._nudge = nudge
        self._open = False
        self._published = False

    def _attach(self, session: AsyncSession) -> None:
        """Called once the session is open. A module creates its repositories here."""

    async def __aenter__(self) -> Self:
        if self._open:
            raise RuntimeError("this unit of work is already open")
        self.session = self._sessionmaker()
        self._open = True
        self._attach(self.session)
        return self

    async def publish(self, event: Event) -> None:
        await self.session.execute(
            text(
                "INSERT INTO outbox (family_id, topic, payload)"
                " VALUES (:family_id, :topic, CAST(:payload AS jsonb))"
            ),
            {
                "family_id": event.family_id,
                "topic": event.topic,
                "payload": json.dumps(event.to_payload()),
            },
        )
        self._published = True

    async def commit(self) -> None:
        await self.session.commit()
        await self._after_commit()

    async def _after_commit(self) -> None:
        if not (self._published and self._nudge):
            return
        self._published = False
        try:
            await self._nudge()
        except Exception:
            # The events are saved. The worker's regular check delivers them a bit later.
            logger.warning("could not nudge the worker about new events", exc_info=True)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if not self._open:
            return
        self._open = False
        try:
            await self.session.rollback()
        finally:
            await self.session.close()
