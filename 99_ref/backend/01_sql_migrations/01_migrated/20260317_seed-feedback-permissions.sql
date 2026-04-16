-- ===========================================================================
-- Migration: Seed feedback feature flag and permissions
-- Date: 2026-03-17
-- ===========================================================================

-- 1. Feature flag
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code, access_mode,
     lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000540', 'feedback', 'Feedback & Support',
     'User feedback submission and support ticket management',
     'platform', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature permissions
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000541', 'feedback.view',   'feedback', 'view',
     'View Feedback Tickets', 'View own submitted feedback tickets', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000542', 'feedback.create', 'feedback', 'create',
     'Submit Feedback', 'Submit new feedback or support tickets', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000543', 'feedback.update', 'feedback', 'update',
     'Update Feedback', 'Edit own open feedback tickets', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000544', 'feedback.delete', 'feedback', 'delete',
     'Delete Feedback', 'Delete own open feedback tickets', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000545', 'feedback.manage', 'feedback', 'assign',
     'Manage Feedback Queue', 'Triage, assign, change status on any ticket', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Grant feedback.view/create/update/delete to basic_user (all registered users)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'basic_user'
  AND fp.code IN ('feedback.view', 'feedback.create', 'feedback.update', 'feedback.delete')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );

-- 4. Grant all feedback permissions to platform_super_admin role
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'platform_super_admin'
  AND fp.code LIKE 'feedback.%'
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );
