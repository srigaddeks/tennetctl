-- UP ====
-- Add JSONB array columns for multiple framework/engagement scope IDs on invitations.
-- These complement the existing single-value framework_id / engagement_id columns.
-- When set, _auto_enroll creates access grants for every ID in the array.

ALTER TABLE "03_auth_manage"."44_trx_invitations"
    ADD COLUMN IF NOT EXISTS framework_ids JSONB DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS engagement_ids JSONB DEFAULT NULL;

COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".framework_ids
    IS 'JSONB array of framework deployment UUIDs when multiple frameworks are selected. Overrides single framework_id.';
COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".engagement_ids
    IS 'JSONB array of engagement UUIDs when multiple engagements are selected. Overrides single engagement_id.';

-- DOWN ====
ALTER TABLE "03_auth_manage"."44_trx_invitations"
    DROP COLUMN IF EXISTS framework_ids,
    DROP COLUMN IF EXISTS engagement_ids;
