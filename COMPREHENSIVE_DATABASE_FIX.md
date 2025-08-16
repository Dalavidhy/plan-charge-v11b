# 🗄️ Comprehensive Database Fix Guide

## 🎯 **TWO ISSUES IDENTIFIED:**

### ✅ **Issue 1: CloudFront Cache - RESOLVED**
- **Problem**: CloudFront was caching 500 error responses
- **Solution**: Cache invalidation completed ✅
- **Result**: Test tokens now return 400 (correct) instead of 500

### ❌ **Issue 2: Database Schema - NEEDS FIX**
- **Problem**: `relation "users" does not exist`
- **Cause**: Database migrations may not have been applied
- **Impact**: Real authentication fails with 500 error

## 🧪 **Current Test Results:**
- ✅ Basic test tokens: HTTP 400 (correct)
- ✅ Cache busting: HTTP 400 (correct)  
- ❌ Real user structure: HTTP 500 "users table does not exist"

## 🔧 **REQUIRED FIXES:**

### **Fix 1: Run Database Migrations**

**Check if migrations need to be run:**
```bash
# Connect to backend container and check migrations
aws ecs execute-command \
  --region eu-west-3 \
  --cluster plan-charge-prod-cluster \
  --task [BACKEND_TASK_ID] \
  --container backend \
  --interactive \
  --command "/bin/bash -c 'cd /app && alembic current'"
```

**Run migrations if needed:**
```bash
# In backend container
cd /app && alembic upgrade head
```

### **Fix 2: Add Organizations (Still Needed)**

**Use AWS RDS Query Editor:**
```sql
-- First check if tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- If organizations table exists, add organizations:
INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) 
VALUES ('00000000-0000-0000-0000-000000000001', 'NDA Partners', NOW(), NOW(), NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW();

INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) 
VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW(), NULL)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW();
```

### **Fix 3: Check Database Connection String**

The error might also indicate connection to wrong database. Check:
```bash
# In backend container, verify DATABASE_URL
echo $DATABASE_URL

# Should point to: plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com
```

## 🎯 **RECOMMENDED APPROACH:**

### **Option A: Via ECS Exec (If Session Manager Working)**
```bash
# Get current task ID
aws ecs list-tasks --region eu-west-3 --cluster plan-charge-prod-cluster --service-name plan-charge-prod-backend

# Execute migrations
PATH="$HOME/bin:$PATH" aws ecs execute-command \
  --region eu-west-3 \
  --cluster plan-charge-prod-cluster \
  --task [TASK_ID] \
  --container backend \
  --interactive \
  --command "/bin/bash -c 'cd /app && alembic upgrade head'"
```

### **Option B: Deployment with Migration Hook**
```bash
# Force new deployment that runs migrations
aws ecs update-service \
  --region eu-west-3 \
  --cluster plan-charge-prod-cluster \
  --service plan-charge-prod-backend \
  --force-new-deployment
```

### **Option C: Manual Database Schema Creation**
Use the Alembic migration files to manually create the schema via RDS Query Editor.

## 🧪 **Testing Plan:**

### **After Database Fix:**
```bash
# Test the structured payload that was failing
curl -X POST https://plan-de-charge.aws.nda-partners.com/api/v1/auth/sso/token-exchange \
  -H "Content-Type: application/json" \
  -d '{
    "userInfo": {
      "email": "test@nda-partners.com",
      "name": "Test User", 
      "id": "test-id"
    },
    "access_token": "test"
  }' \
  -w " HTTP: %{http_code}\n"

# Expected: HTTP 400 (not 500)
```

### **Real Authentication Test:**
1. Go to: https://plan-de-charge.aws.nda-partners.com
2. Click login with @nda-partners.com email
3. Should complete without database errors

## 📊 **Success Criteria:**
- ✅ All test formats return 4xx (not 5xx)
- ✅ Database tables exist and are accessible
- ✅ Organizations are present in database
- ✅ Real authentication works end-to-end

## ⚡ **NEXT IMMEDIATE ACTION:**
1. **Check database schema** via RDS Query Editor
2. **Run migrations** if tables are missing
3. **Add organizations** once schema is ready
4. **Test** real authentication

---

**🎯 CloudFront cache is fixed - now fixing database schema!**