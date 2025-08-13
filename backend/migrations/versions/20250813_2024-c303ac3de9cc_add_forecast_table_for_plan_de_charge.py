"""Add forecast table for plan de charge

Revision ID: c303ac3de9cc
Revises: bdb9cbb84083
Create Date: 2025-08-13 20:24:22.287717

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c303ac3de9cc'
down_revision = 'bdb9cbb84083'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create forecasts table
    op.create_table('forecasts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('collaborator_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('modified_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collaborator_id'], ['gryzzly_collaborators.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['modified_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['gryzzly_projects.id'], ),
        sa.ForeignKeyConstraint(['task_id'], ['gryzzly_tasks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_forecasts_collaborator_date', 'forecasts', ['collaborator_id', 'date'], unique=False)
    op.create_index('ix_forecasts_date', 'forecasts', ['date'], unique=False)
    op.create_index('ix_forecasts_project', 'forecasts', ['project_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_forecasts_project', table_name='forecasts')
    op.drop_index('ix_forecasts_date', table_name='forecasts')
    op.drop_index('ix_forecasts_collaborator_date', table_name='forecasts')
    
    # Drop table
    op.drop_table('forecasts')