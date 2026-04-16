-- Add grc_role_code to invitations so GRC group assignment is
-- automatically applied when the invitee accepts.

ALTER TABLE "03_auth_manage"."44_trx_invitations"
ADD COLUMN IF NOT EXISTS grc_role_code VARCHAR(50) DEFAULT NULL;

COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".grc_role_code
  IS 'GRC workspace role to auto-assign on acceptance (e.g. grc_lead_auditor). NULL for non-GRC invitations.';
