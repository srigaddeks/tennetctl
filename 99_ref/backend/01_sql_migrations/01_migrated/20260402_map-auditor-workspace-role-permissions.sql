-- Map auditor workspace feature permissions to the intended platform roles.
-- This keeps rollout narrow:
--   - auditor roles get the auditor workspace experience
--   - GRC lead / SME get evidence-review and membership-governance permissions
--   - super-admin roles get full visibility for rollout and support

-- Super-admin roles: full access to the auditor workspace capability set
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
JOIN "03_auth_manage"."15_dim_feature_permissions" fp
  ON fp.code IN (
      'audit_workspace_auditor_portfolio.view',
      'audit_workspace_engagement_membership.view',
      'audit_workspace_engagement_membership.update',
      'audit_workspace_control_access.view',
      'audit_workspace_evidence_requests.view',
      'audit_workspace_evidence_requests.create',
      'audit_workspace_evidence_requests.approve',
      'audit_workspace_evidence_requests.revoke',
      'audit_workspace_auditor_findings.view',
      'audit_workspace_auditor_findings.create',
      'audit_workspace_auditor_findings.update',
      'audit_workspace_auditor_tasks.view',
      'audit_workspace_auditor_tasks.create',
      'audit_workspace_auditor_tasks.assign',
      'audit_workspace_auditor_tasks.update'
  )
WHERE r.code IN ('platform_super_admin', 'super_admin')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
      WHERE lnk.role_id = r.id
        AND lnk.feature_permission_id = fp.id
  );

-- Auditor roles: end-to-end auditor workspace usage within engagement scope
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
JOIN "03_auth_manage"."15_dim_feature_permissions" fp
  ON fp.code IN (
      'audit_workspace_auditor_portfolio.view',
      'audit_workspace_engagement_membership.view',
      'audit_workspace_control_access.view',
      'audit_workspace_evidence_requests.view',
      'audit_workspace_evidence_requests.create',
      'audit_workspace_auditor_findings.view',
      'audit_workspace_auditor_findings.create',
      'audit_workspace_auditor_findings.update',
      'audit_workspace_auditor_tasks.view',
      'audit_workspace_auditor_tasks.create',
      'audit_workspace_auditor_tasks.assign',
      'audit_workspace_auditor_tasks.update'
  )
WHERE r.code IN ('grc_lead_auditor', 'grc_staff_auditor')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
      WHERE lnk.role_id = r.id
        AND lnk.feature_permission_id = fp.id
  );

-- GRC governance roles: manage membership-backed access and review evidence requests
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
JOIN "03_auth_manage"."15_dim_feature_permissions" fp
  ON fp.code IN (
      'audit_workspace_engagement_membership.view',
      'audit_workspace_engagement_membership.update',
      'audit_workspace_control_access.view',
      'audit_workspace_evidence_requests.view',
      'audit_workspace_evidence_requests.approve',
      'audit_workspace_evidence_requests.revoke'
  )
WHERE r.code = 'grc_lead'
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
      WHERE lnk.role_id = r.id
        AND lnk.feature_permission_id = fp.id
  );

INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions" (
    id, role_id, feature_permission_id,
    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
    created_at, updated_at, created_by, updated_by
)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, FALSE, FALSE, TRUE, FALSE,
    NOW(), NOW(), NULL, NULL
FROM "03_auth_manage"."16_fct_roles" r
JOIN "03_auth_manage"."15_dim_feature_permissions" fp
  ON fp.code IN (
      'audit_workspace_engagement_membership.view',
      'audit_workspace_control_access.view',
      'audit_workspace_evidence_requests.view',
      'audit_workspace_evidence_requests.approve'
  )
WHERE r.code = 'grc_sme'
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM "03_auth_manage"."20_lnk_role_feature_permissions" lnk
      WHERE lnk.role_id = r.id
        AND lnk.feature_permission_id = fp.id
  );
