"""Add balance and spend_today fields to accounts.

Revision ID: 004
Revises: 003
"""

from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"


def upgrade() -> None:
    op.add_column("accounts", sa.Column("balance", sa.Integer(), server_default="0", nullable=False))
    op.add_column("accounts", sa.Column("spend_today", sa.Integer(), server_default="0", nullable=False))


def downgrade() -> None:
    op.drop_column("accounts", "spend_today")
    op.drop_column("accounts", "balance")
