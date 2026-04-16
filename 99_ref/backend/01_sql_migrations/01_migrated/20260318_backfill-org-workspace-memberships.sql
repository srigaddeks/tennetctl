-- Migration: Backfill org and workspace membership rows
--
-- Prior to the create_org / create_workspace fix, the backend wrote users
-- into org/workspace system groups (18_lnk_group_memberships) but never
-- wrote corresponding rows into:
--   31_lnk_org_memberships      (used by list_orgs_for_user)
--   36_lnk_workspace_memberships (used by list_workspaces_for_user)
--
-- This migration backfills those rows for all existing users who are in
-- org_admin/org_member/org_viewer groups but missing from the membership tables.
-- Membership type is derived from the role assigned to their system group.

-- ── 1. Backfill 31_lnk_org_memberships ──────────────────────────────────────

INSERT INTO "03_auth_manage"."31_lnk_org_memberships" (
    id, org_id, user_id, membership_type, membership_status,
    effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(),
    g.scope_org_id,
    gm.user_id,
    CASE r.code
        WHEN 'org_admin'  THEN 'owner'
        WHEN 'org_member' THEN 'member'
        WHEN 'org_viewer' THEN 'viewer'
    END AS membership_type,
    'active',
    NOW(), NULL,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."18_lnk_group_memberships" gm
JOIN "03_auth_manage"."17_fct_user_groups" g ON g.id = gm.group_id
JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra
    ON gra.group_id = g.id AND gra.is_deleted = FALSE
JOIN "03_auth_manage"."16_fct_roles" r ON r.id = gra.role_id
WHERE g.is_system = TRUE
  AND g.scope_org_id IS NOT NULL
  AND gm.is_deleted = FALSE
  AND r.code IN ('org_admin', 'org_member', 'org_viewer')
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."31_lnk_org_memberships" m
      WHERE m.org_id = g.scope_org_id
        AND m.user_id = gm.user_id
        AND m.is_deleted = FALSE
  )
ON CONFLICT (org_id, user_id) WHERE is_deleted = FALSE DO NOTHING;


-- ── 2. Backfill 36_lnk_workspace_memberships ────────────────────────────────

INSERT INTO "03_auth_manage"."36_lnk_workspace_memberships" (
    id, workspace_id, user_id, membership_type, membership_status,
    effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(),
    g.scope_workspace_id,
    gm.user_id,
    CASE r.code
        WHEN 'workspace_admin'       THEN 'owner'
        WHEN 'workspace_contributor' THEN 'contributor'
        WHEN 'workspace_viewer'      THEN 'viewer'
    END AS membership_type,
    'active',
    NOW(), NULL,
    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."18_lnk_group_memberships" gm
JOIN "03_auth_manage"."17_fct_user_groups" g ON g.id = gm.group_id
JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra
    ON gra.group_id = g.id AND gra.is_deleted = FALSE
JOIN "03_auth_manage"."16_fct_roles" r ON r.id = gra.role_id
WHERE g.is_system = TRUE
  AND g.scope_workspace_id IS NOT NULL
  AND gm.is_deleted = FALSE
  AND r.code IN ('workspace_admin', 'workspace_contributor', 'workspace_viewer')
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."36_lnk_workspace_memberships" m
      WHERE m.workspace_id = g.scope_workspace_id
        AND m.user_id = gm.user_id
        AND m.is_deleted = FALSE
  )
ON CONFLICT (workspace_id, user_id) WHERE is_deleted = FALSE DO NOTHING;
