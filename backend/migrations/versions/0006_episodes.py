"""The episodes of a case: one evening each, with its riddle and answer.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-14 18:30:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "episode",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("case_number", sa.SmallInteger(), nullable=False),
        sa.Column("number", sa.SmallInteger(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("answer", sa.Text(), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("played_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_fallback", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "used_fallback_riddle", sa.Boolean(), server_default=sa.text("false"), nullable=False
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('requested', 'generating', 'ready', 'played', 'failed')",
            name=op.f("ck_episode_status"),
        ),
        sa.ForeignKeyConstraint(
            ["case_id"], ["case_file.id"], name=op.f("fk_episode_case_id_case_file")
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.id"], name=op.f("fk_episode_family_id_family")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_episode")),
        sa.UniqueConstraint("case_id", "number", name=op.f("uq_episode_case_id_number")),
    )
    op.create_index(
        op.f("ix_episode_family_id_case_number_number"),
        "episode",
        ["family_id", "case_number", "number"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_episode_family_id_case_number_number"), table_name="episode")
    op.drop_table("episode")
