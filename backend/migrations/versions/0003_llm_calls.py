"""Every model call of a family, for the daily cap and the cost.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-14 15:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_call",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('case_plan', 'episode')", name=op.f("ck_llm_call_kind")),
        sa.CheckConstraint(
            "outcome IN ('ok', 'bad_output', 'unavailable')", name=op.f("ck_llm_call_outcome")
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.id"], name=op.f("fk_llm_call_family_id_family")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_llm_call")),
    )
    op.create_index(
        op.f("ix_llm_call_family_id_created_at"),
        "llm_call",
        ["family_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_llm_call_family_id_created_at"), table_name="llm_call")
    op.drop_table("llm_call")
