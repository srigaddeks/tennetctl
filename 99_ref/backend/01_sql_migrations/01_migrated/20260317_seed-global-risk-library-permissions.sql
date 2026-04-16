-- ===========================================================================
-- Migration: Seed global_risk_library feature flag and permissions
-- Date: 2026-03-17
-- Adds platform-level Global Risk Library feature to the grc category,
-- seeds its four permissions, and assigns all four to grc_compliance_lead.
-- ===========================================================================

-- 1. Feature flag (grc category already exists)
INSERT INTO "03_auth_manage"."14_dim_feature_flags"
    (id, code, name, description, feature_scope, feature_flag_category_code, access_mode,
     lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003006', 'global_risk_library', 'Global Risk Library',
     'Platform-level global risk registry for publishing risks to workspaces',
     'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature permissions
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003060', 'global_risk_library.view',   'global_risk_library', 'view',
     'View Global Risk Library',   'Can view global risks and published risk entries',    NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003061', 'global_risk_library.create', 'global_risk_library', 'create',
     'Create Global Risk Library',  'Can create new risks in the global risk library',     NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003062', 'global_risk_library.update', 'global_risk_library', 'update',
     'Update Global Risk Library',  'Can update global risk entries and publish to workspaces', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003063', 'global_risk_library.delete', 'global_risk_library', 'delete',
     'Delete Global Risk Library',  'Can delete risks from the global risk library',       NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Assign all four permissions to platform_super_admin and super_admin and grc_compliance_lead
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code IN ('grc_compliance_lead', 'super_admin', 'platform_super_admin')
  AND fp.code IN (
      'global_risk_library.view',
      'global_risk_library.create',
      'global_risk_library.update',
      'global_risk_library.delete'
  )
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
      WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
  );
