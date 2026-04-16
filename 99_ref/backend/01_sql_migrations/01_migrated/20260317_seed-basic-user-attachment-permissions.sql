-- ===========================================================================
-- Migration: Grant attachments.create and attachments.view to basic_user role
-- Date: 2026-03-17
-- Description: All registered users (via default_users group → basic_user role)
--   can view and upload attachments by default. Delete requires explicit permission.
-- ===========================================================================

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id, created_at, updated_at
)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000002001',  -- basic_user role
    fp.id,
    NOW(), NOW()
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN ('attachments.create', 'attachments.view')
ON CONFLICT DO NOTHING;
