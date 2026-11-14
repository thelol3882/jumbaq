"""Remember when a canceled but still paid subscription ends.

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-15 01:53:23.706952
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "subscription", sa.Column("cancels_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("subscription", "cancels_at")
