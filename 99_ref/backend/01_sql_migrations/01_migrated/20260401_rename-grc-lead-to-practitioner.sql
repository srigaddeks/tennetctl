-- =============================================================================
-- Migration: 20260401_rename-grc-lead-to-practitioner.sql
-- Module:    03_auth_manage
-- Description: Consolidate grc_lead + grc_sme into single grc_practitioner role
-- =============================================================================

-- UP ==========================================================================

-- 1. Update the role row: rename grc_lead → grc_practitioner
UPDATE "03_auth_manage"."16_fct_roles"
SET code = 'grc_practitioner',
    name = 'GRC Practitioner'
WHERE code = 'grc_lead';

-- 2. Reassign any existing grc_sme assignments to grc_practitioner
UPDATE "03_auth_manage"."47_lnk_grc_role_assignments"
SET grc_role_code = 'grc_practitioner'
WHERE grc_role_code = 'grc_sme';

UPDATE "03_auth_manage"."47_lnk_grc_role_assignments"
SET grc_role_code = 'grc_practitioner'
WHERE grc_role_code = 'grc_lead';

-- 3. Update workspace memberships using old codes
UPDATE "03_auth_manage"."36_lnk_workspace_memberships"
SET grc_role_code = 'grc_practitioner'
WHERE grc_role_code IN ('grc_lead', 'grc_sme');

-- 4. Update invitations using old codes
UPDATE "03_auth_manage"."44_trx_invitations"
SET grc_role_code = 'grc_practitioner'
WHERE grc_role_code IN ('grc_lead', 'grc_sme');

-- 5. Move role_views from grc_sme role to grc_practitioner role (if any)
INSERT INTO "03_auth_manage"."51_lnk_role_views" (role_id, view_code, created_by)
SELECT
    (SELECT id FROM "03_auth_manage"."16_fct_roles" WHERE code = 'grc_practitioner'),
    rv.view_code,
    rv.created_by
FROM "03_auth_manage"."51_lnk_role_views" rv
JOIN "03_auth_manage"."16_fct_roles" r ON r.id = rv.role_id
WHERE r.code = 'grc_sme'
ON CONFLICT (role_id, view_code) DO NOTHING;

-- 6. Soft-delete the grc_sme role (keep for audit trail)
UPDATE "03_auth_manage"."16_fct_roles"
SET is_deleted = TRUE
WHERE code = 'grc_sme';

-- 7. Drop and re-create CHECK constraint on grc_role_assignments
ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
    DROP CONSTRAINT IF EXISTS chk_47_grc_ra_role_code;

ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
    ADD CONSTRAINT chk_47_grc_ra_role_code CHECK (
        grc_role_code IN (
            'grc_practitioner', 'grc_engineer', 'grc_ciso',
            'grc_lead_auditor', 'grc_staff_auditor', 'grc_vendor'
        )
    );

-- DOWN ========================================================================

-- Revert CHECK constraint
ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
    DROP CONSTRAINT IF EXISTS chk_47_grc_ra_role_code;

ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
    ADD CONSTRAINT chk_47_grc_ra_role_code CHECK (
        grc_role_code IN (
            'grc_lead', 'grc_sme', 'grc_engineer', 'grc_ciso',
            'grc_lead_auditor', 'grc_staff_auditor', 'grc_vendor'
        )
    );

-- Re-activate grc_sme
UPDATE "03_auth_manage"."16_fct_roles"
SET is_deleted = FALSE
WHERE code = 'grc_sme';

-- Rename back
UPDATE "03_auth_manage"."16_fct_roles"
SET code = 'grc_lead',
    name = 'GRC Lead'
WHERE code = 'grc_practitioner';

-- Revert assignments
UPDATE "03_auth_manage"."47_lnk_grc_role_assignments"
SET grc_role_code = 'grc_lead'
WHERE grc_role_code = 'grc_practitioner';

UPDATE "03_auth_manage"."36_lnk_workspace_memberships"
SET grc_role_code = 'grc_lead'
WHERE grc_role_code = 'grc_practitioner';
