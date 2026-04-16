-- Migration: Add test123@kreesalis.com to platform_super_admin group
--
-- This gives the test/dev user full platform super admin access for building
-- and testing all features. The platform_super_admin group already exists with
-- the platform_super_admin role and all feature governance permissions.

INSERT INTO "03_auth_manage"."18_lnk_group_memberships" (
    id, user_id, group_id,
    membership_status, effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(),
    'af88f921-2e07-48aa-a3e5-c556a2b2c223',
    '00000000-0000-0000-0000-000000000701',
    'active', TIMESTAMP '2026-03-15 00:00:00', NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    TIMESTAMP '2026-03-15 00:00:00', TIMESTAMP '2026-03-15 00:00:00',
    NULL, NULL, NULL, NULL
WHERE EXISTS (
    SELECT 1 FROM "03_auth_manage"."03_fct_users"
    WHERE id = 'af88f921-2e07-48aa-a3e5-c556a2b2c223'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."18_lnk_group_memberships"
    WHERE user_id = 'af88f921-2e07-48aa-a3e5-c556a2b2c223'
      AND group_id = '00000000-0000-0000-0000-000000000701'
      AND is_deleted = FALSE
);
