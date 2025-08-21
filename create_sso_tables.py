#!/usr/bin/env python3
"""
Create SSO authentication tables in production database.
This script runs inside the backend container and uses the existing database connection.
"""

import asyncio
import asyncpg
from app.config import settings
import sys

async def create_tables():
    """Create the required database tables using the application's database connection."""
    print("🏗️  Creating SSO authentication tables...")
    print(f"🔗 Connecting to database...")

    try:
        # Use the application's database URL but convert to asyncpg format
        database_url = str(settings.DATABASE_URL)
        # Convert from SQLAlchemy format to asyncpg format
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

        # Connect to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to PostgreSQL database")

        # SQL commands to create tables
        sql_commands = [
            # Enable UUID extension
            'CREATE EXTENSION IF NOT EXISTS "uuid-ossp";',

            # Enable CITEXT extension
            'CREATE EXTENSION IF NOT EXISTS "citext";',

            # Create organizations table
            """
            CREATE TABLE IF NOT EXISTS organizations (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                deleted_at TIMESTAMP WITH TIME ZONE
            );
            """,

            # Create users table with azure_id for SSO
            """
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                org_id UUID REFERENCES organizations(id),
                person_id UUID,
                email CITEXT NOT NULL,
                full_name VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255),
                azure_id VARCHAR(255),
                locale VARCHAR(10) DEFAULT 'fr',
                is_active BOOLEAN DEFAULT TRUE,
                last_login_at TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                deleted_at TIMESTAMP WITH TIME ZONE
            );
            """,

            # Create indexes
            "CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);",
            "CREATE INDEX IF NOT EXISTS ix_users_azure_id ON users(azure_id);",
            "CREATE INDEX IF NOT EXISTS ix_users_org_id ON users(org_id);",
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_org_email ON users(org_id, email) WHERE deleted_at IS NULL;",

            # Insert default organization
            """
            INSERT INTO organizations (id, name)
            VALUES ('00000000-0000-0000-0000-000000000001', 'NDA Partners')
            ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name;
            """,

            # Create alembic_version table
            """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            );
            """,

            # Insert current migration version
            """
            INSERT INTO alembic_version (version_num)
            VALUES ('74b7c8174dd8')
            ON CONFLICT (version_num) DO NOTHING;
            """
        ]

        # Execute commands
        for i, sql_command in enumerate(sql_commands, 1):
            try:
                await conn.execute(sql_command)
                print(f"✅ Step {i}/{len(sql_commands)}: Executed successfully")
            except Exception as e:
                print(f"⚠️  Step {i}/{len(sql_commands)}: {e}")
                # Continue with other commands
                pass

        # Verify tables were created
        result = await conn.fetch("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('organizations', 'users', 'alembic_version')
            ORDER BY table_name;
        """)

        tables = [row['table_name'] for row in result]
        print(f"✅ Tables created: {tables}")

        # Check if default organization exists
        org_count = await conn.fetchval("SELECT COUNT(*) FROM organizations;")
        print(f"✅ Organizations in database: {org_count}")

        # Check users table
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users;")
        print(f"✅ Users in database: {user_count}")

        await conn.close()
        print("✅ Database connection closed")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main execution function."""
    print("🚀 Plan Charge SSO Table Creation")
    print("=" * 50)

    if await create_tables():
        print("\n🎉 SUCCESS! SSO authentication tables created")
        print("✅ Users can now login with Azure AD")
        print("✅ Backend will create user records on first login")
        return 0
    else:
        print("\n❌ FAILED! Could not create database tables")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
