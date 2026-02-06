"""Backfill NULL account_id and add NOT NULL constraint.

Migration 002 added account_id as nullable. This migration:
1. Assigns any NULL account_id rows to the first available account
2. Deletes orphaned rows if no accounts exist
3. Adds NOT NULL constraint

Revision ID: 005
Revises: 004
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "005"
down_revision = "004"


def upgrade() -> None:
    conn = op.get_bind()

    # Find the first account to use as default
    result = conn.execute(sa.text("SELECT id FROM accounts ORDER BY created_at LIMIT 1"))
    first_account = result.fetchone()

    if first_account:
        account_id = str(first_account[0])

        # Backfill budgets with NULL account_id
        conn.execute(
            sa.text("UPDATE budgets SET account_id = :aid WHERE account_id IS NULL"),
            {"aid": account_id},
        )

        # Backfill category_rules with NULL account_id
        conn.execute(
            sa.text("UPDATE category_rules SET account_id = :aid WHERE account_id IS NULL"),
            {"aid": account_id},
        )
    else:
        # No accounts exist — delete orphaned records
        conn.execute(sa.text("DELETE FROM budgets WHERE account_id IS NULL"))
        conn.execute(sa.text("DELETE FROM category_rules WHERE account_id IS NULL"))

    # Now add NOT NULL constraint
    op.alter_column("budgets", "account_id", existing_type=UUID(as_uuid=True), nullable=False)
    op.alter_column("category_rules", "account_id", existing_type=UUID(as_uuid=True), nullable=False)


def downgrade() -> None:
    op.alter_column("category_rules", "account_id", existing_type=UUID(as_uuid=True), nullable=True)
    op.alter_column("budgets", "account_id", existing_type=UUID(as_uuid=True), nullable=True)
