# 🗄️ Execute Database Fix - Organizations

**Status**: ⚡ CloudFront cache CLEARED - Ready for database fix

## 🎯 **EXECUTE THIS SQL NOW**

**Using AWS RDS Query Editor:**

1. **Go to**: AWS Console → RDS → Query Editor
2. **Connect to**: `plan-charge-prod-db` (eu-west-3)
3. **Database**: `plancharge`
4. **Username**: `plancharge` 
5. **Password**: From Parameter Store `/plan-charge/prod/db-password`

**Execute this exact SQL:**

```sql
-- Add NDA Partners organization (primary)
INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) 
VALUES ('00000000-0000-0000-0000-000000000001', 'NDA Partners', NOW(), NOW(), NULL)
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Add Default Organization (fallback)
INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) 
VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW(), NULL)
ON CONFLICT (id) DO UPDATE SET 
    name = EXCLUDED.name,
    updated_at = NOW();

-- Verify both exist
SELECT 'Organizations after fix:' as status;
SELECT id, name, created_at FROM organizations ORDER BY name;
```

## ✅ **Expected Result:**

```
Organizations after fix:
status
"Organizations after fix:"

id                                   | name                 | created_at
00000000-0000-0000-0000-000000000002 | Default Organization | 2025-08-16 20:01:xx
00000000-0000-0000-0000-000000000001 | NDA Partners         | 2025-08-16 20:01:xx
```

## 🧪 **Test Immediately After:**

```bash
# Should now return 400 (not 500) with fresh cache
curl -X POST https://plan-de-charge.aws.nda-partners.com/api/v1/auth/sso/token-exchange \
  -H "Content-Type: application/json" \
  -H "Cache-Control: no-cache" \
  -d '{"access_token": "test"}' \
  -w " HTTP: %{http_code}\n"
```

**Expected**: HTTP 400 "Email not found in user info"

## 🎉 **Then Test Real Authentication:**
1. Go to: https://plan-de-charge.aws.nda-partners.com
2. Click login
3. Use your @nda-partners.com email
4. **Should work without 500 errors!**

---

**⚡ CloudFront cache is CLEARED - Execute the SQL NOW!**