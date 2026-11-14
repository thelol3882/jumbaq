import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, SmallInteger, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.core.db import UUID_V7, Base, check_in
from jumbaq.episodes.domain import EpisodeStatus


class EpisodeRow(Base):
    __tablename__ = "episode"
    __table_args__ = (
        # Makes creating an episode safe to run twice.
        UniqueConstraint("case_id", "number"),
        # The current episode is the newest one of the family.
        Index(None, "family_id", "case_number", "number"),
        check_in("status", EpisodeStatus),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"))
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("case_file.id"))
    # A copy of the case's number, so the newest episode is found without cases' table.
    case_number: Mapped[int] = mapped_column(SmallInteger)
    number: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str]
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    answer: Mapped[str | None]
    resolution: Mapped[str | None]
    available_at: Mapped[datetime | None]
    played_at: Mapped[datetime | None]
    is_fallback: Mapped[bool] = mapped_column(server_default=text("false"))
    used_fallback_riddle: Mapped[bool] = mapped_column(server_default=text("false"))
    created_at: Mapped[datetime]
