"""Add Payfit models

Revision ID: 002_payfit_models
Revises: 001_initial
Create Date: 2024-01-15

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_payfit_models'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create payfit_employees table
    op.create_table('payfit_employees',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payfit_id', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('registration_number', sa.String(length=50), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('nationality', sa.String(length=10), nullable=True),
        sa.Column('department', sa.String(length=255), nullable=True),
        sa.Column('position', sa.String(length=255), nullable=True),
        sa.Column('hire_date', sa.Date(), nullable=True),
        sa.Column('termination_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('manager_payfit_id', sa.String(length=255), nullable=True),
        sa.Column('local_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['local_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payfit_id')
    )
    op.create_index(op.f('ix_payfit_employees_email'), 'payfit_employees', ['email'], unique=False)
    op.create_index(op.f('ix_payfit_employees_payfit_id'), 'payfit_employees', ['payfit_id'], unique=False)
    
    # Create payfit_contracts table
    op.create_table('payfit_contracts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payfit_id', sa.String(length=255), nullable=False),
        sa.Column('payfit_employee_id', sa.String(length=255), nullable=False),
        sa.Column('contract_type', sa.String(length=100), nullable=True),
        sa.Column('job_title', sa.String(length=255), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('weekly_hours', sa.Float(), nullable=True),
        sa.Column('daily_hours', sa.Float(), nullable=True),
        sa.Column('annual_hours', sa.Float(), nullable=True),
        sa.Column('part_time_percentage', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('probation_end_date', sa.Date(), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payfit_employee_id'], ['payfit_employees.payfit_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payfit_id')
    )
    op.create_index(op.f('ix_payfit_contracts_payfit_id'), 'payfit_contracts', ['payfit_id'], unique=False)
    
    # Create payfit_absences table
    op.create_table('payfit_absences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('payfit_id', sa.String(length=255), nullable=False),
        sa.Column('payfit_employee_id', sa.String(length=255), nullable=False),
        sa.Column('absence_type', sa.String(length=100), nullable=False),
        sa.Column('absence_code', sa.String(length=50), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('duration_days', sa.Float(), nullable=True),
        sa.Column('duration_hours', sa.Float(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('raw_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_synced_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['payfit_employee_id'], ['payfit_employees.payfit_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payfit_id')
    )
    op.create_index(op.f('ix_payfit_absences_payfit_id'), 'payfit_absences', ['payfit_id'], unique=False)
    
    # Create payfit_sync_logs table
    op.create_table('payfit_sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sync_type', sa.String(length=50), nullable=False),
        sa.Column('sync_status', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('records_synced', sa.Integer(), nullable=True),
        sa.Column('records_created', sa.Integer(), nullable=True),
        sa.Column('records_updated', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('triggered_by', sa.String(length=255), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('payfit_sync_logs')
    op.drop_index(op.f('ix_payfit_absences_payfit_id'), table_name='payfit_absences')
    op.drop_table('payfit_absences')
    op.drop_index(op.f('ix_payfit_contracts_payfit_id'), table_name='payfit_contracts')
    op.drop_table('payfit_contracts')
    op.drop_index(op.f('ix_payfit_employees_payfit_id'), table_name='payfit_employees')
    op.drop_index(op.f('ix_payfit_employees_email'), table_name='payfit_employees')
    op.drop_table('payfit_employees')