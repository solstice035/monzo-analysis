"""Add account_id to budgets and category_rules tables.

Revision ID: 002_add_account_id
Revises: 001_initial_tables
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '002_add_account_id'
down_revision = '001_initial_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add account_id to budgets table
    # First add as nullable, then we'll handle existing data
    op.add_column(
        'budgets',
        sa.Column('account_id', UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_budgets_account_id',
        'budgets',
        'accounts',
        ['account_id'],
        ['id']
    )
    op.create_index('idx_budgets_account', 'budgets', ['account_id'])

    # Add account_id to category_rules table
    op.add_column(
        'category_rules',
        sa.Column('account_id', UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_category_rules_account_id',
        'category_rules',
        'accounts',
        ['account_id'],
        ['id']
    )
    op.create_index('idx_category_rules_account', 'category_rules', ['account_id'])

    # Note: After migration, existing budgets/rules without account_id
    # will need to be deleted or manually assigned to an account.
    # The API will enforce account_id on all new records.


def downgrade() -> None:
    # Remove from category_rules
    op.drop_index('idx_category_rules_account', 'category_rules')
    op.drop_constraint('fk_category_rules_account_id', 'category_rules', type_='foreignkey')
    op.drop_column('category_rules', 'account_id')

    # Remove from budgets
    op.drop_index('idx_budgets_account', 'budgets')
    op.drop_constraint('fk_budgets_account_id', 'budgets', type_='foreignkey')
    op.drop_column('budgets', 'account_id')
