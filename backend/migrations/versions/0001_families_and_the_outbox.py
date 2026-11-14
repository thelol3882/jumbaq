"""Families with their kids, and the transactional outbox.

Revision ID: 0001
Revises:
Create Date: 2026-11-14 15:04:24.107519
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "family",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("session_token_hash", sa.Text(), nullable=False),
        sa.Column("rooms", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("objects", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_family")),
        sa.UniqueConstraint("session_token_hash", name=op.f("uq_family_session_token_hash")),
    )
    op.create_table(
        "kid",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("nickname", sa.Text(), nullable=False),
        sa.Column("age", sa.SmallInteger(), nullable=False),
        sa.CheckConstraint("age BETWEEN 1 AND 18", name=op.f("ck_kid_age")),
        sa.ForeignKeyConstraint(["family_id"], ["family.id"], name=op.f("fk_kid_family_id_family")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_kid")),
    )
    op.create_index(op.f("ix_kid_family_id"), "kid", ["family_id"], unique=False)
    op.create_table(
        "outbox",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("topic", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "next_attempt_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.id"], name=op.f("fk_outbox_family_id_family")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outbox")),
    )
    op.create_index(
        op.f("ix_outbox_next_attempt_at"),
        "outbox",
        ["next_attempt_at"],
        unique=False,
        postgresql_where=sa.text("processed_at IS NULL AND failed_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_outbox_next_attempt_at"),
        table_name="outbox",
        postgresql_where=sa.text("processed_at IS NULL AND failed_at IS NULL"),
    )
    op.drop_table("outbox")
    op.drop_index(op.f("ix_kid_family_id"), table_name="kid")
    op.drop_table("kid")
    op.drop_table("family")
