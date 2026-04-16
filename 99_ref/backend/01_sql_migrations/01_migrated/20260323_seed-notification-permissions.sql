-- ─────────────────────────────────────────────────────────────────────────────
-- NOTIFICATION SYSTEM PERMISSION SEEDING
-- Seeds feature flags, permissions, and role-permission links for:
--   notification_system   (queue, SMTP, delivery reports, send-test)
--   notification_templates  (template CRUD)
--   notification_broadcasts (rules, broadcasts, releases, incidents)
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Feature flags
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_scope, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006001', 'notification_system',     'Notification System',     'Notification queue, delivery, SMTP config, and reporting',            'platform', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006002', 'notification_templates',  'Notification Templates',  'Manage notification templates and versioning',                         'platform', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006003', 'notification_broadcasts', 'Notification Broadcasts', 'Manage notification rules, broadcasts, releases, and incidents',       'platform', 'admin', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2. Feature permissions — notification_system
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006110', 'notification_system.view',   'view',   'notification_system', 'View Notification System',   'Can view notification queue, delivery reports, and SMTP config', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006111', 'notification_system.create', 'create', 'notification_system', 'Create Notification',        'Can enqueue and send notifications',                             NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006112', 'notification_system.update', 'update', 'notification_system', 'Update Notification System', 'Can retry, dead-letter queue items, and update system config',   NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Feature permissions — notification_templates
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006120', 'notification_templates.view',   'view',   'notification_templates', 'View Notification Templates',   'Can view notification templates and versions', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006121', 'notification_templates.create', 'create', 'notification_templates', 'Create Notification Template',  'Can create notification templates',            NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006122', 'notification_templates.update', 'update', 'notification_templates', 'Update Notification Template',  'Can update and version notification templates', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Feature permissions — notification_broadcasts
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000006130', 'notification_broadcasts.view',   'view',   'notification_broadcasts', 'View Notification Broadcasts',   'Can view rules, broadcasts, releases, and incidents', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006131', 'notification_broadcasts.create', 'create', 'notification_broadcasts', 'Create Notification Broadcast',  'Can create rules, broadcasts, releases, and incidents', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000006132', 'notification_broadcasts.update', 'update', 'notification_broadcasts', 'Update Notification Broadcast',  'Can update, publish, archive rules, broadcasts, releases, and incidents', NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 5. Assign ALL notification permissions to platform_super_admin role
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000000601',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'notification_system.view',   'notification_system.create',   'notification_system.update',
    'notification_templates.view','notification_templates.create','notification_templates.update',
    'notification_broadcasts.view','notification_broadcasts.create','notification_broadcasts.update'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000000601' AND lnk.feature_permission_id = fp.id
);
