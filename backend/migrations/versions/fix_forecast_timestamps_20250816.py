"""Fix forecast timestamp columns to use timezone

Revision ID: fix_forecast_timestamps_20250816
Revises: 20250115_add_azure_id_to_users
Create Date: 2025-08-16 22:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fix_forecast_timestamps_20250816'
down_revision = 'd4f5e6g7h8i9'
branch_labels = None
depends_on = None


def upgrade():
    # Convert created_at and updated_at to TIMESTAMP WITH TIME ZONE
    op.execute("""
        ALTER TABLE forecasts 
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE 
        USING created_at AT TIME ZONE 'UTC'
    """)
    
    op.execute("""
        ALTER TABLE forecasts 
        ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE 
        USING updated_at AT TIME ZONE 'UTC'
    """)
    
    # Set default values
    op.execute("""
        ALTER TABLE forecasts 
        ALTER COLUMN created_at SET DEFAULT NOW()
    """)
    
    op.execute("""
        ALTER TABLE forecasts 
        ALTER COLUMN updated_at SET DEFAULT NOW()
    """)
    
    # Create or replace the trigger for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)
    
    # Drop and recreate trigger
    op.execute("DROP TRIGGER IF EXISTS update_forecasts_updated_at ON forecasts")
    
    op.execute("""
        CREATE TRIGGER update_forecasts_updated_at 
        BEFORE UPDATE ON forecasts 
        FOR EACH ROW 
        EXECUTE FUNCTION update_updated_at_column()
    """)


def downgrade():
    # Revert to TIMESTAMP without timezone
    op.execute("""
        ALTER TABLE forecasts 
        ALTER COLUMN created_at TYPE TIMESTAMP 
        USING created_at AT TIME ZONE 'UTC'
    """)
    
    op.execute("""
        ALTER TABLE forecasts 
        ALTER COLUMN updated_at TYPE TIMESTAMP 
        USING updated_at AT TIME ZONE 'UTC'
    """)
    
    # Drop the trigger
    op.execute("DROP TRIGGER IF EXISTS update_forecasts_updated_at ON forecasts")