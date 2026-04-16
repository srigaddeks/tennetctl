-- ─────────────────────────────────────────────────────────────────────────────
-- FRAMEWORK APPROVE PERMISSION + LIBRARY CURATOR ROLE
-- Adds `frameworks.approve` permission (separate from `frameworks.update`)
-- so authors cannot approve their own submissions.
-- Adds `library_curator` system role with approve + full GRC access.
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Add frameworks.approve permission
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003014',
     'frameworks.approve', 'approve', 'framework_management',
     'Approve Frameworks',
     'Can approve framework submissions for the global marketplace. '
     'Separate from frameworks.update so authors cannot self-approve.',
     NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Add library_curator platform role
INSERT INTO "03_auth_manage"."16_fct_roles"
    (id, tenant_key, role_level_code, code, name, description,
     scope_org_id, scope_workspace_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
VALUES
    ('00000000-0000-0000-0000-000000003103',
     '__platform__', 'platform', 'library_curator',
     'Library Curator',
     'Curates the global framework and control library. '
     'Can approve/reject marketplace submissions and manage all GRC content.',
     NULL, NULL,
     TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
     NOW(), NOW(), NULL, NULL)
ON CONFLICT DO NOTHING;

-- 3. Assign permissions to library_curator:
--    All GRC permissions + frameworks.approve
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003103',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view', 'frameworks.create', 'frameworks.update',
    'frameworks.delete', 'frameworks.approve',
    'controls.view', 'controls.create', 'controls.update', 'controls.delete',
    'tests.view', 'tests.create', 'tests.update', 'tests.delete',
    'risks.view', 'risks.create', 'risks.update', 'risks.delete',
    'tasks.view', 'tasks.create', 'tasks.update', 'tasks.assign'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003103'
      AND lnk.feature_permission_id = fp.id
);

-- 4. Also grant frameworks.approve to platform_super_admin
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
WHERE r.code = 'platform_super_admin'
  AND fp.code = 'frameworks.approve'
  AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id AND lnk.feature_permission_id = fp.id
);

-- 5. Also grant frameworks.approve to grc_compliance_lead (platform admin)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code = 'frameworks.approve'
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003100'
      AND lnk.feature_permission_id = fp.id
);
