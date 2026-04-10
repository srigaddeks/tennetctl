-- =============================================================================
-- Migration:   20260409_014_iam_default_roles.sql
-- Module:      03_iam
-- Sub-feature: 00_bootstrap (RBAC default roles)
-- Sequence:    014
-- Depends on:  011 (iam_rbac — fct_org_roles, fct_workspace_roles,
--              fct_permissions, lnk_*_role_permissions must all exist)
-- Description: Seed helper functions for creating default system roles.
--              org_roles and workspace_roles require a concrete org_id /
--              workspace_id FK — they cannot be seeded as global templates.
--              Instead this migration provides two SQL functions:
--
--                "03_iam".seed_default_org_roles(p_org_id, p_actor_id)
--                "03_iam".seed_default_workspace_roles(p_org_id, p_workspace_id, p_actor_id)
--
--              Called by the application when an org or workspace is created
--              (orgs/service.py and workspaces/service.py) to stamp the three
--              system roles and their permission grants in one atomic call.
--
--              Default org roles  : org_admin, org_member, org_viewer
--              Default ws  roles  : workspace_admin, workspace_member, workspace_viewer
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- seed_default_org_roles
-- Creates org_admin / org_member / org_viewer roles for p_org_id and links
-- permissions from the shared 10_fct_permissions catalog.
--
-- Permissions granted:
--   org_admin   : orgs:read, orgs:write, orgs:admin,
--                 users:read, users:write, users:admin,
--                 groups:read, groups:write,
--                 rbac:admin,
--                 feature_flags:read, feature_flags:write
--   org_member  : orgs:read, users:read, groups:read, feature_flags:read
--   org_viewer  : orgs:read, users:read
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION "03_iam".seed_default_org_roles(
    p_org_id    VARCHAR(36),
    p_actor_id  VARCHAR(36)
) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    v_cat_system SMALLINT;
    v_cat_support SMALLINT;
    v_role_admin_id   VARCHAR(36);
    v_role_member_id  VARCHAR(36);
    v_role_viewer_id  VARCHAR(36);
    v_perm RECORD;
BEGIN
    SELECT id INTO v_cat_system  FROM "03_iam"."06_dim_categories"
     WHERE category_type = 'role' AND code = 'system';
    SELECT id INTO v_cat_support FROM "03_iam"."06_dim_categories"
     WHERE category_type = 'role' AND code = 'support';

    -- Generate UUIDs using gen_random_uuid (UUID4 for DB-internal use)
    v_role_admin_id  := gen_random_uuid()::text;
    v_role_member_id := gen_random_uuid()::text;
    v_role_viewer_id := gen_random_uuid()::text;

    -- Insert org_admin
    INSERT INTO "03_iam"."10_fct_org_roles"
        (id, org_id, code, name, category_id, is_system, is_active,
         created_by, updated_by, created_at, updated_at)
    VALUES
        (v_role_admin_id,  p_org_id, 'org_admin',  'Organization Admin',  v_cat_system,  true, true,
         p_actor_id, p_actor_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (v_role_member_id, p_org_id, 'org_member', 'Organization Member', v_cat_support, true, true,
         p_actor_id, p_actor_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (v_role_viewer_id, p_org_id, 'org_viewer', 'Organization Viewer', v_cat_support, true, true,
         p_actor_id, p_actor_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (org_id, code) DO NOTHING;

    -- Re-fetch actual IDs (handles ON CONFLICT DO NOTHING race)
    SELECT id INTO v_role_admin_id  FROM "03_iam"."10_fct_org_roles"
     WHERE org_id = p_org_id AND code = 'org_admin';
    SELECT id INTO v_role_member_id FROM "03_iam"."10_fct_org_roles"
     WHERE org_id = p_org_id AND code = 'org_member';
    SELECT id INTO v_role_viewer_id FROM "03_iam"."10_fct_org_roles"
     WHERE org_id = p_org_id AND code = 'org_viewer';

    -- Grant permissions to org_admin
    FOR v_perm IN
        SELECT id FROM "03_iam"."10_fct_permissions"
         WHERE (resource, action) IN (
             ('orgs',          'read'),
             ('orgs',          'write'),
             ('orgs',          'admin'),
             ('users',         'read'),
             ('users',         'write'),
             ('users',         'admin'),
             ('groups',        'read'),
             ('groups',        'write'),
             ('rbac',          'admin'),
             ('feature_flags', 'read'),
             ('feature_flags', 'write')
         )
    LOOP
        INSERT INTO "03_iam"."40_lnk_org_role_permissions"
            (id, org_role_id, permission_id, created_at)
        VALUES (gen_random_uuid()::text, v_role_admin_id, v_perm.id, CURRENT_TIMESTAMP)
        ON CONFLICT (org_role_id, permission_id) DO NOTHING;
    END LOOP;

    -- Grant permissions to org_member
    FOR v_perm IN
        SELECT id FROM "03_iam"."10_fct_permissions"
         WHERE (resource, action) IN (
             ('orgs',          'read'),
             ('users',         'read'),
             ('groups',        'read'),
             ('feature_flags', 'read')
         )
    LOOP
        INSERT INTO "03_iam"."40_lnk_org_role_permissions"
            (id, org_role_id, permission_id, created_at)
        VALUES (gen_random_uuid()::text, v_role_member_id, v_perm.id, CURRENT_TIMESTAMP)
        ON CONFLICT (org_role_id, permission_id) DO NOTHING;
    END LOOP;

    -- Grant permissions to org_viewer
    FOR v_perm IN
        SELECT id FROM "03_iam"."10_fct_permissions"
         WHERE (resource, action) IN (
             ('orgs',  'read'),
             ('users', 'read')
         )
    LOOP
        INSERT INTO "03_iam"."40_lnk_org_role_permissions"
            (id, org_role_id, permission_id, created_at)
        VALUES (gen_random_uuid()::text, v_role_viewer_id, v_perm.id, CURRENT_TIMESTAMP)
        ON CONFLICT (org_role_id, permission_id) DO NOTHING;
    END LOOP;

END;
$$;

COMMENT ON FUNCTION "03_iam".seed_default_org_roles(VARCHAR, VARCHAR) IS
    'Seeds org_admin / org_member / org_viewer system roles for p_org_id '
    'and links them to the appropriate permissions. Idempotent — safe to call '
    'multiple times (ON CONFLICT DO NOTHING on all inserts). '
    'Called by orgs/service.py:create_org.';

GRANT EXECUTE ON FUNCTION "03_iam".seed_default_org_roles(VARCHAR, VARCHAR)
    TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- seed_default_workspace_roles
-- Creates workspace_admin / workspace_member / workspace_viewer for p_workspace_id
-- and links permissions.
--
-- Permissions granted:
--   workspace_admin  : groups:read, groups:write, feature_flags:read, feature_flags:write,
--                      users:read, vault.secrets:read, vault.secrets:write
--   workspace_member : feature_flags:read, users:read, vault.secrets:read
--   workspace_viewer : users:read
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION "03_iam".seed_default_workspace_roles(
    p_org_id        VARCHAR(36),
    p_workspace_id  VARCHAR(36),
    p_actor_id      VARCHAR(36)
) RETURNS VOID LANGUAGE plpgsql AS $$
DECLARE
    v_cat_system  SMALLINT;
    v_cat_support SMALLINT;
    v_role_admin_id   VARCHAR(36);
    v_role_member_id  VARCHAR(36);
    v_role_viewer_id  VARCHAR(36);
    v_perm RECORD;
BEGIN
    SELECT id INTO v_cat_system  FROM "03_iam"."06_dim_categories"
     WHERE category_type = 'role' AND code = 'system';
    SELECT id INTO v_cat_support FROM "03_iam"."06_dim_categories"
     WHERE category_type = 'role' AND code = 'support';

    v_role_admin_id  := gen_random_uuid()::text;
    v_role_member_id := gen_random_uuid()::text;
    v_role_viewer_id := gen_random_uuid()::text;

    -- Insert workspace_admin / workspace_member / workspace_viewer
    INSERT INTO "03_iam"."10_fct_workspace_roles"
        (id, org_id, workspace_id, code, name, category_id, is_system, is_active,
         created_by, updated_by, created_at, updated_at)
    VALUES
        (v_role_admin_id,  p_org_id, p_workspace_id,
         'workspace_admin',  'Workspace Admin',  v_cat_system,  true, true,
         p_actor_id, p_actor_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (v_role_member_id, p_org_id, p_workspace_id,
         'workspace_member', 'Workspace Member', v_cat_support, true, true,
         p_actor_id, p_actor_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        (v_role_viewer_id, p_org_id, p_workspace_id,
         'workspace_viewer', 'Workspace Viewer', v_cat_support, true, true,
         p_actor_id, p_actor_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ON CONFLICT (workspace_id, code) DO NOTHING;

    -- Re-fetch actual IDs
    SELECT id INTO v_role_admin_id  FROM "03_iam"."10_fct_workspace_roles"
     WHERE workspace_id = p_workspace_id AND code = 'workspace_admin';
    SELECT id INTO v_role_member_id FROM "03_iam"."10_fct_workspace_roles"
     WHERE workspace_id = p_workspace_id AND code = 'workspace_member';
    SELECT id INTO v_role_viewer_id FROM "03_iam"."10_fct_workspace_roles"
     WHERE workspace_id = p_workspace_id AND code = 'workspace_viewer';

    -- Grant permissions to workspace_admin
    FOR v_perm IN
        SELECT id FROM "03_iam"."10_fct_permissions"
         WHERE (resource, action) IN (
             ('groups',         'read'),
             ('groups',         'write'),
             ('feature_flags',  'read'),
             ('feature_flags',  'write'),
             ('users',          'read'),
             ('vault.secrets',  'read'),
             ('vault.secrets',  'write')
         )
    LOOP
        INSERT INTO "03_iam"."40_lnk_workspace_role_permissions"
            (id, workspace_role_id, permission_id, created_at)
        VALUES (gen_random_uuid()::text, v_role_admin_id, v_perm.id, CURRENT_TIMESTAMP)
        ON CONFLICT (workspace_role_id, permission_id) DO NOTHING;
    END LOOP;

    -- Grant permissions to workspace_member
    FOR v_perm IN
        SELECT id FROM "03_iam"."10_fct_permissions"
         WHERE (resource, action) IN (
             ('feature_flags', 'read'),
             ('users',         'read'),
             ('vault.secrets', 'read')
         )
    LOOP
        INSERT INTO "03_iam"."40_lnk_workspace_role_permissions"
            (id, workspace_role_id, permission_id, created_at)
        VALUES (gen_random_uuid()::text, v_role_member_id, v_perm.id, CURRENT_TIMESTAMP)
        ON CONFLICT (workspace_role_id, permission_id) DO NOTHING;
    END LOOP;

    -- Grant permissions to workspace_viewer
    FOR v_perm IN
        SELECT id FROM "03_iam"."10_fct_permissions"
         WHERE (resource, action) IN (
             ('users', 'read')
         )
    LOOP
        INSERT INTO "03_iam"."40_lnk_workspace_role_permissions"
            (id, workspace_role_id, permission_id, created_at)
        VALUES (gen_random_uuid()::text, v_role_viewer_id, v_perm.id, CURRENT_TIMESTAMP)
        ON CONFLICT (workspace_role_id, permission_id) DO NOTHING;
    END LOOP;

END;
$$;

COMMENT ON FUNCTION "03_iam".seed_default_workspace_roles(VARCHAR, VARCHAR, VARCHAR) IS
    'Seeds workspace_admin / workspace_member / workspace_viewer system roles '
    'for p_workspace_id and links them to the appropriate permissions. '
    'Idempotent — safe to call multiple times. '
    'Called by workspaces/service.py:create_workspace.';

GRANT EXECUTE ON FUNCTION "03_iam".seed_default_workspace_roles(VARCHAR, VARCHAR, VARCHAR)
    TO tennetctl_write;


-- DOWN =======================================================================

DROP FUNCTION IF EXISTS "03_iam".seed_default_workspace_roles(VARCHAR, VARCHAR, VARCHAR);
DROP FUNCTION IF EXISTS "03_iam".seed_default_org_roles(VARCHAR, VARCHAR);
