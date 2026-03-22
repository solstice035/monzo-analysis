"""Create budget_periods table.

Represents one month's budget period (28th to 27th cycle).
UNIQUE(account_id, period_start) prevents duplicate periods.

Revision ID: 008_budget_periods
Revises: 007_budget_soft_delete
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "008_budget_periods"
down_revision = "007_budget_soft_delete"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "budget_periods",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False, index=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("account_id", "period_start", name="uq_budget_periods_account_start"),
    )


def downgrade() -> None:
    op.drop_table("budget_periods")
