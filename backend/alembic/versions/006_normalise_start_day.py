"""Normalise Budget.start_day to 28 for all existing budgets.

All periods now use global 28th-27th cycle via BudgetPeriod.
Per-budget start_day is retained but ignored by new code.

Revision ID: 006_normalise_start_day
Revises: 005_backfill_account_id_not_null
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "006_normalise_start_day"
down_revision = "005_backfill_account_id_not_null"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("UPDATE budgets SET start_day = 28 WHERE start_day != 28")


def downgrade() -> None:
    # Cannot restore original start_day values — data migration is one-way
    pass
