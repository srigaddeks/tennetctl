-- Migration: Seed default_users group, basic_user role, and onboarding permissions
--
-- Every new user is automatically added to the 'default_users' group on registration.
-- This group holds the 'basic_user' platform role which grants the minimum permissions
-- needed to complete onboarding (create one org + workspaces).
--
-- Future: replace with quota/license enforcement per plan tier.

-- ── 1. Seed basic_user role (platform scope) ─────────────────────────────────

INSERT INTO "03_auth_manage"."16_fct_roles" (
    id, tenant_key, role_level_code, code, name, description,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    '00000000-0000-0000-0000-000000002001', 'default', 'platform', 'basic_user',
    'Basic User', 'Default role granted to every registered user. Allows onboarding setup.',
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00',
    NULL, NULL, NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."16_fct_roles" WHERE code = 'basic_user' AND tenant_key = 'default'
);

-- ── 2. Grant onboarding permissions to basic_user role ───────────────────────

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00',
    NULL, NULL, NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'basic_user'
  AND r.tenant_key = 'default'
  AND fp.code IN (
      'org_management.create',
      'org_management.view',
      'org_management.update',
      'org_management.assign',
      'org_management.revoke',
      'workspace_management.create',
      'workspace_management.view',
      'workspace_management.update',
      'workspace_management.assign',
      'workspace_management.revoke'
  )
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp2
      WHERE rfp2.role_id = r.id
        AND rfp2.feature_permission_id = fp.id
        AND rfp2.is_deleted = FALSE
  );

-- ── 3. Seed default_users group (platform scope, no org/workspace scope) ─────

INSERT INTO "03_auth_manage"."17_fct_user_groups" (
    id, tenant_key, role_level_code, code, name, description,
    scope_org_id, scope_workspace_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    '00000000-0000-0000-0000-000000003001', 'default', 'platform', 'default_users',
    'Default Users', 'Every registered user is automatically a member of this group.',
    NULL, NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00',
    NULL, NULL, NULL, NULL
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."17_fct_user_groups" WHERE code = 'default_users' AND tenant_key = 'default'
);

-- ── 4. Assign basic_user role to default_users group ─────────────────────────

INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments" (
    id, group_id, role_id,
    assignment_status, effective_from, effective_to,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
)
SELECT
    '00000000-0000-0000-0000-000000004001',
    g.id,
    r.id,
    'active', TIMESTAMP '2026-03-14 00:00:00', NULL,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00',
    NULL, NULL, NULL, NULL
FROM "03_auth_manage"."17_fct_user_groups" g
CROSS JOIN "03_auth_manage"."16_fct_roles" r
WHERE g.code = 'default_users' AND g.tenant_key = 'default'
  AND r.code = 'basic_user'   AND r.tenant_key = 'default'
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."19_lnk_group_role_assignments" gra2
      WHERE gra2.group_id = g.id AND gra2.role_id = r.id AND gra2.is_deleted = FALSE
  );
