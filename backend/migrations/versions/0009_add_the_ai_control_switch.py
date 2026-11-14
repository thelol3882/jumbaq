"""The owner switch of the model: one row that turns it on or off and sets the daily cap.

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-15 10:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_control",
        sa.Column("id", sa.SmallInteger(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("daily_call_limit", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("daily_call_limit >= 0", name=op.f("ck_ai_control_limit_not_negative")),
        sa.CheckConstraint("id = 1", name=op.f("ck_ai_control_single_row")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_control")),
    )


def downgrade() -> None:
    op.drop_table("ai_control")
