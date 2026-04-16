-- ===========================================================================
-- Migration: Grant org admins write access to org-scoped documents
-- Date: 2026-03-24
-- ===========================================================================

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id,
     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
     created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
    NOW(), NOW(), NULL, NULL, NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
JOIN "03_auth_manage"."15_dim_feature_permissions" fp
  ON fp.code IN ('docs.create', 'docs.update', 'docs.delete')
WHERE r.code = 'org_admin'
  AND r.tenant_key = 'default'
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
    SELECT 1
    FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
    WHERE lnk.role_id = r.id
      AND lnk.feature_permission_id = fp.id
  );
