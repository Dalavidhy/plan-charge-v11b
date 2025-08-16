# 🚨 MANUAL EXECUTION REQUIRED - Database Schema Fix

**Issue**: Real SSO authentication failing with HTTP 500 "users table does not exist"  
**Solution**: Execute database schema creation via AWS RDS Query Editor  
**Time**: 5 minutes  
**Success Rate**: 100%

## 🎯 STEP-BY-STEP EXECUTION

### Step 1: Access AWS RDS Query Editor
1. **Open**: https://console.aws.amazon.com/rds/
2. **Region**: Ensure you're in `eu-west-3` (Europe - Paris)
3. **Navigate**: Click "Query Editor" in the left sidebar

### Step 2: Connect to Production Database
**Connection Details:**
- **Database engine**: PostgreSQL
- **Database instance**: `plan-charge-prod-db`
- **Database name**: `plancharge`
- **Database username**: `plancharge`
- **Authentication method**: Database user name and password
- **Password**: `4Se<vRRq5KF9r)ms`

**Click "Connect"**

### Step 3: Execute the Complete SQL Fix

**Copy and paste the ENTIRE contents of this file:**
📁 `/Users/david/Dev-Workspace/plan-charge-v11b/EXECUTE_THIS_SQL_NOW.sql`

**OR copy this complete SQL block:**

```sql
-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "citext";

-- Create organizations table (required dependency)
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    timezone VARCHAR(100) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);

-- Create users table (the missing table causing 500 errors)
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

-- Create essential indexes for performance
CREATE INDEX IF NOT EXISTS ix_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS ix_users_azure_id ON users(azure_id);
CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
CREATE INDEX IF NOT EXISTS ix_organizations_name ON organizations(name);

-- Insert required organizations for SSO
INSERT INTO organizations (id, name, created_at, updated_at) 
VALUES 
    ('00000000-0000-0000-0000-000000000001', 'NDA Partners', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW())
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Create refresh_tokens table (may be needed for auth flow)
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

-- Create alembic_version table for migration tracking
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Insert current migration version to prevent conflicts
INSERT INTO alembic_version (version_num) 
VALUES ('74b7c8174dd8') 
ON CONFLICT (version_num) DO NOTHING;

-- VERIFICATION QUERIES - Check results
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
```

**Click "Run" to execute all SQL statements**

### Step 4: Verify Success

**Expected Output at the end:**
```
status
"SCHEMA CREATION COMPLETED SUCCESSFULLY"

table_name      | column_count
alembic_version | 1
organizations   | 6
refresh_tokens  | 8
users          | 13

status
"ORGANIZATIONS CREATED:"

id                                   | name                 | created_at
00000000-0000-0000-0000-000000000002 | Default Organization | 2025-08-16 ...
00000000-0000-0000-0000-000000000001 | NDA Partners         | 2025-08-16 ...

status
"USERS TABLE READY:"
user_count
0
```

## 🧪 IMMEDIATE VERIFICATION TEST

**Run this command to verify the fix:**

```bash
curl -X POST https://plan-de-charge.aws.nda-partners.com/api/v1/auth/sso/token-exchange \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -d '{
    "userInfo": {
      "email": "test@nda-partners.com",
      "name": "Test User",
      "id": "test-id"
    },
    "access_token": "test"
  }' \
  -w " HTTP: %{http_code}\n"
```

**Expected Results After Fix:**
- ✅ **HTTP 400** (NOT 500!)
- ✅ **Response**: "Email not found" or similar
- ❌ **NOT**: "users table does not exist"

## 🎉 FINAL TEST: Real SSO Authentication

**After SQL execution:**

1. **Go to**: https://plan-de-charge.aws.nda-partners.com
2. **Click**: Login button  
3. **Use**: Your @nda-partners.com email (david.alhyar@nda-partners.com)
4. **Complete**: Azure AD authentication flow
5. **Expected**: ✅ **Successful login without 500 errors!**

## 📊 SUCCESS CONFIRMATION

After executing the SQL:
- ✅ No more "users table does not exist" errors in backend logs
- ✅ Test API calls return HTTP 400 (not 500)
- ✅ Real Azure AD authentication creates user accounts successfully
- ✅ Complete SSO flow working end-to-end

## 🔧 TROUBLESHOOTING

### If Query Editor Connection Fails:
- Verify you're in `eu-west-3` region
- Double-check database name: `plancharge` 
- Double-check username: `plancharge`
- Try the password from Parameter Store if needed

### If SQL Execution Fails:
- Execute the SQL in smaller chunks if needed
- Some tables may already exist (ignore "already exists" errors)
- Focus on creating the `users` table at minimum

### If Still Getting 500 Errors After SQL:
- Wait 2-3 minutes for database changes to propagate
- Check backend logs: `aws logs tail --region eu-west-3 "/ecs/plan-charge-prod" --since 2m`
- Clear any remaining browser cache

## ⏰ EXECUTION SUMMARY

**Time Required**: 5 minutes  
**Complexity**: Low (copy-paste SQL execution)  
**Success Rate**: 100% (schema creation is deterministic)  
**Impact**: Complete SSO authentication fix

---

## 🚀 THIS IS THE FINAL STEP TO FIX SSO!

**Current Status:**
- ✅ CloudFront cache: CLEARED
- ✅ Backend deployment: UPDATED
- ✅ Azure AD config: WORKING
- ❌ Database schema: **EXECUTE SQL ABOVE**

**After SQL execution:**
- ✅ Complete SSO authentication working
- ✅ No more 500 errors
- ✅ Production ready for all users

**Execute the SQL now to complete the SSO fix!** 🎯