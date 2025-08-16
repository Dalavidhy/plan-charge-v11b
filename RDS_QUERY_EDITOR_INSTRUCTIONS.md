# 🗄️ Execute Database Schema Fix via AWS RDS Query Editor

## ⚡ CRITICAL: The `users` table doesn't exist in production!

**Error confirmed**: `relation "users" does not exist`

## 🎯 IMMEDIATE ACTION REQUIRED

### Step 1: Access AWS RDS Query Editor

1. **Open AWS Console**: https://console.aws.amazon.com/
2. **Navigate to**: Services → RDS → Query Editor
3. **Region**: Ensure you're in `eu-west-3` (Europe - Paris)

### Step 2: Connect to Production Database

**Connection Details:**
- **Engine type**: PostgreSQL
- **Database instance**: `plan-charge-prod-db`
- **Database name**: `plancharge`
- **Database username**: `plancharge`
- **Authentication**: Choose "Database user name and password"

**Password**: Get from AWS Systems Manager Parameter Store:
- **Parameter name**: `/plan-charge/prod/db-password` 
- **Or try**: Check the .env file for the password: `4Se%3CvRRq5KF9r)ms`

### Step 3: Execute Schema Creation

**Copy and paste the ENTIRE SQL from this file:**
📁 `/Users/david/Dev-Workspace/plan-charge-v11b/create_production_schema.sql`

**Click "Run"** to execute all SQL statements.

### Step 4: Verify Success

**Expected output at the end:**
```
Schema creation completed successfully

table_name
-----------
engagements
organizations  
people
person_emails
person_identifiers
refresh_tokens
user_org_roles
users

id                                   | name                 | created_at
00000000-0000-0000-0000-000000000002 | Default Organization | 2025-08-16 ...
00000000-0000-0000-0000-000000000001 | NDA Partners         | 2025-08-16 ...
```

## 🧪 Test Immediately After Schema Fix

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

**Expected Result:** 
- ✅ HTTP 400 (not 500!)
- ✅ Message: "Email not found" or similar (not "users table does not exist")

## 🎉 Final Test: Real Authentication

After schema is created:

1. **Go to**: https://plan-de-charge.aws.nda-partners.com
2. **Click**: Login button
3. **Use**: Your @nda-partners.com email
4. **Expected**: Successful login without 500 errors!

## 📋 Troubleshooting

### If Query Editor Connection Fails:
- Verify you're in `eu-west-3` region
- Check VPC security groups allow connection
- Try the password from Parameter Store: `/plan-charge/prod/db-password`

### If SQL Execution Fails:
- Run the SQL in smaller chunks (create tables first, then indexes)
- Check if some tables already exist (ignore conflicts)

### If Still Getting 500 Errors After Schema:
- Wait 2-3 minutes for database changes to propagate
- Clear any remaining CloudFront cache
- Check backend logs for new error messages

## ⚡ THIS IS THE FINAL FIX!

**Current Status:**
- ✅ CloudFront cache: CLEARED  
- ✅ Backend deployment: UPDATED
- ✅ Azure AD config: WORKING
- ❌ Database schema: **NEEDS EXECUTION**

**After executing the schema SQL:**
- ✅ Database schema: COMPLETE
- ✅ SSO authentication: FULLY WORKING

---

**🚀 Execute the schema SQL NOW to complete the SSO fix!**