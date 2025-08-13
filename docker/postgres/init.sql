-- Initial PostgreSQL setup for Plan Charge v9

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable case-insensitive text extension
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create custom types
CREATE TYPE role_type AS ENUM ('owner', 'admin', 'manager', 'member', 'viewer');
CREATE TYPE project_status AS ENUM ('proposed', 'active', 'paused', 'done', 'cancelled');
CREATE TYPE task_status AS ENUM ('todo', 'in_progress', 'blocked', 'done', 'cancelled');
CREATE TYPE absence_type AS ENUM ('vacation', 'sick', 'other');
CREATE TYPE engagement_type AS ENUM ('employee', 'contractor', 'mandataire', 'freelance');
CREATE TYPE allocation_source AS ENUM ('manual', 'import', 'rule');
CREATE TYPE sync_state AS ENUM ('queued', 'running', 'success', 'error');
CREATE TYPE connection_status AS ENUM ('connected', 'error', 'revoked');

-- Set default timezone
SET timezone = 'UTC';

-- Note: Indexes will be created by Alembic migrations after tables are created

-- Add comments for documentation
COMMENT ON DATABASE plancharge IS 'Plan Charge v9 - Multi-team resource planning and capacity management system';
COMMENT ON EXTENSION "uuid-ossp" IS 'Provides UUID generation functions';
COMMENT ON EXTENSION "citext" IS 'Case-insensitive text type for email addresses';

-- Performance tuning for PostgreSQL
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;