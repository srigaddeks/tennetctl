-- Migration: Fix basic_user role permissions
--
-- basic_user was seeded with full org_management.* and workspace_management.*
-- at platform scope, causing every registered user to see all orgs as if they
-- were super admins.
--
-- Correct model:
--   basic_user  → no org/workspace management permissions
--   org_admin   → full org_management.* + workspace_management.* (scoped to their org)
--   org_member  → org_management.view + workspace_management.* (scoped to their org)
--
-- Org creation (onboarding) does NOT require a permission check —
-- any authenticated user may create their first org. The backend service
-- has been updated to remove that check accordingly.

DELETE FROM "03_auth_manage"."20_lnk_role_feature_permissions"
WHERE role_id = (
    SELECT id FROM "03_auth_manage"."16_fct_roles"
    WHERE code = 'basic_user' AND tenant_key = 'default'
)
AND feature_permission_id IN (
    SELECT id FROM "03_auth_manage"."15_dim_feature_permissions"
    WHERE code IN (
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
);
