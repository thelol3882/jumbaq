"""The monthly subscriptions of families and the payment events already handled.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-14 17:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "payment_event",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("provider_event_id", sa.Text(), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.id"], name=op.f("fk_payment_event_family_id_family")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_event")),
        sa.UniqueConstraint("provider_event_id", name=op.f("uq_payment_event_provider_event_id")),
    )
    op.create_table(
        "subscription",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuidv7()"), nullable=False),
        sa.Column("family_id", sa.Uuid(), nullable=False),
        sa.Column("provider_ref", sa.Text(), nullable=False),
        sa.Column("customer_ref", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('incomplete', 'incomplete_expired', 'trialing', 'active',"
            " 'past_due', 'unpaid', 'paused', 'canceled')",
            name=op.f("ck_subscription_status"),
        ),
        sa.ForeignKeyConstraint(
            ["family_id"], ["family.id"], name=op.f("fk_subscription_family_id_family")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscription")),
        sa.UniqueConstraint("provider_ref", name=op.f("uq_subscription_provider_ref")),
    )
    op.create_index(op.f("ix_subscription_family_id"), "subscription", ["family_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_subscription_family_id"), table_name="subscription")
    op.drop_table("subscription")
    op.drop_table("payment_event")
