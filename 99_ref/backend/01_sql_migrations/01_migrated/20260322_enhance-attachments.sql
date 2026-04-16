-- ===========================================================================
-- Migration: Enhance attachments — storage quota, versioning, audit immutability
-- Date: 2026-03-22
-- Description: Storage quota materialized view, attachment versioning table,
--              and immutability triggers on audit and edit-history tables.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- Materialized view: org storage usage (refreshed periodically or on upload)
-- ---------------------------------------------------------------------------
CREATE MATERIALIZED VIEW IF NOT EXISTS "09_attachments"."mv_org_storage_usage" AS
SELECT
    tenant_key,
    COUNT(*) AS total_files,
    COALESCE(SUM(file_size_bytes), 0) AS total_bytes,
    COUNT(*) FILTER (WHERE virus_scan_status = 'infected') AS infected_count,
    COUNT(*) FILTER (WHERE virus_scan_status = 'pending') AS pending_scan_count
FROM "09_attachments"."01_fct_attachments"
WHERE is_deleted = FALSE
GROUP BY tenant_key;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_org_storage_usage_tenant
    ON "09_attachments"."mv_org_storage_usage" (tenant_key);

-- ---------------------------------------------------------------------------
-- Attachment versioning table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_attachments"."04_trx_attachment_versions" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attachment_id UUID NOT NULL REFERENCES "09_attachments"."01_fct_attachments" (id) ON DELETE CASCADE,
    version_number INT NOT NULL DEFAULT 1,
    storage_key TEXT NOT NULL,
    storage_bucket TEXT NOT NULL,
    file_size_bytes BIGINT NOT NULL CHECK (file_size_bytes > 0),
    checksum_sha256 TEXT NOT NULL CHECK (length(checksum_sha256) = 64),
    content_type TEXT NOT NULL,
    uploaded_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_04_attachment_version UNIQUE (attachment_id, version_number)
);

CREATE INDEX idx_04_trx_attachment_versions_attachment
    ON "09_attachments"."04_trx_attachment_versions" (attachment_id, version_number DESC);

-- ---------------------------------------------------------------------------
-- Audit log immutability functions
-- ---------------------------------------------------------------------------

-- Comment schema immutability function
CREATE OR REPLACE FUNCTION "08_comments".fn_prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit records are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

-- Attachment schema immutability function
CREATE OR REPLACE FUNCTION "09_attachments".fn_prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit records are immutable and cannot be modified or deleted';
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------------------
-- Apply immutability triggers to comment audit table
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_04_aud_comment_events_immutable_update ON "08_comments"."04_aud_comment_events";
CREATE TRIGGER trg_04_aud_comment_events_immutable_update
    BEFORE UPDATE ON "08_comments"."04_aud_comment_events"
    FOR EACH ROW EXECUTE FUNCTION "08_comments".fn_prevent_audit_mutation();

DROP TRIGGER IF EXISTS trg_04_aud_comment_events_immutable_delete ON "08_comments"."04_aud_comment_events";
CREATE TRIGGER trg_04_aud_comment_events_immutable_delete
    BEFORE DELETE ON "08_comments"."04_aud_comment_events"
    FOR EACH ROW EXECUTE FUNCTION "08_comments".fn_prevent_audit_mutation();

-- ---------------------------------------------------------------------------
-- Apply immutability triggers to attachment audit table
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_03_aud_attachment_events_immutable_update ON "09_attachments"."03_aud_attachment_events";
CREATE TRIGGER trg_03_aud_attachment_events_immutable_update
    BEFORE UPDATE ON "09_attachments"."03_aud_attachment_events"
    FOR EACH ROW EXECUTE FUNCTION "09_attachments".fn_prevent_audit_mutation();

DROP TRIGGER IF EXISTS trg_03_aud_attachment_events_immutable_delete ON "09_attachments"."03_aud_attachment_events";
CREATE TRIGGER trg_03_aud_attachment_events_immutable_delete
    BEFORE DELETE ON "09_attachments"."03_aud_attachment_events"
    FOR EACH ROW EXECUTE FUNCTION "09_attachments".fn_prevent_audit_mutation();

-- ---------------------------------------------------------------------------
-- Apply immutability triggers to comment edit history (should also be immutable)
-- ---------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_02_trx_comment_edits_immutable_update ON "08_comments"."02_trx_comment_edits";
CREATE TRIGGER trg_02_trx_comment_edits_immutable_update
    BEFORE UPDATE ON "08_comments"."02_trx_comment_edits"
    FOR EACH ROW EXECUTE FUNCTION "08_comments".fn_prevent_audit_mutation();

DROP TRIGGER IF EXISTS trg_02_trx_comment_edits_immutable_delete ON "08_comments"."02_trx_comment_edits";
CREATE TRIGGER trg_02_trx_comment_edits_immutable_delete
    BEFORE DELETE ON "08_comments"."02_trx_comment_edits"
    FOR EACH ROW EXECUTE FUNCTION "08_comments".fn_prevent_audit_mutation();

-- ---------------------------------------------------------------------------
-- Widen the event_type CHECK on attachment audit to allow GDPR events
-- ---------------------------------------------------------------------------
ALTER TABLE "09_attachments"."03_aud_attachment_events"
    DROP CONSTRAINT IF EXISTS "ck_03_aud_attachment_events_event_type";

ALTER TABLE "09_attachments"."03_aud_attachment_events"
    ADD CONSTRAINT "ck_03_aud_attachment_events_event_type" CHECK (
        event_type IN (
            'uploaded', 'downloaded', 'deleted', 'virus_scan_completed',
            'description_updated', 'storage_cleanup_failed', 'gdpr_data_deleted'
        )
    );
