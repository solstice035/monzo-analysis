"""Code review fixes: CHECK constraints on status fields, index on deleted_at.

Revision ID: 012_review_fixes
Revises: 011_category_rule_flags
Create Date: 2026-03-22
"""

from alembic import op

revision = "012_review_fixes"
down_revision = "011_category_rule_flags"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # CHECK constraint on budget_periods.status
    op.create_check_constraint(
        "ck_budget_periods_status",
        "budget_periods",
        "status IN ('active', 'closing', 'closed')",
    )

    # Index on budget_periods.status for active-period queries
    op.create_index("ix_budget_periods_status", "budget_periods", ["status"])

    # CHECK constraint on transactions.review_status
    op.create_check_constraint(
        "ck_transactions_review_status",
        "transactions",
        "review_status IN ('pending', 'confirmed', 'excluded') OR review_status IS NULL",
    )

    # Index on budgets.deleted_at for soft-delete filtering
    op.create_index("ix_budgets_deleted_at", "budgets", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_budgets_deleted_at", "budgets")
    op.drop_constraint("ck_transactions_review_status", "transactions")
    op.drop_index("ix_budget_periods_status", "budget_periods")
    op.drop_constraint("ck_budget_periods_status", "budget_periods")
