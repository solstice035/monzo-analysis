"""Add deleted_at to budgets for soft-delete support.

Soft-deleted budgets are skipped during period rollover but
preserve their EnvelopeBalance history for audit.

Revision ID: 007_budget_soft_delete
Revises: 006_normalise_start_day
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "007_budget_soft_delete"
down_revision = "006_normalise_start_day"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "budgets",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("budgets", "deleted_at")
