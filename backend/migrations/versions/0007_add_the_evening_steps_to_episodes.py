"""The three steps of an evening: answer, decode, strike, with their attempts and times.

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-14 20:15:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("episode", sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "episode",
        sa.Column(
            "decode_attempts", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
    )
    op.add_column("episode", sa.Column("decoded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "episode",
        sa.Column(
            "strike_attempts", sa.SmallInteger(), server_default=sa.text("0"), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("episode", "strike_attempts")
    op.drop_column("episode", "decoded_at")
    op.drop_column("episode", "decode_attempts")
    op.drop_column("episode", "answered_at")
