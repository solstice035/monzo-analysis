"""Add is_income and is_transfer flags to category_rules.

Income rules (e.g. Sophie's contribution) and transfer rules
skip envelope assignment entirely.

Revision ID: 011_category_rule_flags
Revises: 010_transaction_envelope_fields
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "011_category_rule_flags"
down_revision = "010_transaction_envelope_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "category_rules",
        sa.Column("is_income", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "category_rules",
        sa.Column("is_transfer", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade() -> None:
    op.drop_column("category_rules", "is_transfer")
    op.drop_column("category_rules", "is_income")
