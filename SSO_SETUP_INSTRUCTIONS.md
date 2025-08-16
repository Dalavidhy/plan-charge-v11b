# Plan Charge SSO Setup - Final Steps

## Current Status ✅

**Azure AD Authentication**: ✅ **WORKING**
- Azure AD app correctly configured for SPA/PKCE flow
- Frontend successfully acquires MSAL tokens
- Redirect URIs properly configured
- `isFallbackPublicClient=true` enabled

**Backend Service**: ✅ **RUNNING**
- Service deployed and accessible
- Configuration fixed (Alembic migration issues resolved)
- Token exchange endpoint responding

**Issue**: ❌ **Database tables missing**
- Error: `relation 'users' does not exist`
- Backend can't complete SSO authentication without user tables

## What's Working
1. ✅ User visits https://plan-de-charge.aws.nda-partners.com
2. ✅ Azure AD authentication popup appears
3. ✅ User authenticates with @nda-partners.com account
4. ✅ MSAL acquires tokens successfully
5. ✅ Frontend sends tokens to backend `/auth/azure/token-exchange`
6. ❌ Backend fails: "relation 'users' does not exist"

## Solution: Create Database Tables

We need to create the `organizations` and `users` tables in the production database.

### Option 1: AWS RDS Query Editor (Recommended)

1. **Go to AWS Console → RDS → Query Editor**
2. **Select your PostgreSQL database instance**
3. **Authenticate with database credentials**
4. **Execute the SQL script**: `create_tables_manually.sql`

```sql
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create organizations table
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
```

### Option 2: ECS Task Override (if possible)

If you can run ECS tasks, try this command:

```bash
aws ecs run-task \
  --cluster plan-charge-cluster \
  --task-definition plan-charge-backend \
  --overrides '{
    "containerOverrides": [{
      "name": "backend",
      "command": ["python3", "/app/create_sso_tables.py"]
    }]
  }' \
  --region eu-west-1
```

## Expected Results After Table Creation

Once the tables are created, the authentication flow will work as follows:

1. ✅ User authenticates with Azure AD
2. ✅ Frontend receives tokens and sends to backend
3. ✅ Backend validates Azure AD token
4. ✅ Backend looks up user by `azure_id` (Object ID)
5. ✅ If user doesn't exist, backend creates new user record
6. ✅ Backend issues JWT token for the application
7. ✅ User is logged in and redirected to dashboard

## Verification Steps

After creating the tables:

1. **Test SSO Login**:
   - Visit: https://plan-de-charge.aws.nda-partners.com
   - Click login
   - Authenticate with Azure AD
   - Should be redirected to dashboard

2. **Check Backend Logs**:
   ```bash
   aws logs get-log-events \
     --log-group-name /ecs/plan-charge-backend \
     --log-stream-name [latest-stream] \
     --region eu-west-1
   ```

3. **Verify User Creation**:
   ```sql
   SELECT id, email, full_name, azure_id, created_at 
   FROM users 
   ORDER BY created_at DESC 
   LIMIT 5;
   ```

## Files Created

- `create_tables_manually.sql` - Complete SQL script for manual execution
- `create_sso_tables.py` - Python script for container execution
- `SSO_SETUP_INSTRUCTIONS.md` - This instruction file

## Support

If you encounter issues:

1. **Check Azure AD token validity**: MSAL should show token acquisition success
2. **Verify database connectivity**: Backend logs should show database connection
3. **Check table existence**: Query `information_schema.tables` to verify tables exist
4. **Monitor backend logs**: Look for SSO authentication attempts and errors

## Summary

🎯 **Final Step Required**: Create database tables using one of the methods above.

Once completed, the SSO authentication will be fully functional and users with @nda-partners.com email addresses will be able to login to the Plan Charge application.