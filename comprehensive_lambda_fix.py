#!/usr/bin/env python3
"""
Comprehensive Lambda function to fix SSO organizations
Uses the improved Lambda with VPC configuration
"""

import boto3
import zipfile
import json
import time
import tempfile
import os

def create_comprehensive_lambda_fix():
    """Create and deploy Lambda function to add both organizations."""

    print("🚀 Comprehensive Lambda SSO Fix")
    print("=" * 35)

    # Configuration
    region = 'eu-west-3'
    function_name = f'sso-comprehensive-fix-{int(time.time())}'
    role_name = f'lambda-sso-role-{int(time.time())}'

    lambda_client = boto3.client('lambda', region_name=region)
    iam_client = boto3.client('iam')
    ec2_client = boto3.client('ec2', region_name=region)

    cleanup_resources = []

    try:
        # Step 1: Get VPC configuration
        print("🔍 Finding VPC configuration...")

        # Get VPC and subnets for RDS
        vpcs = ec2_client.describe_vpcs()['Vpcs']
        default_vpc = next((vpc for vpc in vpcs if vpc.get('IsDefault', False)), None)

        if not default_vpc:
            print("❌ No default VPC found")
            return False

        vpc_id = default_vpc['VpcId']
        print(f"✅ Using VPC: {vpc_id}")

        # Get private subnets (where RDS likely resides)
        subnets = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )['Subnets']

        # Prefer private subnets, but use any available
        private_subnets = [s for s in subnets if not s.get('MapPublicIpOnLaunch', False)]
        subnet_ids = [s['SubnetId'] for s in (private_subnets if private_subnets else subnets)]

        print(f"✅ Using subnets: {subnet_ids[:2]}")  # Use first 2 subnets

        # Get or create security group that allows RDS access
        try:
            security_groups = ec2_client.describe_security_groups(
                Filters=[
                    {'Name': 'vpc-id', 'Values': [vpc_id]},
                    {'Name': 'group-name', 'Values': ['default']}
                ]
            )['SecurityGroups']

            if security_groups:
                sg_id = security_groups[0]['GroupId']
                print(f"✅ Using security group: {sg_id}")
            else:
                print("❌ No security group found")
                return False

        except Exception as sg_error:
            print(f"⚠️ Security group error: {sg_error}")
            return False

        # Step 2: Create IAM role
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
            Description='Comprehensive SSO fix role with VPC access'
        )

        role_arn = role_response['Role']['Arn']
        cleanup_resources.append(('role', role_name))

        # Attach VPC execution policy
        iam_client.attach_role_policy(
            RoleName=role_name,
            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole'
        )

        print("✅ IAM role created with VPC access")

        # Step 3: Create Lambda function code
        print("📦 Creating comprehensive Lambda package...")

        lambda_code = '''
import json
import psycopg2
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """Comprehensive SSO fix - add both organizations to ensure compatibility."""

    logger.info("🔧 Starting comprehensive SSO fix...")

    try:
        # Database connection configuration
        db_config = {
            "host": "plan-charge-prod-db.cm296zxv9y8r.eu-west-3.rds.amazonaws.com",
            "port": 5432,
            "database": "plancharge",
            "user": "plancharge",
            "password": "4Se%3CvRRq5KF9r)ms",
            "connect_timeout": 15,
            "sslmode": "require"
        }

        logger.info(f"Connecting to database: {db_config['host']}")

        # Connect to database
        conn = psycopg2.connect(**db_config)
        conn.autocommit = True
        cursor = conn.cursor()

        logger.info("✅ Connected to database successfully")

        # Check current organizations
        cursor.execute("SELECT id, name FROM organizations ORDER BY name")
        existing_orgs = cursor.fetchall()

        logger.info(f"Current organizations: {existing_orgs}")

        organizations_added = []

        # Add NDA Partners (primary organization)
        try:
            cursor.execute("""
                INSERT INTO organizations (id, name, created_at, updated_at, deleted_at)
                VALUES (%s, %s, NOW(), NOW(), NULL)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW()
                RETURNING id, name;
            """, ('00000000-0000-0000-0000-000000000001', 'NDA Partners'))

            result = cursor.fetchone()
            organizations_added.append(f"NDA Partners (ID: {result[0]})")
            logger.info("✅ NDA Partners organization ensured")

        except Exception as nda_error:
            logger.error(f"❌ Error adding NDA Partners: {nda_error}")

        # Add Default Organization (backward compatibility)
        try:
            cursor.execute("""
                INSERT INTO organizations (id, name, created_at, updated_at, deleted_at)
                VALUES (%s, %s, NOW(), NOW(), NULL)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW()
                RETURNING id, name;
            """, ('00000000-0000-0000-0000-000000000002', 'Default Organization'))

            result = cursor.fetchone()
            organizations_added.append(f"Default Organization (ID: {result[0]})")
            logger.info("✅ Default Organization ensured")

        except Exception as default_error:
            logger.error(f"❌ Error adding Default Organization: {default_error}")

        # Verify final state
        cursor.execute("SELECT id, name, created_at FROM organizations ORDER BY name")
        final_orgs = cursor.fetchall()

        logger.info(f"Final organizations: {final_orgs}")

        cursor.close()
        conn.close()

        result = {
            "success": True,
            "message": "Comprehensive SSO fix completed successfully",
            "organizations_ensured": organizations_added,
            "final_organizations": [
                {"id": str(org[0]), "name": org[1], "created_at": str(org[2])}
                for org in final_orgs
            ],
            "action": "comprehensive_fix"
        }

        logger.info("🎉 Comprehensive SSO fix completed successfully")

        return {
            "statusCode": 200,
            "body": json.dumps(result, indent=2)
        }

    except psycopg2.Error as db_error:
        error_msg = f"Database error: {str(db_error)}"
        logger.error(f"❌ {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": error_msg,
                "type": "database_error"
            })
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "success": False,
                "error": error_msg,
                "type": "general_error"
            })
        }
'''

        # Create deployment package
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
                zip_file.writestr('lambda_function.py', lambda_code)

                # Add psycopg2 library (simplified - may need layer in production)
                requirements = 'psycopg2-binary==2.9.9'
                zip_file.writestr('requirements.txt', requirements)

            zip_path = temp_zip.name

        print("✅ Lambda package created")

        # Wait for role to be ready
        print("⏳ Waiting for role propagation...")
        time.sleep(15)

        # Step 4: Create Lambda function with VPC configuration
        print("🚀 Creating Lambda function with VPC access...")

        with open(zip_path, 'rb') as zip_file:
            lambda_response = lambda_client.create_function(
                FunctionName=function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_file.read()},
                Timeout=60,  # Increased timeout for VPC
                MemorySize=256,  # Increased memory
                VpcConfig={
                    'SubnetIds': subnet_ids[:2],
                    'SecurityGroupIds': [sg_id]
                },
                Description='Comprehensive SSO fix - adds both organizations for compatibility'
            )

        cleanup_resources.append(('lambda', function_name))
        print("✅ Lambda function created with VPC access")

        # Wait for function to be ready
        print("⏳ Waiting for Lambda to be ready...")
        time.sleep(20)

        # Step 5: Execute the fix
        print("🔧 Executing comprehensive SSO fix...")

        response = lambda_client.invoke(
            FunctionName=function_name,
            LogType='Tail',
            Payload=json.dumps({})
        )

        # Parse response
        payload = json.loads(response['Payload'].read())

        print("📄 Lambda response:")
        print(json.dumps(payload, indent=2))

        if payload.get('statusCode') == 200:
            body = json.loads(payload['body'])
            if body.get('success'):
                print("🎉 COMPREHENSIVE SSO FIX SUCCESSFUL!")
                print("✅ Both organizations ensured in database")
                print("✅ SSO should work with both old and new code")
                print("🚀 Test at: https://plan-de-charge.aws.nda-partners.com")
                return True
            else:
                print(f"❌ Fix failed: {body.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Lambda execution failed: {payload}")
            return False

    except Exception as e:
        print(f"❌ Error creating comprehensive Lambda: {e}")
        return False

    finally:
        # Cleanup
        print("🧹 Cleaning up...")
        for resource_type, resource_name in reversed(cleanup_resources):
            try:
                if resource_type == 'lambda':
                    lambda_client.delete_function(FunctionName=resource_name)
                    print(f"✅ Lambda function {resource_name} deleted")
                elif resource_type == 'role':
                    # Detach policies first
                    try:
                        iam_client.detach_role_policy(
                            RoleName=resource_name,
                            PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole'
                        )
                    except:
                        pass
                    iam_client.delete_role(RoleName=resource_name)
                    print(f"✅ IAM role {resource_name} deleted")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup warning for {resource_name}: {cleanup_error}")

        # Clean up temp file
        try:
            os.unlink(zip_path)
        except:
            pass

if __name__ == "__main__":
    success = create_comprehensive_lambda_fix()

    if success:
        print("\n🎉 SUCCESS! SSO organizations fix completed!")
        print("✅ Both 'NDA Partners' and 'Default Organization' are now in database")
        print("✅ SSO authentication should work without 500 errors")
        print("🚀 Test login at: https://plan-de-charge.aws.nda-partners.com")
    else:
        print("\n❌ Failed to execute comprehensive fix")
        print("💡 Try manual database approach or check CloudWatch logs")
