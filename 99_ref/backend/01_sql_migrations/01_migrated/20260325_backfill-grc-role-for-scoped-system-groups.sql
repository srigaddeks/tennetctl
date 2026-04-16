-- ============================================================================
-- Migration: Backfill grc_compliance_lead onto scoped system groups
-- Date: 2026-03-25
--
-- Why:
-- - 20260320_seed-grc-permissions.sql granted grc_compliance_lead to all groups
--   that existed at that time.
-- - Org/workspace system groups created after that migration did not inherit the
--   same GRC role automatically, so newly invited users in newer orgs/workspaces
--   could miss the expected risk/task/comment access.
--
-- This migration makes the existing data consistent by assigning the
-- grc_compliance_lead role to all active org/workspace system groups.
-- Future group provisioning is handled in backend/03_auth_manage/_scoped_group_provisioning.py.
-- ============================================================================

INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (
    id,
    group_id,
    role_id,
    assignment_status,
    effective_from,
    effective_to,
    is_active,
    is_disabled,
    is_deleted,
    is_test,
    is_system,
    is_locked,
    created_at,
    updated_at,
    created_by,
    updated_by,
    deleted_at,
    deleted_by
)
SELECT
    gen_random_uuid(),
    g.id,
    r.id,
    'active',
    NOW(),
    NULL,
    TRUE,
    FALSE,
    FALSE,
    FALSE,
    TRUE,
    TRUE,
    NOW(),
    NOW(),
    NULL,
    NULL,
    NULL,
    NULL
FROM "03_auth_manage"."17_fct_user_groups" g
JOIN "03_auth_manage"."16_fct_roles" r
  ON r.code = 'grc_compliance_lead'
 AND r.is_deleted = FALSE
WHERE g.is_system = TRUE
  AND g.is_active = TRUE
  AND g.is_deleted = FALSE
  AND g.role_level_code IN ('org', 'workspace')
  AND (
      g.scope_org_id IS NOT NULL
      OR g.scope_workspace_id IS NOT NULL
  )
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."19_lnk_group_role_assignments" gra
      WHERE gra.group_id = g.id
        AND gra.role_id = r.id
        AND gra.is_deleted = FALSE
  );
