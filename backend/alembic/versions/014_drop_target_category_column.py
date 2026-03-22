"""HOLD — Deploy separately after 48h dual-column observation.

Drop the legacy target_category string column from category_rules.
Only deploy after verifying:
  1. All code paths use target_budget_id (not target_category)
  2. 48+ hours of dual-column operation with no issues
  3. Zero non-exclusion rules with NULL target_budget_id

Revision ID: 014_drop_target_category_column
Revises: 013_add_target_budget_id_fk
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "014_drop_target_category_column"
down_revision = "013_add_target_budget_id_fk"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # HOLD — DO NOT RUN until 48h+ after migration 013.
    # Verify first:
    #   SELECT COUNT(*) FROM category_rules
    #   WHERE is_exclusion = FALSE AND target_budget_id IS NULL;
    #   -- Must be 0
    op.drop_column("category_rules", "target_category")


def downgrade() -> None:
    op.add_column(
        "category_rules",
        sa.Column("target_category", sa.String(100), nullable=True),
    )
    # Note: backfilling target_category from target_budget_id would require
    # joining budgets to get the category string. Manual intervention needed.
