import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index
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
