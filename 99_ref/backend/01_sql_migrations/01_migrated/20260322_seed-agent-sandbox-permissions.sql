-- ─────────────────────────────────────────────────────────────────────────────
-- AGENT SANDBOX PERMISSION SEEDING
-- Seeds feature flag, permission actions, feature permissions, and
-- role-permission links for the agent sandbox module.
-- ─────────────────────────────────────────────────────────────────────────────

-- 0. Ensure 'ai' feature flag category exists
INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
VALUES (gen_random_uuid(), 'ai', 'AI', 'AI and agent platform features', 11, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 1. Ensure 'execute' and 'manage' actions exist (execute already seeded by sandbox)
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000007001', 'manage', 'Manage', 'Full management access including approvals and registry.', 100, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flag
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_scope, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000007010', 'agent_sandbox', 'Agent Sandbox', 'Build, test, and deploy autonomous AI agents from the UI', 'platform', 'ai', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Feature permissions
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000007020', 'agent_sandbox.view',    'view',    'agent_sandbox', 'View Agent Sandbox',    'Can view agents, tools, and execution runs',                NOW(), NOW()),
    ('00000000-0000-0000-0000-000000007021', 'agent_sandbox.create',  'create',  'agent_sandbox', 'Create Agent Sandbox',  'Can create and update agents, tools, and test scenarios',   NOW(), NOW()),
    ('00000000-0000-0000-0000-000000007022', 'agent_sandbox.execute', 'execute', 'agent_sandbox', 'Execute Agent Sandbox', 'Can execute agents and test scenarios',                      NOW(), NOW()),
    ('00000000-0000-0000-0000-000000007023', 'agent_sandbox.manage',  'manage',  'agent_sandbox', 'Manage Agent Sandbox',  'Can manage tool registry and approve agent runs',           NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Role-permission assignments

-- grc_compliance_lead gets ALL 4 agent_sandbox permissions
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'agent_sandbox.view', 'agent_sandbox.create', 'agent_sandbox.execute', 'agent_sandbox.manage'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003100' AND lnk.feature_permission_id = fp.id
);

-- grc_control_owner gets view, create, execute (can build and run agents, not manage registry)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003101',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'agent_sandbox.view', 'agent_sandbox.create', 'agent_sandbox.execute'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003101' AND lnk.feature_permission_id = fp.id
);

-- grc_risk_manager gets view and execute (can view and run agents, not modify)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003102',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'agent_sandbox.view', 'agent_sandbox.execute'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003102' AND lnk.feature_permission_id = fp.id
);
