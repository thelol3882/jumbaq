"""A model call whose draft the rules refused is logged as refused, not ok.

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-15 09:00:00.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_llm_call_outcome"), "llm_call", type_="check")
    op.create_check_constraint(
        op.f("ck_llm_call_outcome"),
        "llm_call",
        "outcome IN ('ok', 'bad_output', 'unavailable', 'refused')",
    )


def downgrade() -> None:
    # A refused call was an ok one before.
    op.execute("UPDATE llm_call SET outcome = 'ok' WHERE outcome = 'refused'")
    op.drop_constraint(op.f("ck_llm_call_outcome"), "llm_call", type_="check")
    op.create_check_constraint(
        op.f("ck_llm_call_outcome"),
        "llm_call",
        "outcome IN ('ok', 'bad_output', 'unavailable')",
    )
