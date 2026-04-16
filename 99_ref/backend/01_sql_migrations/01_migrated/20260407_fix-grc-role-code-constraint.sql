-- 20260407_fix-grc-role-code-constraint.sql
-- Align chk_47_grc_ra_role_code with the application's _GRC_ROLE_CODES set.
--
-- Background: a sync-from-staging migration (20260402_sync-dev-from-staging.sql)
-- reverted the CHECK constraint on "47_lnk_grc_role_assignments".grc_role_code
-- to the legacy 7-value set, dropping 'grc_practitioner'. The application code
-- in backend/03_auth_manage/_scoped_group_provisioning.py still inserts
-- 'grc_practitioner' (and 'grc_lead' coexists for legacy data), so any GRC
-- invite assignment with the new code fails with CheckViolationError. This
-- broke both the authenticated /invitations/accept path and the new public
-- /invitations/accept-public path.
--
-- This migration recreates the constraint with the union of legacy + current
-- codes — no data is touched, no rows need to migrate.

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        DROP CONSTRAINT IF EXISTS chk_47_grc_ra_role_code;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        ADD CONSTRAINT chk_47_grc_ra_role_code
        CHECK (((grc_role_code)::text = ANY ((ARRAY[
            'grc_lead'::character varying,
            'grc_sme'::character varying,
            'grc_practitioner'::character varying,
            'grc_engineer'::character varying,
            'grc_ciso'::character varying,
            'grc_lead_auditor'::character varying,
            'grc_staff_auditor'::character varying,
            'grc_vendor'::character varying
        ])::text[])));
EXCEPTION WHEN undefined_table THEN NULL; END $$;
