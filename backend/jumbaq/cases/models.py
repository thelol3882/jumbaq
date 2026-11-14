import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.cases.domain import CaseStatus, Rank
from jumbaq.core.db import UUID_V7, Base, check_in


class CaseRow(Base):
    """`case` is a reserved word in PostgreSQL, so the table is `case_file`."""

    __tablename__ = "case_file"
    __table_args__ = (
        # Makes opening a case safe to run twice.
        UniqueConstraint("family_id", "number"),
        check_in("status", CaseStatus),
        check_in("rank", Rank),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"))
    number: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str]
    # Null until the case is planned. The title is a copy, so lists need not read the plan.
    title: Mapped[str | None]
    plan: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_fallback: Mapped[bool] = mapped_column(server_default=text("false"))
    played_episodes: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    accusation_attempts: Mapped[int] = mapped_column(SmallInteger, server_default=text("0"))
    rank: Mapped[str | None]
    solved_at: Mapped[datetime | None]
