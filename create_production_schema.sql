-- Complete Production Database Schema for Plan de Charge
-- Execute this via AWS RDS Query Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types first
DO $$ BEGIN
    CREATE TYPE person_source AS ENUM ('manual', 'payfit', 'gryzzly', 'import');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE email_kind AS ENUM ('corporate', 'personal', 'integration');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE engagement_type AS ENUM ('employee', 'contractor', 'mandataire', 'freelance');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE role_type AS ENUM ('owner', 'admin', 'manager', 'member', 'viewer');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create organizations table (core dependency)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create refresh_tokens table
CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL, -- Will reference users.id
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create people table
CREATE TABLE IF NOT EXISTS people (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    full_name VARCHAR(255) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    manager_id UUID NULL REFERENCES people(id),
    cost_center VARCHAR(100) NULL,
    location VARCHAR(100) NULL,
    weekly_hours_default NUMERIC(5,2) NULL,
    source person_source NOT NULL DEFAULT 'manual',
    source_updated_at TIMESTAMP WITH TIME ZONE NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create users table (depends on organizations and people)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    person_id UUID NULL REFERENCES people(id),
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

-- Add foreign key constraint for refresh_tokens.user_id now that users table exists
ALTER TABLE refresh_tokens 
DROP CONSTRAINT IF EXISTS refresh_tokens_user_id_fkey;

ALTER TABLE refresh_tokens 
ADD CONSTRAINT refresh_tokens_user_id_fkey 
FOREIGN KEY (user_id) REFERENCES users(id);

-- Create user_org_roles table
CREATE TABLE IF NOT EXISTS user_org_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    user_id UUID NOT NULL REFERENCES users(id),
    role role_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, user_id)
);

-- Create person_emails table
CREATE TABLE IF NOT EXISTS person_emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    person_id UUID NOT NULL REFERENCES people(id),
    email CITEXT NOT NULL,
    kind email_kind NOT NULL DEFAULT 'corporate',
    is_primary BOOLEAN NOT NULL DEFAULT false,
    verified BOOLEAN NOT NULL DEFAULT false,
    source VARCHAR(50) NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(person_id, email)
);

-- Create person_identifiers table
CREATE TABLE IF NOT EXISTS person_identifiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    person_id UUID NOT NULL REFERENCES people(id),
    id_type VARCHAR(50) NOT NULL,
    id_value VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(org_id, id_type, id_value)
);

-- Create engagements table
CREATE TABLE IF NOT EXISTS engagements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    person_id UUID NOT NULL REFERENCES people(id),
    type engagement_type NOT NULL DEFAULT 'employee',
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NULL,
    weekly_hours_default NUMERIC(5,2) NULL,
    payroll_eligible BOOLEAN NOT NULL DEFAULT true,
    notes VARCHAR(500) NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    external_contract_id VARCHAR(100) NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS ix_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS ix_users_person_id ON users(person_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_users_azure_id ON users(azure_id);

CREATE INDEX IF NOT EXISTS ix_people_org_id ON people(org_id);
CREATE INDEX IF NOT EXISTS ix_people_manager_id ON people(manager_id);
CREATE INDEX IF NOT EXISTS ix_people_org_active ON people(org_id, active);
CREATE INDEX IF NOT EXISTS ix_people_full_name ON people(full_name);

CREATE INDEX IF NOT EXISTS ix_person_emails_person_id ON person_emails(person_id);
CREATE INDEX IF NOT EXISTS ix_person_emails_email ON person_emails(email);

CREATE INDEX IF NOT EXISTS ix_person_identifiers_person_id ON person_identifiers(person_id);
CREATE INDEX IF NOT EXISTS ix_person_identifiers_org_id ON person_identifiers(org_id);

CREATE INDEX IF NOT EXISTS ix_engagements_person_id ON engagements(person_id);
CREATE INDEX IF NOT EXISTS ix_engagements_org_id ON engagements(org_id);
CREATE INDEX IF NOT EXISTS ix_engagements_person_dates ON engagements(person_id, start_date, end_date);

CREATE INDEX IF NOT EXISTS ix_user_org_roles_org_id ON user_org_roles(org_id);
CREATE INDEX IF NOT EXISTS ix_user_org_roles_user_id ON user_org_roles(user_id);

CREATE INDEX IF NOT EXISTS ix_refresh_tokens_org_id ON refresh_tokens(org_id);
CREATE INDEX IF NOT EXISTS ix_refresh_tokens_user_id ON refresh_tokens(user_id);

-- Insert required organizations
INSERT INTO organizations (id, name, created_at, updated_at) 
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'NDA Partners', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Verify schema creation
SELECT 'Schema creation completed successfully' as status;

-- Show created tables
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Show organizations
SELECT id, name, created_at 
FROM organizations 
ORDER BY name;