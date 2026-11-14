import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.ai.domain import CallOutcome, TaskKind
from jumbaq.core.db import UUID_V7, Base, check_in


class LlmCallRow(Base):
    """Every model call, also the failed ones: the daily cap counts them, and they show the cost."""

    __tablename__ = "llm_call"
    __table_args__ = (
        # The daily cap counts the calls of one family since midnight.
        Index(None, "family_id", "created_at"),
        check_in("kind", TaskKind),
        check_in("outcome", CallOutcome),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"))
    kind: Mapped[str]
    provider: Mapped[str]
    model: Mapped[str]
    input_tokens: Mapped[int]
    output_tokens: Mapped[int]
    duration_ms: Mapped[int]
    outcome: Mapped[str]
    created_at: Mapped[datetime]


class AiControlRow(Base):
    """The owner switch of the model: one row with id 1, written from the server."""

    __tablename__ = "ai_control"
    __table_args__ = (
        CheckConstraint("id = 1", name="single_row"),
        CheckConstraint("daily_call_limit >= 0", name="limit_not_negative"),
    )

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    enabled: Mapped[bool]
    # NULL: the cap comes from the settings.
    daily_call_limit: Mapped[int | None]
    updated_at: Mapped[datetime]
