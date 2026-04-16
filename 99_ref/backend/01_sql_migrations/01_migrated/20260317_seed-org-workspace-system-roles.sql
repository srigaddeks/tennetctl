-- ─────────────────────────────────────────────────────────────────────────
-- Org-Level & Workspace-Level System Roles
--
-- Creates system roles at org and workspace levels so that membership_type
-- on org/workspace link tables maps cleanly to scoped permission groups.
--
-- Access model:
--   org_admin    → full org_management.* + workspace_management.* within their org
--   org_member   → org_management.view + workspace_management.view/create/update/assign/revoke
--   org_viewer   → org_management.view only (cannot interact with workspaces unless also ws member)
--
--   workspace_admin       → workspace_management.* within their workspace
--   workspace_contributor → workspace_management.view/update
--   workspace_viewer      → workspace_management.view only
--
-- Groups are NOT seeded here — they are created dynamically by the backend
-- when orgs/workspaces are created (_provision_org_system_groups,
-- _provision_workspace_system_groups). This migration only seeds:
--   1. Roles (16_fct_roles)
--   2. Role → Feature Permission links (20_lnk_role_feature_permissions)
-- ─────────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════
-- 0. ENSURE PLATFORM ROLE LEVEL EXISTS (referenced by basic_user but
--    missing from original dimension seed)
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."13_dim_role_levels" (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000000304', 'platform', 'Platform', 'Platform-wide non-admin scope.', 5, NOW(), NOW()
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."13_dim_role_levels" WHERE code = 'platform');


-- ═══════════════════════════════════════════════════════════════════════
-- 1. ORG-LEVEL SYSTEM ROLES
-- ═══════════════════════════════════════════════════════════════════════

-- org_admin: full org + workspace management
INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000004001', 'default', 'org', 'org_admin',
       'Org Admin', 'Full administrative control within an organization. Can manage org settings, members, and all workspaces.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'org_admin' AND tenant_key = 'default');

-- org_member: can view org, interact with workspaces
INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000004002', 'default', 'org', 'org_member',
       'Org Member', 'Standard organization member. Can view org, interact with all workspaces, but cannot administer the org.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'org_member' AND tenant_key = 'default');

-- org_viewer: read-only org access, no workspace access unless also ws member
INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000004003', 'default', 'org', 'org_viewer',
       'Org Viewer', 'Read-only organization access. Can view org details but cannot modify anything. No workspace access unless separately granted.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'org_viewer' AND tenant_key = 'default');


-- ═══════════════════════════════════════════════════════════════════════
-- 2. WORKSPACE-LEVEL SYSTEM ROLES
-- ═══════════════════════════════════════════════════════════════════════

-- workspace_admin: full workspace management
INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000004011', 'default', 'workspace', 'workspace_admin',
       'Workspace Admin', 'Full administrative control within a workspace. Can manage workspace settings and members.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'workspace_admin' AND tenant_key = 'default');

-- workspace_contributor: can view and update workspace
INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000004012', 'default', 'workspace', 'workspace_contributor',
       'Workspace Contributor', 'Can view and contribute to workspace content. Cannot manage members or settings.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'workspace_contributor' AND tenant_key = 'default');

-- workspace_viewer: read-only workspace access
INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT '00000000-0000-0000-0000-000000004013', 'default', 'workspace', 'workspace_viewer',
       'Workspace Viewer', 'Read-only workspace access. Can view workspace content but cannot modify anything.',
       NULL, NULL,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'workspace_viewer' AND tenant_key = 'default');


-- ═══════════════════════════════════════════════════════════════════════
-- 3. ORG_ADMIN PERMISSIONS — org_management.* + workspace_management.*
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000004001', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'org_management.view', 'org_management.create', 'org_management.update',
    'org_management.assign', 'org_management.revoke',
    'workspace_management.view', 'workspace_management.create', 'workspace_management.update',
    'workspace_management.assign', 'workspace_management.revoke'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000004001' AND rfp2.feature_permission_id = fp.id
);


-- ═══════════════════════════════════════════════════════════════════════
-- 4. ORG_MEMBER PERMISSIONS — org_management.view + workspace_management.*
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000004002', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'org_management.view',
    'workspace_management.view', 'workspace_management.create', 'workspace_management.update',
    'workspace_management.assign', 'workspace_management.revoke'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000004002' AND rfp2.feature_permission_id = fp.id
);


-- ═══════════════════════════════════════════════════════════════════════
-- 5. ORG_VIEWER PERMISSIONS — org_management.view only
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000004003', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'org_management.view'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000004003' AND rfp2.feature_permission_id = fp.id
);


-- ═══════════════════════════════════════════════════════════════════════
-- 6. WORKSPACE_ADMIN PERMISSIONS — workspace_management.*
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000004011', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'workspace_management.view', 'workspace_management.create', 'workspace_management.update',
    'workspace_management.assign', 'workspace_management.revoke'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000004011' AND rfp2.feature_permission_id = fp.id
);


-- ═══════════════════════════════════════════════════════════════════════
-- 7. WORKSPACE_CONTRIBUTOR PERMISSIONS — workspace_management.view + update
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000004012', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'workspace_management.view', 'workspace_management.update'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000004012' AND rfp2.feature_permission_id = fp.id
);


-- ═══════════════════════════════════════════════════════════════════════
-- 8. WORKSPACE_VIEWER PERMISSIONS — workspace_management.view only
-- ═══════════════════════════════════════════════════════════════════════

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT gen_random_uuid(), '00000000-0000-0000-0000-000000004013', fp.id,
       TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
       NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN (
    'workspace_management.view'
)
AND NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
    WHERE rfp2.role_id = '00000000-0000-0000-0000-000000004013' AND rfp2.feature_permission_id = fp.id
);


-- ═══════════════════════════════════════════════════════════════════════
-- 9. Also assign org_management + workspace_management permissions to
--    platform_super_admin role and GRC roles if not already done
--    (super_admin should inherit everything at all scopes)
-- ═══════════════════════════════════════════════════════════════════════

-- (Already handled in earlier migration 20260314_create-auth-orgs-workspaces-v2.sql)
