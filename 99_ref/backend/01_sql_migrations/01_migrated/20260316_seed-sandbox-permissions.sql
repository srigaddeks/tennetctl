-- ─────────────────────────────────────────────────────────────────────────────
-- SANDBOX PERMISSION SEEDING
-- Seeds feature flag, custom actions, feature permissions, and role-permission links
-- for the control test sandbox environment
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Custom permission actions (execute, promote)
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000005001', 'execute', 'Execute', 'Execute a control test or sandbox run.', 80, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005002', 'promote', 'Promote', 'Promote a sandbox artifact to production.', 90, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flag
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_scope, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000005010', 'sandbox', 'Sandbox', 'Control test sandbox environment for building, testing, and promoting runtime compliance checks', 'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Feature permissions (6 total)
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000005020', 'sandbox.view',    'view',    'sandbox', 'View Sandbox',    'Can view sandbox environments and test runs',             NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005021', 'sandbox.create',  'create',  'sandbox', 'Create Sandbox',  'Can create new sandbox environments and test definitions', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005022', 'sandbox.update',  'update',  'sandbox', 'Update Sandbox',  'Can update sandbox configurations and test parameters',   NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005023', 'sandbox.delete',  'delete',  'sandbox', 'Delete Sandbox',  'Can delete sandbox environments and test runs',           NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005024', 'sandbox.execute', 'execute', 'sandbox', 'Execute Sandbox', 'Can execute control tests in the sandbox',                NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005025', 'sandbox.promote', 'promote', 'sandbox', 'Promote Sandbox', 'Can promote sandbox artifacts to production',              NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Role-permission assignments (grc_compliance_lead gets ALL 6 sandbox permissions)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'sandbox.view','sandbox.create','sandbox.update','sandbox.delete',
    'sandbox.execute','sandbox.promote'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003100' AND lnk.feature_permission_id = fp.id
);

-- grc_control_owner gets view, create, update, execute (can build and run tests, not promote or delete)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003101',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'sandbox.view','sandbox.create','sandbox.update','sandbox.execute'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003101' AND lnk.feature_permission_id = fp.id
);

-- grc_risk_manager gets view and execute (can view and run tests, not modify)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003102',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'sandbox.view','sandbox.execute'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003102' AND lnk.feature_permission_id = fp.id
);
