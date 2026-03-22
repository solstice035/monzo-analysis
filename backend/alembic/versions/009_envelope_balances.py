"""Create envelope_balances table.

Tracks allocated, original_allocated, and rollover per budget per period.
`spent` is intentionally NOT stored — computed on read via SUM query.
`account_id` is intentionally omitted — derivable via joins.

Revision ID: 009_envelope_balances
Revises: 008_budget_periods
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "009_envelope_balances"
down_revision = "008_budget_periods"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "envelope_balances",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("budget_id", UUID(as_uuid=True), sa.ForeignKey("budgets.id"), nullable=False, index=True),
        sa.Column("period_id", UUID(as_uuid=True), sa.ForeignKey("budget_periods.id"), nullable=False, index=True),
        sa.Column("allocated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("original_allocated", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rollover", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("budget_id", "period_id", name="uq_envelope_balances_budget_period"),
    )


def downgrade() -> None:
    op.drop_table("envelope_balances")
