"""The plan, the accusation and the rank of a case, and its new statuses.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-14 17:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("case_file", sa.Column("title", sa.Text(), nullable=True))
    op.add_column(
        "case_file", sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    op.add_column(
        "case_file",
        sa.Column("is_fallback", sa.Boolean(), server_default=sa.text("false"), nullable=False),
    )
    op.add_column(
        "case_file",
        sa.Column(
            "played_episodes", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
    )
    op.add_column(
        "case_file",
        sa.Column(
            "accusation_attempts", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
    )
    op.add_column("case_file", sa.Column("rank", sa.Text(), nullable=True))
    op.add_column("case_file", sa.Column("solved_at", sa.DateTime(timezone=True), nullable=True))
    # Autogenerate does not see CHECK constraints.
    op.drop_constraint(op.f("ck_case_file_status"), "case_file", type_="check")
    op.create_check_constraint(
        op.f("ck_case_file_status"),
        "case_file",
        "status IN ('planning', 'active', 'accusing', 'solved', 'failed')",
    )
    op.create_check_constraint(
        op.f("ck_case_file_rank"),
        "case_file",
        "rank IN ('chief_detective', 'detective', 'junior_detective')",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("ck_case_file_rank"), "case_file", type_="check")
    op.drop_constraint(op.f("ck_case_file_status"), "case_file", type_="check")
    op.create_check_constraint(op.f("ck_case_file_status"), "case_file", "status IN ('planning')")
    op.drop_column("case_file", "solved_at")
    op.drop_column("case_file", "rank")
    op.drop_column("case_file", "accusation_attempts")
    op.drop_column("case_file", "played_episodes")
    op.drop_column("case_file", "is_fallback")
    op.drop_column("case_file", "plan")
    op.drop_column("case_file", "title")
