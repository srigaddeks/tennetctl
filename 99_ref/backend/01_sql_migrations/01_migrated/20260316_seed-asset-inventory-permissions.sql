-- ─────────────────────────────────────────────────────────────────────────────
-- ASSET INVENTORY PERMISSION SEEDING
-- Seeds feature flag, custom actions, feature permissions, and role-permission links
-- for the asset inventory module (external provider discovery and log ingestion)
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Custom permission actions (collect is new; view/create/update/delete/execute already exist)
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006001', 'collect', 'Collect', 'Trigger or cancel asset collection runs.', 85, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature flag
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_scope, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006010', 'asset_inventory', 'Asset Inventory', 'Asset discovery and log ingestion from external providers (GitHub, Azure Storage, etc.) for compliance evidence collection', 'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, FALSE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Feature permissions (5 total)
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006020', 'asset_inventory.view',    'view',    'asset_inventory', 'View Asset Inventory',    'View asset inventory, providers, connectors, discovered assets',  NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006021', 'asset_inventory.create',  'create',  'asset_inventory', 'Create Asset Inventory',  'Create connector instances and configure log sources',            NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006022', 'asset_inventory.update',  'update',  'asset_inventory', 'Update Asset Inventory',  'Update connector configuration and credentials',                  NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006023', 'asset_inventory.delete',  'delete',  'asset_inventory', 'Delete Asset Inventory',  'Delete connectors and assets',                                    NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006024', 'asset_inventory.collect', 'collect', 'asset_inventory', 'Collect Asset Inventory', 'Trigger manual collection runs and test connections',              NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Role-permission assignments (grc_compliance_lead gets ALL 5 permissions)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'asset_inventory.view','asset_inventory.create','asset_inventory.update',
    'asset_inventory.delete','asset_inventory.collect'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003100' AND lnk.feature_permission_id = fp.id
);

-- grc_control_owner gets view, create, update, collect (can configure and trigger collection, not delete)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003101',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'asset_inventory.view','asset_inventory.create','asset_inventory.update','asset_inventory.collect'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003101' AND lnk.feature_permission_id = fp.id
);

-- grc_risk_manager gets view and collect (read-only + can trigger collection)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003102',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'asset_inventory.view','asset_inventory.collect'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003102' AND lnk.feature_permission_id = fp.id
);
