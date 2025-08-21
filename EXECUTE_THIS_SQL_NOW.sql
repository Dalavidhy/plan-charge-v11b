-- ================================================================
-- FINAL DATABASE SCHEMA FIX - Execute via AWS RDS Query Editor
-- ================================================================
-- This resolves the "relation 'users' does not exist" error
-- causing SSO authentication HTTP 500 failures

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- ================================================================
-- Create organizations table (required dependency)
-- ================================================================
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- ================================================================
-- Create users table (the missing table causing 500 errors)
-- ================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    person_id UUID NULL,
    email CITEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NULL,
    azure_id VARCHAR(255) NULL UNIQUE,
    locale VARCHAR(10) NOT NULL DEFAULT 'fr',
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_login_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL,
    UNIQUE(org_id, email)
);

-- ================================================================
-- Create essential indexes for performance
-- ================================================================
CREATE INDEX IF NOT EXISTS ix_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS ix_users_azure_id ON users(azure_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations(name);

-- ================================================================
-- Insert required organizations for SSO
-- ================================================================
INSERT INTO organizations (id, name, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'NDA Partners', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = NOW();

-- ================================================================
-- Create refresh_tokens table (may be needed for auth flow)
-- ================================================================
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Index for refresh tokens
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_token_hash ON refresh_tokens(token_hash);

-- ================================================================
-- Create alembic_version table for migration tracking
-- ================================================================
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Insert current migration version to prevent conflicts
INSERT INTO alembic_version (version_num)
VALUES ('74b7c8174dd8')
ON CONFLICT (version_num) DO NOTHING;

-- ================================================================
-- VERIFICATION QUERIES - Check results
-- ================================================================

-- Confirm schema creation was successful
SELECT 'SCHEMA CREATION COMPLETED SUCCESSFULLY' as status;

-- Show all created tables
SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns
        WHERE table_name = t.table_name AND table_schema = 'public') as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
AND table_name IN ('organizations', 'users', 'refresh_tokens', 'alembic_version')
ORDER BY table_name;

-- Show organizations (should have 2 rows)
SELECT 'ORGANIZATIONS CREATED:' as status;
SELECT id, name, created_at FROM organizations ORDER BY name;

-- Show users table structure (should be empty initially)
SELECT 'USERS TABLE READY:' as status;
SELECT COUNT(*) as user_count FROM users;

-- Show indexes created
SELECT 'INDEXES CREATED:' as status;
SELECT indexname
FROM pg_indexes
WHERE tablename IN ('users', 'organizations', 'refresh_tokens')
ORDER BY tablename, indexname;

-- ================================================================
-- EXPECTED RESULTS:
-- ================================================================
-- status: "SCHEMA CREATION COMPLETED SUCCESSFULLY"
--
-- table_name      | column_count
-- alembic_version | 1
-- organizations   | 6
-- refresh_tokens  | 8
-- users          | 13
--
-- status: "ORGANIZATIONS CREATED:"
-- id                                   | name                 | created_at
-- 00000000-0000-0000-0000-000000000002 | Default Organization | 2025-08-16 ...
-- 00000000-0000-0000-0000-000000000001 | NDA Partners         | 2025-08-16 ...
--
-- status: "USERS TABLE READY:"
-- user_count: 0
--
-- ================================================================
-- POST-EXECUTION TEST:
-- ================================================================
-- After running this SQL, test immediately:
--
-- curl -X POST https://plan-de-charge.aws.nda-partners.com/api/v1/auth/sso/token-exchange \
--   -H "Content-Type: application/json" \
--   -H "Cache-Control: no-cache" \
--   -d '{"userInfo": {"email": "test@nda-partners.com", "name": "Test User", "id": "test-id"}, "access_token": "test"}'
--
-- Expected: HTTP 400 (not 500!) with "Email not found" message
-- ================================================================
