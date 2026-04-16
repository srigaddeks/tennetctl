-- Add is_draft column to connector instances
-- Draft connectors are saved but not yet connection-tested; they don't
-- participate in scheduled collection until promoted to active.
-- ---------------------------------------------------------------------------

ALTER TABLE "15_sandbox"."20_fct_connector_instances"
    ADD COLUMN IF NOT EXISTS is_draft BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN "15_sandbox"."20_fct_connector_instances".is_draft
    IS 'TRUE = saved as draft, not yet connection-tested. Collection is disabled for drafts.';
