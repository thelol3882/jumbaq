import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, SmallInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.core.db import UUID_V7, Base


class FamilyRow(Base):
    __tablename__ = "family"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    session_token_hash: Mapped[str] = mapped_column(unique=True)
    rooms: Mapped[list[str]] = mapped_column(JSONB)
    objects: Mapped[list[str]] = mapped_column(JSONB)
    created_at: Mapped[datetime]


class KidRow(Base):
    __tablename__ = "kid"
    __table_args__ = (CheckConstraint("age BETWEEN 1 AND 18", name="age"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"), index=True)
    nickname: Mapped[str]
    age: Mapped[int] = mapped_column(SmallInteger)
