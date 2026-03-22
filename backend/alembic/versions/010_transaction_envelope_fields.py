"""Add budget_id and review_status to transactions.

budget_id links transactions to budget envelopes.
review_status: NULL=auto-assigned, 'pending'=needs review, 'confirmed'=manually reviewed.

Revision ID: 010_transaction_envelope_fields
Revises: 009_envelope_balances
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "010_transaction_envelope_fields"
down_revision = "009_envelope_balances"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("budget_id", UUID(as_uuid=True), sa.ForeignKey("budgets.id"), nullable=True),
    )
    op.create_index("ix_transactions_budget_id", "transactions", ["budget_id"])
    op.add_column(
        "transactions",
        sa.Column("review_status", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_index("ix_transactions_budget_id", "transactions")
    op.drop_column("transactions", "review_status")
    op.drop_column("transactions", "budget_id")
