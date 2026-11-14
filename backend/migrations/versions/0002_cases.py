"""Cases of a family. Only case 1 for now, opened when the family is created.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-14 15:05:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "case_file",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.CheckConstraint("status IN ('planning')", name=op.f("ck_case_file_status")),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.id"], name=op.f("fk_case_file_family_id_family")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_case_file")),
        sa.UniqueConstraint("family_id", "number", name=op.f("uq_case_file_family_id_number")),
    )


def downgrade() -> None:
    op.drop_table("case_file")
