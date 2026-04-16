-- =============================================================================
-- Migration: 20260401_reconcile-groups-roles-permissions.sql
-- Module:    03_auth_manage
-- Description: Reconciles groups, roles, and permissions for staging/prod.
--              - Removes duplicated per-org/workspace groups (old pattern)
--              - Soft-deletes old platform-level GRC roles
--              - Ensures new workspace-level GRC roles exist (from 0330 seed)
--              - Adds missing controls.edit and controls.admin permissions
--              - Creates clean set of 17 global system groups
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Soft-delete duplicated per-org/workspace groups (UUID-prefixed codes)
--    Dev cleaned these up manually; staging/prod still has 43+ groups.
--    We keep only global system groups (no UUID prefix in code).
-- ─────────────────────────────────────────────────────────────────────────────

UPDATE "03_auth_manage"."17_fct_user_groups"
SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE code ~ '^[0-9a-f]{8}_'  -- UUID-prefixed group codes
  AND is_deleted = FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Soft-delete old platform-level GRC roles (replaced by workspace-level)
--    Old: grc_assessor, grc_compliance_lead, grc_control_owner,
--         grc_finding_responder, grc_risk_manager, library_curator
-- ─────────────────────────────────────────────────────────────────────────────

UPDATE "03_auth_manage"."16_fct_roles"
SET is_deleted = TRUE, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
WHERE code IN (
    'grc_assessor', 'grc_compliance_lead', 'grc_control_owner',
    'grc_finding_responder', 'grc_risk_manager', 'library_curator'
)
AND is_deleted = FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Ensure all 17 global system groups exist
--    Idempotent: skips if code already exists and is not deleted
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    v_groups jsonb := '[
        {"level": "super_admin", "code": "platform_super_admin", "name": "Platform Super Admin",       "desc": "Full platform access — bootstrapped by system"},
        {"level": "platform",    "code": "platform_admins",      "name": "Platform Admins",             "desc": "Platform-level administrators"},
        {"level": "platform",    "code": "default_users",        "name": "Default Users",               "desc": "All authenticated users get this group"},
        {"level": "platform",    "code": "external_collaborators","name": "External Collaborators",     "desc": "External users with limited access"},
        {"level": "org",         "code": "org_admins",           "name": "Org Admins",                  "desc": "Organization administrators"},
        {"level": "org",         "code": "org_members",          "name": "Org Members",                 "desc": "Standard organization members"},
        {"level": "org",         "code": "org_viewers",          "name": "Org Viewers",                 "desc": "Read-only organization access"},
        {"level": "workspace",   "code": "workspace_admins",     "name": "Workspace Admins",            "desc": "Workspace-level administrators"},
        {"level": "workspace",   "code": "workspace_contributors","name": "Workspace Contributors",     "desc": "Workspace contributors with write access"},
        {"level": "workspace",   "code": "workspace_viewers",    "name": "Workspace Viewers",           "desc": "Read-only workspace access"},
        {"level": "workspace",   "code": "grc_leads",            "name": "GRC Leads",                   "desc": "GRC program leads with full compliance ownership"},
        {"level": "workspace",   "code": "grc_smes",             "name": "GRC SMEs",                    "desc": "Compliance specialists"},
        {"level": "workspace",   "code": "grc_engineers",        "name": "Engineers",                   "desc": "Remediation and evidence submission"},
        {"level": "workspace",   "code": "grc_cisos",            "name": "CISO / Execs",               "desc": "Executive read-only compliance view"},
        {"level": "workspace",   "code": "grc_lead_auditors",    "name": "Lead Auditors",               "desc": "External lead auditors"},
        {"level": "workspace",   "code": "grc_staff_auditors",   "name": "Staff Auditors",              "desc": "External staff auditors"},
        {"level": "workspace",   "code": "grc_vendors",          "name": "Vendors",                     "desc": "Vendor questionnaire access"}
    ]'::jsonb;
    v_item jsonb;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(v_groups) LOOP
        INSERT INTO "03_auth_manage"."17_fct_user_groups"
            (id, tenant_key, role_level_code, code, name, description,
             is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
             created_at, updated_at)
        SELECT
            gen_random_uuid(),
            'default',
            v_item->>'level',
            v_item->>'code',
            v_item->>'name',
            v_item->>'desc',
            TRUE, FALSE, FALSE, FALSE, TRUE, TRUE, NOW(), NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM "03_auth_manage"."17_fct_user_groups"
            WHERE code = v_item->>'code' AND is_deleted = FALSE
        );
    END LOOP;
END $$;

-- For groups that were soft-deleted and need to be un-deleted (if previously existed)
UPDATE "03_auth_manage"."17_fct_user_groups"
SET is_deleted = FALSE, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
WHERE code IN (
    'platform_super_admin', 'platform_admins', 'default_users', 'external_collaborators',
    'org_admins', 'org_members', 'org_viewers',
    'workspace_admins', 'workspace_contributors', 'workspace_viewers',
    'grc_leads', 'grc_smes', 'grc_engineers', 'grc_cisos',
    'grc_lead_auditors', 'grc_staff_auditors', 'grc_vendors'
)
AND is_deleted = TRUE;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Add missing permissions: controls.edit and controls.admin
--    The engagement router requires these but only view/create/update/delete
--    were seeded in the original migration.
-- ─────────────────────────────────────────────────────────────────────────────

-- First ensure the 'edit' and 'admin' action codes exist in dim table
INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions"
    (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000008001', 'edit', 'Edit', 'Edit/modify resources', 35, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'edit');

INSERT INTO "03_auth_manage"."12_dim_feature_permission_actions"
    (id, code, name, description, sort_order, created_at, updated_at)
SELECT '00000000-0000-0000-0000-000000008002', 'admin', 'Admin', 'Full administrative control', 110, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."12_dim_feature_permission_actions" WHERE code = 'admin');

-- Add controls.edit permission
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000008901',
    'controls.edit',
    'control_management',
    'edit',
    'Edit Controls',
    'Edit control details and manage control-level operations (evidence, engagements)',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.edit');

-- Add controls.admin permission
INSERT INTO "03_auth_manage"."15_dim_feature_permissions"
    (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
SELECT
    '00000000-0000-0000-0000-000000008902',
    'controls.admin',
    'control_management',
    'admin',
    'Admin Controls',
    'Full administrative control over controls, engagements, and audit workflow',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
WHERE NOT EXISTS (SELECT 1 FROM "03_auth_manage"."15_dim_feature_permissions" WHERE code = 'controls.admin');

-- Assign controls.edit to grc_lead, grc_sme roles
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_deleted, created_at, updated_at)
SELECT gen_random_uuid(), r.id, fp.id, TRUE, FALSE, NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code = 'controls.edit'
  AND r.code IN ('grc_lead', 'grc_sme', 'workspace_admin', 'super_admin', 'platform_super_admin')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp
      WHERE rfp.role_id = r.id AND rfp.feature_permission_id = fp.id
  );

-- Assign controls.admin to grc_lead, super_admin roles
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
    (id, role_id, feature_permission_id, is_active, is_deleted, created_at, updated_at)
SELECT gen_random_uuid(), r.id, fp.id, TRUE, FALSE, NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r
CROSS JOIN "03_auth_manage"."15_dim_feature_permissions" fp
WHERE fp.code = 'controls.admin'
  AND r.code IN ('grc_lead', 'workspace_admin', 'super_admin', 'platform_super_admin')
  AND r.is_deleted = FALSE
  AND NOT EXISTS (
      SELECT 1 FROM "03_auth_manage"."20_lnk_role_feature_permissions" rfp
      WHERE rfp.role_id = r.id AND rfp.feature_permission_id = fp.id
  );


-- DOWN ========================================================================

-- Remove permission assignments
DELETE FROM "03_auth_manage"."20_lnk_role_feature_permissions"
WHERE feature_permission_id IN (
    SELECT id FROM "03_auth_manage"."15_dim_feature_permissions"
    WHERE code IN ('controls.edit', 'controls.admin')
);

-- Remove permissions
DELETE FROM "03_auth_manage"."15_dim_feature_permissions"
WHERE code IN ('controls.edit', 'controls.admin');

-- Note: group cleanup and role soft-deletes are not reverted (intentional)
