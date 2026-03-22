"""Add target_budget_id FK and is_exclusion flag to category_rules.

Phase 2.5a — ADD COLUMN + backfill. Dual-column period begins.
Both target_category (old) and target_budget_id (new) coexist for ≥48h.

Revision ID: 013_add_target_budget_id_fk
Revises: 012_review_fixes
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "013_add_target_budget_id_fk"
down_revision = "012_review_fixes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add the new FK column (nullable — exclusion rules have no target budget)
    op.add_column(
        "category_rules",
        sa.Column("target_budget_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_category_rules_target_budget_id",
        "category_rules",
        "budgets",
        ["target_budget_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 2. Backfill: match existing target_category → Budget.id (case-insensitive, same account)
    op.execute("""
        UPDATE category_rules cr
        SET target_budget_id = b.id
        FROM budgets b
        WHERE LOWER(b.category) = LOWER(cr.target_category)
          AND b.account_id = cr.account_id
          AND b.deleted_at IS NULL
    """)

    # 3. Add is_exclusion flag
    op.add_column(
        "category_rules",
        sa.Column("is_exclusion", sa.Boolean(), nullable=False, server_default="false"),
    )

    # 4. Mark exclusion rules (savings/income/transfers or orphaned rules with no target budget)
    op.execute("""
        UPDATE category_rules
        SET is_exclusion = TRUE
        WHERE target_category IN ('savings', 'income', 'transfers')
           OR (target_budget_id IS NULL AND target_category IS NOT NULL)
    """)

    # 5. Index on target_budget_id for join performance
    op.create_index(
        "ix_category_rules_target_budget_id",
        "category_rules",
        ["target_budget_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_category_rules_target_budget_id", "category_rules")
    op.drop_column("category_rules", "is_exclusion")
    op.drop_constraint("fk_category_rules_target_budget_id", "category_rules", type_="foreignkey")
    op.drop_column("category_rules", "target_budget_id")
