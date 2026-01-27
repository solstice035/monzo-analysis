"""Add budget_groups table and sinking fund support.

Revision ID: 003_add_budget_groups
Revises: 002_add_account_id
Create Date: 2026-01-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '003_add_budget_groups'
down_revision = '002_add_account_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create budget_groups table
    op.create_table(
        'budget_groups',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_budget_groups_account', 'budget_groups', ['account_id'])

    # Add new columns to budgets table
    # group_id: Reference to budget_groups (nullable initially for migration)
    op.add_column(
        'budgets',
        sa.Column('group_id', UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_budgets_group_id',
        'budgets',
        'budget_groups',
        ['group_id'],
        ['id']
    )
    op.create_index('idx_budgets_group', 'budgets', ['group_id'])

    # name: Line item name (e.g., "Elodie Piano")
    op.add_column(
        'budgets',
        sa.Column('name', sa.String(200), nullable=True)
    )

    # period_type: weekly, monthly, quarterly, annual, bi-annual
    op.add_column(
        'budgets',
        sa.Column('period_type', sa.String(20), nullable=True, server_default='monthly')
    )

    # annual_amount: Total target for sinking funds (in pence)
    op.add_column(
        'budgets',
        sa.Column('annual_amount', sa.Integer, nullable=True)
    )

    # target_month: When the annual expense is due (1-12)
    op.add_column(
        'budgets',
        sa.Column('target_month', sa.Integer, nullable=True)
    )

    # linked_pot_id: Monzo Pot ID for pot-backed budgets
    op.add_column(
        'budgets',
        sa.Column('linked_pot_id', sa.String(100), nullable=True)
    )

    # Note: Existing budgets will have null group_id and name.
    # The application will need to handle migration of existing budgets
    # by creating a "Miscellaneous" group and assigning orphaned budgets to it.
    # The API will enforce group_id on all new budgets going forward.


def downgrade() -> None:
    # Remove new columns from budgets
    op.drop_column('budgets', 'linked_pot_id')
    op.drop_column('budgets', 'target_month')
    op.drop_column('budgets', 'annual_amount')
    op.drop_column('budgets', 'period_type')
    op.drop_column('budgets', 'name')
    op.drop_index('idx_budgets_group', 'budgets')
    op.drop_constraint('fk_budgets_group_id', 'budgets', type_='foreignkey')
    op.drop_column('budgets', 'group_id')

    # Drop budget_groups table
    op.drop_index('idx_budget_groups_account', 'budget_groups')
    op.drop_table('budget_groups')
