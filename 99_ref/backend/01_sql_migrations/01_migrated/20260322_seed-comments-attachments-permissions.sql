-- ─────────────────────────────────────────────────────────────────────────────
-- COMMENTS & ATTACHMENTS PERMISSION SEEDING
-- Adds feature flags, permissions, and role assignments for comments/attachments
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Feature flags for comments and attachments
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (id, code, name, description, feature_scope, feature_flag_category_code, access_mode, lifecycle_state, initial_audience, env_dev, env_staging, env_prod, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003008', 'comments',    'Comments',    'Collaborative comments on GRC entities with replies and reactions', 'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003007', 'attachments', 'Attachments', 'File attachments on GRC entities with cloud storage integration',   'platform', 'grc', 'permissioned', 'active', 'all', TRUE, TRUE, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2a. Seed 'resolve' and 'manage' permission actions if not present
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000005020', 'resolve', 'Resolve', 'Resolve or unresolve feature-managed items.', 55, NOW(), NOW()),
    ('00000000-0000-0000-0000-000000005021', 'manage',  'Manage',  'Manage and moderate feature-managed items.',  60, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 2b. Feature permissions for comments (6 permissions)
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003160', 'comments.view',    'view',    'comments', 'View Comments',    'Can view comments on any entity',                        NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003161', 'comments.create',  'create',  'comments', 'Create Comments',  'Can create comments and replies on any entity',           NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003162', 'comments.update',  'update',  'comments', 'Edit Comments',    'Can edit own comments',                                   NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003163', 'comments.delete',  'delete',  'comments', 'Delete Comments',  'Can soft-delete own comments; hard delete requires admin', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003164', 'comments.manage',  'manage',  'comments', 'Manage Comments',  'Can pin, lock, and moderate comments (workspace admins)', NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003165', 'comments.resolve', 'resolve', 'comments', 'Resolve Comments', 'Can resolve and unresolve comment threads',               NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 3. Feature permissions for attachments (3 permissions)
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (id, code, permission_action_code, feature_flag_code, name, description, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000003170', 'attachments.view',   'view',   'attachments', 'View Attachments',   'Can view and download attachments',                        NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003171', 'attachments.create', 'create', 'attachments', 'Upload Attachments', 'Can upload new attachments to any entity',                 NOW(), NOW()),
    ('00000000-0000-0000-0000-000000003172', 'attachments.delete', 'delete', 'attachments', 'Delete Attachments', 'Can delete attachments (own); admin can delete any',       NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- 4. Grant all comments + attachments permissions to grc_compliance_lead
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003100',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'comments.view','comments.create','comments.update','comments.delete','comments.manage','comments.resolve',
    'attachments.view','attachments.create','attachments.delete'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003100' AND lnk.feature_permission_id = fp.id
);

-- 5. Grant comments.view/create/update, attachments.view/create to grc_control_owner
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003101',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'comments.view','comments.create','comments.update',
    'attachments.view','attachments.create'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003101' AND lnk.feature_permission_id = fp.id
);

-- 6. Grant comments.view/create/update/resolve, attachments.view/create to grc_risk_manager
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (id, role_id, feature_permission_id, is_active, is_disabled, is_deleted, is_test, is_system, is_locked, created_at, updated_at, created_by, updated_by)
SELECT
    gen_random_uuid(),
    '00000000-0000-0000-0000-000000003102',
    fp.id,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'comments.view','comments.create','comments.update','comments.resolve',
    'attachments.view','attachments.create'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = '00000000-0000-0000-0000-000000003102' AND lnk.feature_permission_id = fp.id
);
