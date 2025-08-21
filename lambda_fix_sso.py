import json
import psycopg2
import os

def lambda_handler(event, context):
    """
    Lambda function to fix SSO by adding 'Default Organization' to database.
    This is a one-time fix for the 500 Internal Server Error.
    """

    print("🚀 Starting SSO fix - adding Default Organization")

    try:
        # Database connection details from environment variables
        db_host = os.environ.get('DB_HOST')
        db_name = os.environ.get('DB_NAME', 'plancharge')
        db_user = os.environ.get('DB_USER', 'plancharge')
        db_password = os.environ.get('DB_PASSWORD')
        db_port = os.environ.get('DB_PORT', '5432')

        if not all([db_host, db_password]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required environment variables: DB_HOST, DB_PASSWORD'
                })
            }

        print(f"🔗 Connecting to database: {db_host}:{db_port}/{db_name}")

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            database=db_name,
            user=db_user,
            password=db_password,
            connect_timeout=10
        )

        conn.autocommit = True
        cursor = conn.cursor()

        print("✅ Connected to database successfully")

        # Check current organizations
        cursor.execute("SELECT id, name FROM organizations ORDER BY name;")
        existing_orgs = cursor.fetchall()

        print(f"📊 Current organizations: {existing_orgs}")

        # Check if Default Organization already exists
        default_org_exists = any('Default Organization' in str(org) for org in existing_orgs)

        if default_org_exists:
            print("✅ 'Default Organization' already exists - no fix needed")
            result = {
                'success': True,
                'message': 'Default Organization already exists',
                'organizations': [{'id': str(org[0]), 'name': org[1]} for org in existing_orgs],
                'action': 'none_needed'
            }
        else:
            print("➕ Adding 'Default Organization'...")

            # Add Default Organization
            cursor.execute("""
                INSERT INTO organizations (id, name, created_at, updated_at, deleted_at)
                VALUES (%s, %s, NOW(), NOW(), NULL)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    updated_at = NOW();
            """, (
                '00000000-0000-0000-0000-000000000002',
                'Default Organization'
            ))

            print("✅ Default Organization added successfully")

            # Verify the addition
            cursor.execute("SELECT id, name FROM organizations ORDER BY name;")
            updated_orgs = cursor.fetchall()

            print(f"📊 Updated organizations: {updated_orgs}")

            result = {
                'success': True,
                'message': 'Default Organization added successfully',
                'organizations': [{'id': str(org[0]), 'name': org[1]} for org in updated_orgs],
                'action': 'added'
            }

        cursor.close()
        conn.close()

        print("🎉 SSO fix completed successfully")

        return {
            'statusCode': 200,
            'body': json.dumps(result, indent=2)
        }

    except psycopg2.Error as db_error:
        error_msg = f"Database error: {str(db_error)}"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg,
                'type': 'database_error'
            })
        }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'success': False,
                'error': error_msg,
                'type': 'general_error'
            })
        }

# For local testing
if __name__ == "__main__":
    # Test event
    test_event = {}
    test_context = type('Context', (), {})()

    # Set test environment variables
    os.environ['DB_HOST'] = 'your-rds-endpoint-here'
    os.environ['DB_PASSWORD'] = 'your-password-here'

    result = lambda_handler(test_event, test_context)
    print(json.dumps(result, indent=2))
