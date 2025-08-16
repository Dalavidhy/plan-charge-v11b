-- MINIMAL DATABASE SCHEMA FIX
-- Execute this if the full schema is too complex

-- Enable UUID extension (safe to run multiple times)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create organizations table (core dependency)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create users table (the missing one causing the 500 error)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id),
    person_id UUID NULL, -- Can be null initially
    email VARCHAR(255) NOT NULL,
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

-- Create basic indexes
CREATE INDEX IF NOT EXISTS ix_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS ix_users_azure_id ON users(azure_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);

-- Insert required organizations
INSERT INTO organizations (id, name, created_at, updated_at) 
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'NDA Partners', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Verify the fix
SELECT 'MINIMAL SCHEMA FIX COMPLETED' as status;
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('organizations', 'users');
SELECT id, name FROM organizations ORDER BY name;