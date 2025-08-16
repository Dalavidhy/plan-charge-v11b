# Complete SSO Fix Guide

## Problem Summary
Your SSO authentication is failing with **500 Internal Server Error** because:
- Backend code expects `"Default Organization"` in the database
- Database only contains `"NDA Partners"` organization  
- When users try to login, user creation fails due to missing organization

## Quick Fix Solution

**You need to add "Default Organization" to the database with this SQL:**

```sql
INSERT INTO organizations (id, name, created_at, updated_at) 
VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW()) 
ON CONFLICT (id) DO NOTHING;
```

## Available Solutions (Choose One)

### 🚀 Option 1: AWS Lambda (Recommended)
**Files Created:**
- `lambda_fix_sso.py` - Lambda function code
- `deploy_lambda_sso_fix.sh` - Full deployment script
- `simple_lambda_fix.sh` - Simplified version

**How to Use:**
1. Fix the VPC configuration in `deploy_lambda_sso_fix.sh`
2. Run: `./deploy_lambda_sso_fix.sh`
3. Lambda executes the fix and cleans up automatically

### 🔧 Option 2: EC2 Bastion Host
**Create temporary EC2 instance:**

```bash
# 1. Launch EC2 instance in same VPC as RDS
aws ec2 run-instances \
  --image-id ami-0c02fb55956c7d316 \
  --instance-type t2.micro \
  --key-name your-key \
  --subnet-id subnet-xxx \
  --security-group-ids sg-xxx

# 2. SSH to instance and install PostgreSQL client
ssh -i your-key.pem ec2-user@instance-ip
sudo yum install postgresql-client -y

# 3. Connect to database and execute fix
psql -h your-rds-endpoint -U plancharge -d plancharge \
  -c "INSERT INTO organizations (id, name, created_at, updated_at) VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;"

# 4. Terminate EC2 instance
aws ec2 terminate-instances --instance-ids i-xxx
```

### 🔍 Option 3: Find and Use Existing Resources

**A. Check for existing bastion/jump host:**
```bash
aws ec2 describe-instances --region eu-west-1 \
  --filters "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],PublicIpAddress]' \
  --output table
```

**B. Use ECS Exec (if enabled):**
```bash
# Find running tasks
aws ecs list-tasks --cluster plan-charge-cluster --region eu-west-1

# Execute in container
aws ecs execute-command \
  --cluster plan-charge-cluster \
  --task task-id \
  --container backend \
  --interactive \
  --command "psql $DATABASE_URL -c \"INSERT INTO organizations VALUES ('00000000-0000-0000-0000-000000000002','Default Organization',NOW(),NOW(),NULL) ON CONFLICT (id) DO NOTHING;\""
```

### 🗄️ Option 4: Database Direct Access

**If RDS is publicly accessible:**
```bash
# Find RDS endpoint
aws rds describe-db-instances --region eu-west-1

# Connect directly
psql -h your-actual-rds-endpoint -U plancharge -d plancharge \
  -c "INSERT INTO organizations (id, name, created_at, updated_at) VALUES ('00000000-0000-0000-0000-000000000002', 'Default Organization', NOW(), NOW()) ON CONFLICT (id) DO NOTHING;"
```

### 📊 Option 5: Use AWS Systems Manager

**If you have Session Manager access:**
```bash
# Connect to any instance with database access
aws ssm start-session --target i-instanceid --region eu-west-1

# Then execute the SQL from inside the instance
```

## How to Test Success

After executing the fix, test immediately:

```bash
python3 /tmp/sso_workaround_complete.py
```

**Expected result:**
- Status should change from `NEEDS_WORKAROUND` to `WORKING`
- SSO login should work without 500 errors

## Testing SSO Login

1. Go to: https://plan-de-charge.aws.nda-partners.com
2. Click login
3. Use your @nda-partners.com email
4. Should successfully authenticate and create user account

## Long-term Fix (Optional)

The backend code has been updated to use "NDA Partners" instead of "Default Organization":
- Files fixed: `backend/app/services/azure_sso.py`, `backend/app/api/v1/auth.py`
- Deployment script: `deploy-sso-fix.sh`
- Requires ECR/ECS deployment permissions

## Files Created in This Session

### 🔧 Fix Scripts
- `lambda_fix_sso.py` - Lambda function to add organization
- `deploy_lambda_sso_fix.sh` - Full Lambda deployment
- `simple_lambda_fix.sh` - Simplified Lambda deployment  
- `add-default-organization.sql` - SQL file for manual execution
- `/tmp/quick_fix.sql` - Single line SQL fix
- `/tmp/direct_sql_fix.py` - Direct database connection attempt

### 🧪 Test Scripts
- `/tmp/sso_workaround_complete.py` - Complete test and diagnosis
- `test-sso-fix.py` - Verify organization fix deployment

### 📋 Documentation
- `SSO_SETUP_INSTRUCTIONS.md` - Complete SSO setup guide
- `SSO_FIX_COMPLETE_GUIDE.md` - This comprehensive guide

## Support

If you need help:
1. **First try**: AWS Lambda option (easiest)
2. **Alternative**: Create temporary EC2 bastion host
3. **Check**: If you have existing bastion/jump hosts
4. **Contact**: Database administrator if available

## Expected Timeline

- **Lambda approach**: 2-3 minutes
- **EC2 bastion**: 5-10 minutes  
- **Existing resource**: 1 minute
- **Direct connection**: 30 seconds (if accessible)

**The fix takes effect immediately - no restart needed!** 🚀