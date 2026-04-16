-- =============================================================================
-- Migration: 20260401_create-grc-role-assignments.sql
-- Module:    03_auth_manage
-- Description: Org-level GRC role assignment table with optional access grants
--              for workspace/framework/engagement scoping. Replaces the per-
--              workspace grc_role_code column approach with proper org-level
--              identity. Backfills existing workspace-level assignments.
--
-- UUID ranges:
--   Feature flag:     00000000-0000-0000-0000-000000009000
--   Permissions:      00000000-0000-0000-0000-000000009001 – 9004
--   Role assignments: 00000000-0000-0000-0000-000000009010 – 9015
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Org-level GRC role assignments
--    One role per user per org. This is the user's GRC identity.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."47_lnk_grc_role_assignments" (
    id                  UUID  NOT NULL,
    org_id              UUID  NOT NULL,
    user_id             UUID  NOT NULL,
    grc_role_code       VARCHAR(50)  NOT NULL,
    assigned_by         UUID,
    assigned_at         TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at          TIMESTAMP,
    revoked_by          UUID,
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_47_lnk_grc_role_assignments PRIMARY KEY (id),
    CONSTRAINT fk_47_grc_ra_org
        FOREIGN KEY (org_id)  REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_47_grc_ra_user
        FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users" (id),
    CONSTRAINT chk_47_grc_ra_role_code CHECK (
        grc_role_code IN (
            'grc_lead', 'grc_sme', 'grc_engineer', 'grc_ciso',
            'grc_lead_auditor', 'grc_staff_auditor', 'grc_vendor'
        )
    )
);

COMMENT ON TABLE  "03_auth_manage"."47_lnk_grc_role_assignments"
    IS 'Org-level GRC role identity. One active role per user per org. Immutable rows — revoke by setting revoked_at.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".id
    IS 'UUID v7 PK for the assignment.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".org_id
    IS 'Org this GRC role belongs to. FK to 29_fct_orgs.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".user_id
    IS 'User who holds this GRC role. FK to 03_fct_users.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".grc_role_code
    IS 'GRC role code: grc_lead, grc_sme, grc_engineer, grc_ciso, grc_lead_auditor, grc_staff_auditor, grc_vendor.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".assigned_by
    IS 'UUID of actor who assigned this role.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".assigned_at
    IS 'Timestamp when the role was assigned.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".revoked_at
    IS 'NULL = active assignment. SET = revoked at this timestamp.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".revoked_by
    IS 'UUID of actor who revoked this role. NULL if still active.';
COMMENT ON COLUMN "03_auth_manage"."47_lnk_grc_role_assignments".created_at
    IS 'Row creation timestamp (UTC).';

-- One active role per user per org
CREATE UNIQUE INDEX IF NOT EXISTS uq_47_grc_ra_active
    ON "03_auth_manage"."47_lnk_grc_role_assignments" (org_id, user_id, grc_role_code)
    WHERE revoked_at IS NULL;
COMMENT ON INDEX "03_auth_manage".uq_47_grc_ra_active
    IS 'Enforce one active GRC role assignment per user per org per role code.';

-- Fast lookup by org
CREATE INDEX IF NOT EXISTS idx_47_grc_ra_org
    ON "03_auth_manage"."47_lnk_grc_role_assignments" (org_id)
    WHERE revoked_at IS NULL;
COMMENT ON INDEX "03_auth_manage".idx_47_grc_ra_org
    IS 'Fast team lookup by org for active assignments.';

-- Fast lookup by user
CREATE INDEX IF NOT EXISTS idx_47_grc_ra_user
    ON "03_auth_manage"."47_lnk_grc_role_assignments" (user_id)
    WHERE revoked_at IS NULL;
COMMENT ON INDEX "03_auth_manage".idx_47_grc_ra_user
    IS 'Fast permission check by user for active assignments.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. GRC access grants — optional scope narrowing
--    Grants a role-holder access to a specific workspace/framework/engagement.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."48_lnk_grc_access_grants" (
    id                          UUID  NOT NULL,
    grc_role_assignment_id      UUID  NOT NULL,
    scope_type                  VARCHAR(20)  NOT NULL,
    scope_id                    UUID  NOT NULL,
    granted_by                  UUID,
    granted_at                  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at                  TIMESTAMP,
    revoked_by                  UUID,
    created_at                  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_48_lnk_grc_access_grants PRIMARY KEY (id),
    CONSTRAINT fk_48_grc_ag_assignment
        FOREIGN KEY (grc_role_assignment_id)
        REFERENCES "03_auth_manage"."47_lnk_grc_role_assignments" (id),
    CONSTRAINT chk_48_grc_ag_scope_type CHECK (
        scope_type IN ('workspace', 'framework', 'engagement')
    )
);

COMMENT ON TABLE  "03_auth_manage"."48_lnk_grc_access_grants"
    IS 'Grants a GRC role-holder access to a specific workspace, framework deployment, or audit engagement. Immutable rows — revoke by setting revoked_at.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".id
    IS 'UUID v7 PK for the access grant.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".grc_role_assignment_id
    IS 'FK to 47_lnk_grc_role_assignments. The org-level role this grant extends.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".scope_type
    IS 'What this grant scopes to: workspace, framework, or engagement.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".scope_id
    IS 'UUID of the target workspace/framework_deployment/engagement.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".granted_by
    IS 'UUID of actor who created this grant.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".granted_at
    IS 'Timestamp when access was granted.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".revoked_at
    IS 'NULL = active grant. SET = revoked at this timestamp.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".revoked_by
    IS 'UUID of actor who revoked this grant. NULL if still active.';
COMMENT ON COLUMN "03_auth_manage"."48_lnk_grc_access_grants".created_at
    IS 'Row creation timestamp (UTC).';

-- One active grant per assignment per scope
CREATE UNIQUE INDEX IF NOT EXISTS uq_48_grc_ag_active
    ON "03_auth_manage"."48_lnk_grc_access_grants" (grc_role_assignment_id, scope_type, scope_id)
    WHERE revoked_at IS NULL;
COMMENT ON INDEX "03_auth_manage".uq_48_grc_ag_active
    IS 'Enforce one active grant per assignment per scope target.';

-- Fast lookup by assignment
CREATE INDEX IF NOT EXISTS idx_48_grc_ag_assignment
    ON "03_auth_manage"."48_lnk_grc_access_grants" (grc_role_assignment_id)
    WHERE revoked_at IS NULL;
COMMENT ON INDEX "03_auth_manage".idx_48_grc_ag_assignment
    IS 'Fast grant lookup by role assignment.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Read view: v_grc_team
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "03_auth_manage"."v_grc_team" AS
SELECT
    ra.id                   AS assignment_id,
    ra.org_id,
    ra.user_id,
    ra.grc_role_code,
    r.name                  AS role_name,
    r.description           AS role_description,
    email.property_value    AS email,
    dn.property_value       AS display_name,
    ra.assigned_by,
    ra.assigned_at,
    ra.revoked_at,
    ra.created_at,
    -- Access grant counts
    (SELECT COUNT(*) FROM "03_auth_manage"."48_lnk_grc_access_grants" g
     WHERE g.grc_role_assignment_id = ra.id AND g.revoked_at IS NULL)
        AS active_grant_count
FROM "03_auth_manage"."47_lnk_grc_role_assignments" ra
JOIN "03_auth_manage"."16_fct_roles" r
    ON r.code = ra.grc_role_code
    AND r.is_deleted = FALSE
    AND r.role_level_code = 'workspace'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" email
    ON email.user_id = ra.user_id AND email.property_key = 'email'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" dn
    ON dn.user_id = ra.user_id AND dn.property_key = 'display_name'
WHERE ra.revoked_at IS NULL;

COMMENT ON VIEW "03_auth_manage"."v_grc_team"
    IS 'Read view of active org-level GRC role assignments with resolved user info and access grant counts.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Backfill from existing grc_role_code on workspace memberships
--    Deduplicates to one role per user per org (takes the earliest assignment).
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_auth_manage"."47_lnk_grc_role_assignments"
    (id, org_id, user_id, grc_role_code, assigned_by, assigned_at, created_at)
SELECT DISTINCT ON (w.org_id, m.user_id, m.grc_role_code)
    gen_random_uuid(),
    w.org_id,
    m.user_id,
    m.grc_role_code,
    m.created_by,
    COALESCE(m.effective_from, m.created_at, CURRENT_TIMESTAMP),
    CURRENT_TIMESTAMP
FROM "03_auth_manage"."36_lnk_workspace_memberships" m
JOIN "03_auth_manage"."34_fct_workspaces" w ON w.id = m.workspace_id
WHERE m.grc_role_code IS NOT NULL
  AND m.is_active = TRUE
  AND m.is_deleted = FALSE
ORDER BY w.org_id, m.user_id, m.grc_role_code, m.effective_from ASC NULLS LAST
ON CONFLICT DO NOTHING;

-- Also create workspace access grants for each backfilled assignment
INSERT INTO "03_auth_manage"."48_lnk_grc_access_grants"
    (id, grc_role_assignment_id, scope_type, scope_id, granted_by, granted_at, created_at)
SELECT
    gen_random_uuid(),
    ra.id,
    'workspace',
    m.workspace_id,
    m.created_by,
    COALESCE(m.effective_from, m.created_at, CURRENT_TIMESTAMP),
    CURRENT_TIMESTAMP
FROM "03_auth_manage"."36_lnk_workspace_memberships" m
JOIN "03_auth_manage"."34_fct_workspaces" w ON w.id = m.workspace_id
JOIN "03_auth_manage"."47_lnk_grc_role_assignments" ra
    ON ra.org_id = w.org_id
    AND ra.user_id = m.user_id
    AND ra.grc_role_code = m.grc_role_code
    AND ra.revoked_at IS NULL
WHERE m.grc_role_code IS NOT NULL
  AND m.is_active = TRUE
  AND m.is_deleted = FALSE
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. Seed feature flag + permissions for GRC role management
-- ─────────────────────────────────────────────────────────────────────────────

-- Feature flag: grc_role_management
INSERT INTO "03_auth_manage"."14_dim_feature_flags" (
    id, code, name, description, feature_flag_category_code, access_mode, lifecycle_state, initial_audience,
    env_dev, env_staging, env_prod, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000009000', 'grc_role_management',
       'GRC Role Management',
       'Manage org-level GRC role assignments (lead, SME, auditor, vendor) and access grants.',
       'grc', 'permissioned', 'active', 'org_admin',
       TRUE, TRUE, TRUE,
       TIMESTAMP '2026-04-01 00:00:00', TIMESTAMP '2026-04-01 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."14_dim_feature_flags" WHERE code = 'grc_role_management');

-- Permissions: view, assign, revoke, manage
INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000009001', 'grc_role_management.view',
       'grc_role_management', 'view',
       'View GRC Team', 'View GRC role assignments and access grants for the org.',
       TIMESTAMP '2026-04-01 00:00:00', TIMESTAMP '2026-04-01 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.view');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000009002', 'grc_role_management.assign',
       'grc_role_management', 'assign',
       'Assign GRC Role', 'Assign a GRC role to a user at the org level.',
       TIMESTAMP '2026-04-01 00:00:00', TIMESTAMP '2026-04-01 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.assign');

INSERT INTO "03_auth_manage"."15_dim_feature_permissions" (
    id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at
)
SELECT '00000000-0000-0000-0000-000000009003', 'grc_role_management.revoke',
       'grc_role_management', 'revoke',
       'Revoke GRC Role', 'Revoke a GRC role assignment.',
       TIMESTAMP '2026-04-01 00:00:00', TIMESTAMP '2026-04-01 00:00:00'
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'grc_role_management.revoke');

-- Assign view permission to all GRC roles (everyone can see the team)
-- Assign assign/revoke to grc_lead only
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_deleted, created_at, updated_at)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code = 'grc_role_management.view'
  AND r.code IN ('grc_lead', 'grc_sme', 'grc_engineer', 'grc_ciso', 'grc_lead_auditor', 'grc_staff_auditor', 'grc_vendor', 'org_admin', 'workspace_admin', 'platform_super_admin', 'super_admin')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp
      WHERE rfp.role_id = r.id AND rfp.feature_permission_id = fp.id
  );

-- grc_lead gets assign + revoke
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_deleted, created_at, updated_at)
SELECT
    gen_random_uuid(),
    r.id,
    fp.id,
    TRUE, FALSE, NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code IN ('grc_role_management.assign', 'grc_role_management.revoke')
  AND r.code = 'grc_lead'
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp
      WHERE rfp.role_id = r.id AND rfp.feature_permission_id = fp.id
  );


-- DOWN ========================================================================

DROP VIEW  IF EXISTS "03_auth_manage"."v_grc_team";
DROP TABLE IF EXISTS "03_auth_manage"."48_lnk_grc_access_grants";
DROP TABLE IF EXISTS "03_auth_manage"."47_lnk_grc_role_assignments";

DELETE FROM "03_auth_manage"."20_lnk_role_feature_permissions"
WHERE feature_permission_id IN (
    SELECT id FROM "03_auth_manage"."15_dim_feature_permissions"
    WHERE feature_flag_code = 'grc_role_management'
);
DELETE FROM "03_auth_manage"."15_dim_feature_permissions"
WHERE feature_flag_code = 'grc_role_management';
DELETE FROM "03_auth_manage"."14_dim_feature_flags"
WHERE code = 'grc_role_management';
