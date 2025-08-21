"""Add azure_id to users table for SSO

Revision ID: d4f5e6g7h8i9
Revises: c303ac3de9cc
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4f5e6g7h8i9'
down_revision = 'c303ac3de9cc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add azure_id column to users table."""
    # Check if column already exists
    from alembic import context
    conn = context.get_bind()
    result = conn.execute(sa.text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'users' AND column_name = 'azure_id'"
    ))
    if not result.fetchone():
        op.add_column('users', sa.Column('azure_id', sa.String(length=255), nullable=True))
        op.create_index('ix_users_azure_id', 'users', ['azure_id'])


def downgrade() -> None:
    """Remove azure_id column from users table."""
    op.drop_index('ix_users_azure_id', table_name='users')
    op.drop_column('users', 'azure_id')