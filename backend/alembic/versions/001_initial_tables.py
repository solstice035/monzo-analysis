"""Initial database tables.

Revision ID: 001_initial_tables
Revises:
Create Date: 2026-01-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision = '001_initial_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accounts table
    op.create_table(
        'accounts',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('monzo_id', sa.String(255), unique=True, nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('monzo_id', sa.String(255), unique=True, nullable=False),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('merchant_name', sa.String(255), nullable=True),
        sa.Column('monzo_category', sa.String(100), nullable=True),
        sa.Column('custom_category', sa.String(100), nullable=True),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_payload', JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_transactions_account', 'transactions', ['account_id'])
    op.create_index('idx_transactions_created', 'transactions', ['created_at'])
    op.create_index('idx_transactions_category', 'transactions', ['custom_category'])

    # Create pots table
    op.create_table(
        'pots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('monzo_id', sa.String(255), unique=True, nullable=False),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('accounts.id'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('balance', sa.Integer, nullable=False),
        sa.Column('deleted', sa.Boolean, default=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create budgets table
    op.create_table(
        'budgets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('amount', sa.Integer, nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('start_day', sa.Integer, default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create category_rules table
    op.create_table(
        'category_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('conditions', JSON, nullable=False),
        sa.Column('target_category', sa.String(100), nullable=False),
        sa.Column('priority', sa.Integer, default=0),
        sa.Column('enabled', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('idx_category_rules_priority', 'category_rules', ['priority'], postgresql_ops={'priority': 'DESC'})

    # Create sync_log table
    op.create_table(
        'sync_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('transactions_synced', sa.Integer, default=0),
        sa.Column('error', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create auth table
    op.create_table(
        'auth',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('access_token', sa.Text, nullable=False),
        sa.Column('refresh_token', sa.Text, nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # Create settings table
    op.create_table(
        'settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', JSON, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('settings')
    op.drop_table('auth')
    op.drop_table('sync_log')
    op.drop_index('idx_category_rules_priority', 'category_rules')
    op.drop_table('category_rules')
    op.drop_table('budgets')
    op.drop_table('pots')
    op.drop_index('idx_transactions_category', 'transactions')
    op.drop_index('idx_transactions_created', 'transactions')
    op.drop_index('idx_transactions_account', 'transactions')
    op.drop_table('transactions')
    op.drop_table('accounts')
