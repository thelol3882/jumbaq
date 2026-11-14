import uuid

from sqlalchemy import ForeignKey, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from jumbaq.cases.domain import CaseStatus
from jumbaq.core.db import UUID_V7, Base, check_in


class CaseRow(Base):
    """`case` is a reserved word in PostgreSQL, so the table is `case_file`."""

    __tablename__ = "case_file"
    __table_args__ = (
        # Makes opening a case safe to run twice.
        UniqueConstraint("family_id", "number"),
        check_in("status", CaseStatus),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, server_default=UUID_V7)
    family_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("family.id"))
    number: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str]
