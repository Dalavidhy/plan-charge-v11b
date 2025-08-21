-- ============================================================================
-- Plan Charge Database Setup - SSO Authentication Tables
-- ============================================================================
-- Execute this SQL in AWS RDS Query Editor or any PostgreSQL client
-- to create the required tables for SSO authentication.

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create organizations table if it doesn't exist
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create users table with azure_id for SSO
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id),
    person_id UUID,
    email CITEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255),
    azure_id VARCHAR(255), -- Azure AD Object ID for SSO
    locale VARCHAR(10) DEFAULT 'fr',
    is_active BOOLEAN DEFAULT TRUE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_azure_id ON users(azure_id);
CREATE INDEX IF NOT EXISTS ix_users_org_id ON users(org_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_users_org_email ON users(org_id, email) WHERE deleted_at IS NULL;

-- Insert default organization
INSERT INTO organizations (id, name)
VALUES ('00000000-0000-0000-0000-000000000001', 'NDA Partners')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;

-- Create alembic_version table to track migrations
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Insert current migration version
INSERT INTO alembic_version (version_num)
VALUES ('74b7c8174dd8')
ON CONFLICT (version_num) DO NOTHING;

-- Verify tables were created
SELECT
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('organizations', 'users')
ORDER BY table_name, ordinal_position;

-- Show organizations count
SELECT 'organizations' as table_name, COUNT(*) as row_count FROM organizations
UNION ALL
SELECT 'users' as table_name, COUNT(*) as row_count FROM users;

-- ============================================================================
-- INSTRUCTIONS FOR EXECUTION:
-- ============================================================================
--
-- Option 1: AWS RDS Query Editor
-- 1. Go to AWS Console -> RDS -> Query Editor
-- 2. Select your PostgreSQL database
-- 3. Authenticate with database credentials
-- 4. Copy and paste this entire SQL script
-- 5. Execute the script
--
-- Option 2: Using PostgreSQL client (if you have database access)
-- 1. Connect to the database using psql or any PostgreSQL client
-- 2. Execute this script
--
-- Option 3: ECS Task Override (if working)
-- 1. Use ECS task override to run migration
-- 2. Command: alembic upgrade head
--
-- ============================================================================
-- EXPECTED RESULTS:
-- ============================================================================
-- - organizations table created with 1 row (NDA Partners)
-- - users table created with 0 rows (will be populated on first login)
-- - alembic_version table created with migration tracking
-- - All required indexes created for performance
-- - SSO authentication ready to work
-- ============================================================================
