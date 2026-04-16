-- Add engagement_id and framework_id to invitations for GRC scoped access.
--
-- engagement_id: accepting the invite auto-creates an audit access token for the engagement.
-- framework_id: informational scope — records which framework this auditor is working against.
--               No enforcement in v1; stored for future fine-grained permission control.

-- UP =========================================================================

ALTER TABLE "03_auth_manage"."44_trx_invitations"
    ADD COLUMN IF NOT EXISTS engagement_id UUID DEFAULT NULL;

COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".engagement_id
    IS 'If set, accepting this invitation auto-creates an audit access token for this engagement (auditor pathway only).';

ALTER TABLE "03_auth_manage"."44_trx_invitations"
    ADD COLUMN IF NOT EXISTS framework_id UUID DEFAULT NULL;

COMMENT ON COLUMN "03_auth_manage"."44_trx_invitations".framework_id
    IS 'Optional framework scope. Informational in v1 — stored so future access control can enforce framework-level visibility.';

-- DOWN =======================================================================
-- ALTER TABLE "03_auth_manage"."44_trx_invitations" DROP COLUMN IF EXISTS engagement_id;
-- ALTER TABLE "03_auth_manage"."44_trx_invitations" DROP COLUMN IF EXISTS framework_id;
