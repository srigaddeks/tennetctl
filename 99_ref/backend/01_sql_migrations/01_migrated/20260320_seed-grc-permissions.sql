-- ─────────────────────────────────────────────────────────────────────────────
-- GRC PERMISSION SEEDING
-- Seeds feature flags, feature permissions, GRC roles, and role-permission links
-- ─────────────────────────────────────────────────────────────────────────────

-- 0. Seed 'delete' permission action (needed by GRC and sandbox permissions)
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES ('00000000-0000-0000-0000-000000005000', 'delete', 'Delete', 'Delete feature-managed state.', 35, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 1. Feature flag category
INSERT INTO "03_auth_manage"."11_dim_feature_flag_categories" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003000', 'grc', 'GRC', 'Governance, Risk, and Compliance features', 10, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flags
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_scope, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003001', 'framework_management',  'Framework Management',  'Framework library and versions',                         'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003002', 'risk_registry',        'Risk Registry',        'Risk register, assessments, treatment plans',             'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003003', 'control_test_library', 'Control Test Library', 'Reusable control test library and evidence templates',    'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003004', 'task_management',      'Task Management',      'GRC task management with dependencies and assignments',   'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003005', 'control_management',   'Control Management',   'Control library within frameworks',                       'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Feature permissions (20 total)
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003010', 'frameworks.view',   'view',   'framework_management', 'View Frameworks',   'Can view framework library, controls, requirements',  NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003011', 'frameworks.create', 'create', 'framework_management', 'Create Frameworks', 'Can create new frameworks and framework versions',    NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003012', 'frameworks.update', 'update', 'framework_management', 'Update Frameworks', 'Can update framework details and publish versions',   NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003013', 'frameworks.delete', 'delete', 'framework_management', 'Delete Frameworks', 'Can delete frameworks and unpublished versions',      NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003020', 'controls.view',     'view',   'control_management', 'View Controls',     'Can view controls within frameworks',                 NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003021', 'controls.create',   'create', 'control_management', 'Create Controls',   'Can create new controls in frameworks',               NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003022', 'controls.update',   'update', 'control_management', 'Update Controls',   'Can update control details and mappings',             NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003023', 'controls.delete',   'delete', 'control_management', 'Delete Controls',   'Can delete controls from frameworks',                 NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003030', 'tests.view',        'view',   'control_test_library',      'View Tests',        'Can view control test library',                       NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003031', 'tests.create',      'create', 'control_test_library',      'Create Tests',      'Can create new control tests',                        NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003032', 'tests.update',      'update', 'control_test_library',      'Update Tests',      'Can update test definitions and mappings',            NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003033', 'tests.delete',      'delete', 'control_test_library',      'Delete Tests',      'Can delete control tests',                            NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003040', 'risks.view',        'view',   'risk_registry',      'View Risks',        'Can view risk register and assessments',              NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003041', 'risks.create',      'create', 'risk_registry',      'Create Risks',      'Can create new risks and treatment plans',            NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003042', 'risks.update',      'update', 'risk_registry',      'Update Risks',      'Can update risks, assess, and link controls',         NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003043', 'risks.delete',      'delete', 'risk_registry',      'Delete Risks',      'Can delete risks from the registry',                  NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003050', 'tasks.view',        'view',   'task_management',    'View Tasks',        'Can view tasks and task details',                     NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003051', 'tasks.create',      'create', 'task_management',    'Create Tasks',      'Can create new tasks',                                NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003052', 'tasks.update',      'update', 'task_management',    'Update Tasks',      'Can update task details and status',                  NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003053', 'tasks.assign',      'assign', 'task_management',    'Assign Tasks',      'Can assign and reassign tasks to users',              NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. GRC Roles
INSERT INTO "03_auth_manage"."16_fct_roles" (id, tenant_key, role_level_code, code, name, description, scope_org_id, scope_workspace_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
VALUES
    ('00000000-0000-0000-0000-000000003100', '__platform__', 'platform', 'grc_compliance_lead', 'GRC Compliance Lead', 'Full access to all GRC features', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),
    ('00000000-0000-0000-0000-000000003101', '__platform__', 'platform', 'grc_control_owner',   'GRC Control Owner',   'View frameworks, manage controls and tests', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL),
    ('00000000-0000-0000-0000-000000003102', '__platform__', 'platform', 'grc_risk_manager',    'GRC Risk Manager',    'Full risk management, view frameworks and controls', NULL, NULL, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW(), NULL, NULL)
ON CONFLICT DO NOTHING;

-- 5. Role-permission assignments (grc_compliance_lead gets ALL 20 permissions)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view','frameworks.create','frameworks.update','frameworks.delete',
    'controls.view','controls.create','controls.update','controls.delete',
    'tests.view','tests.create','tests.update','tests.delete',
    'risks.view','risks.create','risks.update','risks.delete',
    'tasks.view','tasks.create','tasks.update','tasks.assign'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003100' AND lnk.feature_permission_id = fp.id
);

-- grc_control_owner permissions
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003101',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'frameworks.view',
    'controls.view','controls.update',
    'tests.view','tests.create','tests.update','tests.delete',
    'tasks.view','tasks.update','tasks.assign',
    'risks.view'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003101' AND lnk.feature_permission_id = fp.id
);

-- grc_risk_manager permissions
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003102',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'risks.view','risks.create','risks.update','risks.delete',
    'frameworks.view',
    'controls.view',
    'tasks.view','tasks.create','tasks.assign'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003102' AND lnk.feature_permission_id = fp.id
);

-- 6. Assign grc_compliance_lead role to all existing groups (so test user gets access)
INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (id, group_id, role_id, assignment_status, effective_from, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    g.id,
    '00000000-0000-0000-0000-000000003100',
    'active',
    NOW(),
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."17_fct_user_groups" g
WHERE g.is_active = TRUE AND g.is_deleted = FALSE
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."19_lnk_group_role_assignments" gra
    WHERE gra.group_id = g.id AND gra.role_id = '00000000-0000-0000-0000-000000003100'
);
