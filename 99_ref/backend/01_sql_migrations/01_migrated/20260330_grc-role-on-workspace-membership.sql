-- ─────────────────────────────────────────────────────────────────────────────
-- Add grc_role_code to workspace memberships
--
-- GRC role assignment moves from group indirection to a direct column on the
-- workspace membership record. This removes the need to provision per-workspace
-- GRC groups. The permission check reads this column directly.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE "03_auth_manage"."36_lnk_workspace_memberships"
    ADD COLUMN IF NOT EXISTS grc_role_code VARCHAR(50) DEFAULT NULL;

COMMENT ON COLUMN "03_auth_manage"."36_lnk_workspace_memberships".grc_role_code
    IS 'GRC workspace role for this member (grc_lead, grc_sme, grc_engineer, grc_ciso, grc_lead_auditor, grc_staff_auditor, grc_vendor). NULL for non-GRC workspaces or members without a GRC role.';
