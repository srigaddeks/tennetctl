-- ===========================================================================
-- Migration: Seed docs feature flag and permissions
-- Date: 2026-03-17
-- ===========================================================================

-- 1. Feature flag
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code, access_mode,
     lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000550', 'docs', 'Document Library',
     'Global and org-scoped document library for policies, frameworks, and RAG knowledge base',
     'platform', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature permissions
--    docs.manage maps to 'assign' action (the "super admin manage" action pattern)
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000551', 'docs.view',   'docs', 'view',
     'View Documents', 'Browse and download documents', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000552', 'docs.create', 'docs', 'create',
     'Upload Documents', 'Upload new documents', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000553', 'docs.update', 'docs', 'update',
     'Update Documents', 'Edit document metadata', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000554', 'docs.delete', 'docs', 'delete',
     'Delete Documents', 'Delete documents', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000000555', 'docs.manage', 'docs', 'assign',
     'Manage Library', 'Manage global library (super admin only)', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Grant docs.view to basic_user (all registered users can read docs)
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
  AND fp.code IN ('docs.view')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );

-- 4. Grant all docs permissions to platform_super_admin role
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
  AND fp.code LIKE 'docs.%'
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );
