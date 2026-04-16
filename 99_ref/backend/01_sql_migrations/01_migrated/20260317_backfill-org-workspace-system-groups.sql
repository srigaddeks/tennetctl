-- ─────────────────────────────────────────────────────────────────────────
-- Backfill: Create system groups for existing orgs and workspaces,
-- and assign existing members to the correct scoped groups.
--
-- This is a one-time backfill. Going forward, the backend services
-- auto-provision groups on create and auto-assign on member add.
-- ─────────────────────────────────────────────────────────────────────────

-- ═══════════════════════════════════════════════════════════════════════
-- 1. CREATE ORG SYSTEM GROUPS for every existing org
-- ═══════════════════════════════════════════════════════════════════════

-- For each org, create 3 system groups: org_admins, org_members, org_viewers
DO $$
DECLARE
    rec RECORD;
    v_org_prefix TEXT;
    v_group_id UUID;
    v_actual_group_id UUID;
    v_role_id UUID;
    v_group_defs TEXT[][] := ARRAY[
        ARRAY['org_admins', 'Org Admins', 'org_admin'],
        ARRAY['org_members', 'Org Members', 'org_member'],
        ARRAY['org_viewers', 'Org Viewers', 'org_viewer']
    ];
    v_def TEXT[];
BEGIN
    FOR rec IN
        SELECT id, tenant_key FROM "03_auth_manage"."29_fct_orgs" WHERE is_deleted = FALSE
    LOOP
        v_org_prefix := LEFT(REPLACE(rec.id::text, '-', ''), 8);

        FOREACH v_def SLICE 1 IN ARRAY v_group_defs
        LOOP
            -- Check if this system group already exists for this org
            SELECT id INTO v_actual_group_id
            FROM "03_auth_manage"."17_fct_user_groups"
            WHERE code = v_org_prefix || '_' || v_def[1]
              AND scope_org_id = rec.id
              AND is_deleted = FALSE;

            IF v_actual_group_id IS NULL THEN
                v_group_id := gen_random_uuid();
                INSERT INTO "03_auth_manage"."17_fct_user_groups" (
                    id, tenant_key, role_level_code, code, name, description,
                    parent_group_id, scope_org_id, scope_workspace_id,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
                VALUES (
                    v_group_id, rec.tenant_key, 'org',
                    v_org_prefix || '_' || v_def[1],
                    v_def[2],
                    'System group for ' || LOWER(v_def[2]) || ' of this organization',
                    NULL, rec.id, NULL,
                    TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
                    NOW(), NOW(), NULL, NULL, NULL, NULL
                )
                ON CONFLICT (tenant_key, role_level_code, code) DO NOTHING;

                SELECT id INTO v_actual_group_id
                FROM "03_auth_manage"."17_fct_user_groups"
                WHERE code = v_org_prefix || '_' || v_def[1]
                  AND scope_org_id = rec.id
                  AND is_deleted = FALSE;
            END IF;

            IF v_actual_group_id IS NOT NULL THEN
                -- Assign the role to this group if not already assigned
                SELECT id INTO v_role_id
                FROM "03_auth_manage"."16_fct_roles"
                WHERE code = v_def[3] AND is_deleted = FALSE
                LIMIT 1;

                IF v_role_id IS NOT NULL THEN
                    INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (
                        id, group_id, role_id, assignment_status, effective_from, effective_to,
                        is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                        created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                    )
                    SELECT gen_random_uuid(), v_actual_group_id, v_role_id, 'active', NOW(), NULL,
                           TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
                           NOW(), NOW(), NULL, NULL, NULL, NULL
                    WHERE NOT EXISTS (
                        SELECT 1 FROM "03_auth_manage"."19_lnk_group_role_assignments"
                        WHERE group_id = v_actual_group_id AND role_id = v_role_id AND is_deleted = FALSE
                    );
                END IF;
            END IF;
        END LOOP;
    END LOOP;
END $$;


-- ═══════════════════════════════════════════════════════════════════════
-- 2. CREATE WORKSPACE SYSTEM GROUPS for every existing workspace
-- ═══════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    rec RECORD;
    v_ws_prefix TEXT;
    v_group_id UUID;
    v_actual_group_id UUID;
    v_role_id UUID;
    v_group_defs TEXT[][] := ARRAY[
        ARRAY['ws_admins', 'Workspace Admins', 'workspace_admin'],
        ARRAY['ws_contributors', 'Workspace Contributors', 'workspace_contributor'],
        ARRAY['ws_viewers', 'Workspace Viewers', 'workspace_viewer']
    ];
    v_def TEXT[];
BEGIN
    FOR rec IN
        SELECT id, org_id FROM "03_auth_manage"."34_fct_workspaces" WHERE is_deleted = FALSE
    LOOP
        v_ws_prefix := LEFT(REPLACE(rec.id::text, '-', ''), 8);

        FOREACH v_def SLICE 1 IN ARRAY v_group_defs
        LOOP
            SELECT id INTO v_actual_group_id
            FROM "03_auth_manage"."17_fct_user_groups"
            WHERE code = v_ws_prefix || '_' || v_def[1]
              AND scope_workspace_id = rec.id
              AND is_deleted = FALSE;

            IF v_actual_group_id IS NULL THEN
                v_group_id := gen_random_uuid();
                INSERT INTO "03_auth_manage"."17_fct_user_groups" (
                    id, tenant_key, role_level_code, code, name, description,
                    parent_group_id, scope_org_id, scope_workspace_id,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
                VALUES (
                    v_group_id, 'default', 'workspace',
                    v_ws_prefix || '_' || v_def[1],
                    v_def[2],
                    'System group for ' || LOWER(v_def[2]) || ' of this workspace',
                    NULL, rec.org_id, rec.id,
                    TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
                    NOW(), NOW(), NULL, NULL, NULL, NULL
                )
                ON CONFLICT (tenant_key, role_level_code, code) DO NOTHING;

                SELECT id INTO v_actual_group_id
                FROM "03_auth_manage"."17_fct_user_groups"
                WHERE code = v_ws_prefix || '_' || v_def[1]
                  AND scope_workspace_id = rec.id
                  AND is_deleted = FALSE;
            END IF;

            IF v_actual_group_id IS NOT NULL THEN
                SELECT id INTO v_role_id
                FROM "03_auth_manage"."16_fct_roles"
                WHERE code = v_def[3] AND is_deleted = FALSE
                LIMIT 1;

                IF v_role_id IS NOT NULL THEN
                    INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (
                        id, group_id, role_id, assignment_status, effective_from, effective_to,
                        is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                        created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                    )
                    SELECT gen_random_uuid(), v_actual_group_id, v_role_id, 'active', NOW(), NULL,
                           TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
                           NOW(), NOW(), NULL, NULL, NULL, NULL
                    WHERE NOT EXISTS (
                        SELECT 1 FROM "03_auth_manage"."19_lnk_group_role_assignments"
                        WHERE group_id = v_actual_group_id AND role_id = v_role_id AND is_deleted = FALSE
                    );
                END IF;
            END IF;
        END LOOP;
    END LOOP;
END $$;


-- ═══════════════════════════════════════════════════════════════════════
-- 3. ASSIGN EXISTING ORG MEMBERS to their scoped groups
--    membership_type mapping:
--      owner/admin → org_admin group
--      member      → org_member group
--      viewer/billing → org_viewer group
-- ═══════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    mem RECORD;
    v_role_code TEXT;
    v_group_id UUID;
BEGIN
    FOR mem IN
        SELECT om.user_id, om.org_id, om.membership_type
        FROM "03_auth_manage"."31_lnk_org_memberships" om
        WHERE om.is_deleted = FALSE AND om.is_active = TRUE
    LOOP
        -- Map membership_type to role_code
        v_role_code := CASE mem.membership_type
            WHEN 'owner' THEN 'org_admin'
            WHEN 'admin' THEN 'org_admin'
            WHEN 'member' THEN 'org_member'
            WHEN 'viewer' THEN 'org_viewer'
            WHEN 'billing' THEN 'org_viewer'
            ELSE NULL
        END;

        IF v_role_code IS NULL THEN
            CONTINUE;
        END IF;

        -- Find the system group for this org + role
        SELECT g.id INTO v_group_id
        FROM "03_auth_manage"."17_fct_user_groups" g
        JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra ON gra.group_id = g.id AND gra.is_deleted = FALSE
        JOIN "03_auth_manage"."16_fct_roles" r ON r.id = gra.role_id AND r.is_deleted = FALSE
        WHERE g.scope_org_id = mem.org_id
          AND g.is_system = TRUE AND g.is_deleted = FALSE
          AND r.code = v_role_code
        LIMIT 1;

        IF v_group_id IS NOT NULL THEN
            INSERT INTO "03_auth_manage"."18_lnk_group_memberships" (
                id, group_id, user_id, membership_status, effective_from, effective_to,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES (
                gen_random_uuid(), v_group_id, mem.user_id, 'active', NOW(), NULL,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                NOW(), NOW(), NULL, NULL, NULL, NULL
            )
            ON CONFLICT (group_id, user_id) DO NOTHING;
        END IF;
    END LOOP;
END $$;


-- ═══════════════════════════════════════════════════════════════════════
-- 4. ASSIGN EXISTING WORKSPACE MEMBERS to their scoped groups
--    membership_type mapping:
--      owner/admin      → workspace_admin group
--      contributor      → workspace_contributor group
--      viewer/readonly  → workspace_viewer group
-- ═══════════════════════════════════════════════════════════════════════

DO $$
DECLARE
    mem RECORD;
    v_role_code TEXT;
    v_group_id UUID;
BEGIN
    FOR mem IN
        SELECT wm.user_id, wm.workspace_id, wm.membership_type
        FROM "03_auth_manage"."36_lnk_workspace_memberships" wm
        WHERE wm.is_deleted = FALSE AND wm.is_active = TRUE
    LOOP
        v_role_code := CASE mem.membership_type
            WHEN 'owner' THEN 'workspace_admin'
            WHEN 'admin' THEN 'workspace_admin'
            WHEN 'contributor' THEN 'workspace_contributor'
            WHEN 'viewer' THEN 'workspace_viewer'
            WHEN 'readonly' THEN 'workspace_viewer'
            ELSE NULL
        END;

        IF v_role_code IS NULL THEN
            CONTINUE;
        END IF;

        SELECT g.id INTO v_group_id
        FROM "03_auth_manage"."17_fct_user_groups" g
        JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra ON gra.group_id = g.id AND gra.is_deleted = FALSE
        JOIN "03_auth_manage"."16_fct_roles" r ON r.id = gra.role_id AND r.is_deleted = FALSE
        WHERE g.scope_workspace_id = mem.workspace_id
          AND g.is_system = TRUE AND g.is_deleted = FALSE
          AND r.code = v_role_code
        LIMIT 1;

        IF v_group_id IS NOT NULL THEN
            INSERT INTO "03_auth_manage"."18_lnk_group_memberships" (
                id, group_id, user_id, membership_status, effective_from, effective_to,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES (
                gen_random_uuid(), v_group_id, mem.user_id, 'active', NOW(), NULL,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                NOW(), NOW(), NULL, NULL, NULL, NULL
            )
            ON CONFLICT (group_id, user_id) DO NOTHING;
        END IF;
    END LOOP;
END $$;
