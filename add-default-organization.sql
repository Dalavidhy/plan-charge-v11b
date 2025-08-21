-- ============================================================================
-- Workaround: Add "Default Organization" to Database
-- ============================================================================
-- This is a temporary workaround for the SSO 500 error.
-- The backend code expects "Default Organization" but database has "NDA Partners".
-- This adds the expected organization so SSO authentication can work.

-- Add Default Organization that backend expects
INSERT INTO organizations (id, name, created_at, updated_at, deleted_at)
VALUES (
    '00000000-0000-0000-0000-000000000002',
    'Default Organization',
    NOW(),
    NOW(),
    NULL
)
ON CONFLICT (id) DO UPDATE SET
    name = EXCLUDED.name,
    updated_at = NOW();

-- Verify both organizations exist
SELECT id, name, created_at
FROM organizations
WHERE name IN ('NDA Partners', 'Default Organization')
ORDER BY created_at;

-- ============================================================================
-- INSTRUCTIONS:
-- ============================================================================
--
-- Execute this SQL using one of these methods:
--
-- 1. AWS RDS Query Editor:
--    - Go to AWS Console -> RDS -> Query Editor
--    - Select your PostgreSQL database
--    - Paste and execute this SQL
--
-- 2. PostgreSQL client (if you have direct access):
--    - Connect to the database
--    - Execute this SQL
--
-- 3. Copy SQL to existing container and execute
--
-- ============================================================================
-- EXPECTED RESULT:
-- ============================================================================
-- After executing this SQL:
-- - Database will have both "NDA Partners" and "Default Organization"
-- - Backend SSO code will find "Default Organization" and work correctly
-- - Users can successfully authenticate via Azure AD
-- - No 500 Internal Server Error during SSO token exchange
-- ============================================================================

-- Check if the insert was successful
DO $$
BEGIN
    IF EXISTS(SELECT 1 FROM organizations WHERE name = 'Default Organization') THEN
        RAISE NOTICE 'SUCCESS: Default Organization added to database';
        RAISE NOTICE 'SSO authentication should now work correctly';
    ELSE
        RAISE NOTICE 'WARNING: Default Organization not found after insert';
    END IF;
END $$;
