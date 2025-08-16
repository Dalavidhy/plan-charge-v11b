#!/usr/bin/env python3
"""
Simple Lambda fix for SSO - EU-West-3 with correct endpoint
This creates a minimal Lambda to execute the SQL fix
"""

import json
import boto3
import zipfile
import os
import time

def create_lambda_fix():
    """Create and execute Lambda function to fix SSO."""
    
    print("🚀 Simple Lambda SSO Fix - EU-West-3")
    print("=" * 40)
    
    # Configuration
    region = 'eu-west-3'
    function_name = f'sso-fix-{int(time.time())}'
    role_name = f'lambda-sso-role-{int(time.time())}'
    
    lambda_client = boto3.client('lambda', region_name=region)
    iam_client = boto3.client('iam')
    
    try:
        # Step 1: Create IAM role
        print("🔐 Creating IAM role...")
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        role_response = iam_client.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description='Temporary role for SSO fix'
        )
        
        role_arn = role_response['Role']['Arn']
        
        # Attach basic execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
        )
        
        print("✅ IAM role created")
        
        # Step 2: Create Lambda function code
        print("📦 Creating Lambda package...")
        
        lambda_code = '''
import json
import psycopg2

def lambda_handler(event, context):
    try:
        print("🔧 Starting SSO fix...")
        
        # Connect to database
        conn = psycopg2.connect(
            host="plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com",
            port=5432,
            database="plancharge",
            user="plancharge",
            password="4Se%3CvRRq5KF9r)ms",
            connect_timeout=10
        )
        
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("✅ Connected to database")
        
        # Check current organizations
        cursor.execute("SELECT id, name FROM organizations ORDER BY name;")
        existing_orgs = cursor.fetchall()
        print(f"Current orgs: {existing_orgs}")
        
        # Check if Default Organization exists
        default_exists = any('Default Organization' in str(org) for org in existing_orgs)
        
        if default_exists:
            result = {"success": True, "message": "Default Organization already exists", "action": "none"}
        else:
            # Add Default Organization
            cursor.execute("""
                INSERT INTO organizations (id, name, created_at, updated_at, deleted_at) 
                VALUES (%s, %s, NOW(), NOW(), NULL)
                ON CONFLICT (id) DO UPDATE SET 
                    name = EXCLUDED.name, updated_at = NOW();
            """, ('00000000-0000-0000-0000-000000000002', 'Default Organization'))
            
            print("✅ Default Organization added")
            result = {"success": True, "message": "Default Organization added successfully", "action": "added"}
        
        cursor.close()
        conn.close()
        
        return {"statusCode": 200, "body": json.dumps(result)}
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"statusCode": 500, "body": json.dumps({"success": False, "error": str(e)})}
'''
        
        # Create zip file
        zip_buffer = '/tmp/lambda_sso_fix.zip'
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.writestr('lambda_function.py', lambda_code)
        
        print("✅ Lambda package created")
        
        # Wait for role to be ready
        print("⏳ Waiting for role propagation...")
        time.sleep(10)
        
        # Step 3: Create Lambda function (without VPC for simplicity)
        print("🚀 Creating Lambda function...")
        
        with open(zip_buffer, 'rb') as zip_file:
            lambda_response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_file.read()},
                Timeout=30,
                MemorySize=128,
                Description='Temporary function to fix SSO by adding Default Organization'
            )
        
        print("✅ Lambda function created")
        
        # Wait for function to be ready
        print("⏳ Waiting for Lambda to be ready...")
        time.sleep(5)
        
        # Step 4: Execute the fix
        print("🔧 Executing SSO fix...")
        
        response = lambda_client.invoke(
            FunctionName=function_name,
            LogType='Tail'
        )
        
        # Parse response
        payload = json.loads(response['Payload'].read())
        
        print("📄 Lambda response:")
        print(json.dumps(payload, indent=2))
        
        if payload.get('statusCode') == 200:
            body = json.loads(payload['body'])
            if body.get('success'):
                print("🎉 SSO FIX SUCCESSFUL!")
                print("✅ Default Organization added to database")
                print("🚀 Test at: https://plan-de-charge.aws.nda-partners.com")
                return True
            else:
                print(f"❌ Fix failed: {body.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Lambda execution failed: {payload}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating Lambda: {e}")
        return False
        
    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        try:
            lambda_client.delete_function(FunctionName=function_name)
            iam_client.detach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            iam_client.delete_role(RoleName=role_name)
            os.remove(zip_buffer)
            print("✅ Cleanup completed")
        except Exception as cleanup_error:
            print(f"⚠️ Cleanup warning: {cleanup_error}")

if __name__ == "__main__":
    success = create_lambda_fix()
    if success:
        print("\n🎉 SUCCESS! SSO should now work without 500 errors!")
        print("Test login at: https://plan-de-charge.aws.nda-partners.com")
    else:
        print("\n❌ Failed to execute fix - check output above")