-- ===========================================================================
-- Migration: Create attachments schema
-- Date: 2026-03-22
-- Description: Enterprise-grade file attachments system supporting S3, GCS,
--              Azure Blob Storage, and MinIO.
--
-- Row-Level Security (RLS) notes:
--   This schema stores files that belong to tenants. If RLS is enabled in a
--   future phase, policies on "01_fct_attachments" should filter by
--   tenant_key using a current_setting('app.tenant_key') session variable.
--   The "02_trx_attachment_downloads" table can be gated by joining to the
--   parent attachment's tenant_key. The audit table (03_aud) already carries
--   tenant_key for post-hoc filtering.
-- ===========================================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- ---------------------------------------------------------------------------
-- 01_fct_attachments — main attachment fact table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_attachments"."01_fct_attachments" (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    tenant_key          TEXT        NOT NULL,
    entity_type         TEXT        NOT NULL,  -- task, risk, control, framework, evidence_template, test, comment
    entity_id           UUID        NOT NULL,
    uploaded_by         UUID        NOT NULL,
    original_filename   TEXT        NOT NULL,
    storage_key         TEXT        NOT NULL,  -- path in object storage e.g. "tenant/entity_type/entity_id/uuid/filename"
    storage_provider    TEXT        NOT NULL,  -- s3, gcs, azure, minio
    storage_bucket      TEXT        NOT NULL,
    content_type        TEXT        NOT NULL,  -- MIME type
    file_size_bytes     BIGINT      NOT NULL,
    checksum_sha256     TEXT        NOT NULL,  -- for integrity verification
    is_deleted          BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID,
    virus_scan_status   TEXT        NOT NULL DEFAULT 'pending',  -- pending, clean, infected, error, skipped
    virus_scan_at       TIMESTAMPTZ,
    description         TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT "01_fct_attachments_pkey" PRIMARY KEY (id),
    CONSTRAINT "ck_01_fct_attachments_entity_type" CHECK (
        entity_type IN ('task', 'risk', 'control', 'framework', 'evidence_template', 'test', 'comment')
    ),
    CONSTRAINT "ck_01_fct_attachments_storage_provider" CHECK (
        storage_provider IN ('s3', 'gcs', 'azure', 'minio')
    ),
    CONSTRAINT "ck_01_fct_attachments_virus_scan_status" CHECK (
        virus_scan_status IN ('pending', 'clean', 'infected', 'error', 'skipped')
    ),
    CONSTRAINT "ck_01_fct_attachments_file_size_positive" CHECK (
        file_size_bytes > 0
    ),
    CONSTRAINT "01_fct_attachments_storage_key_unique" UNIQUE (storage_key),
    -- Data integrity constraints
    CONSTRAINT ck_01_fct_attachments_deleted_coherence
        CHECK ((is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
            OR (is_deleted = TRUE AND deleted_at IS NOT NULL)),
    CONSTRAINT ck_01_fct_attachments_checksum_format
        CHECK (length(checksum_sha256) = 64),
    CONSTRAINT ck_01_fct_attachments_filename_nonempty
        CHECK (length(original_filename) > 0)
);

-- Composite index: the primary list query filters by entity + active flag and sorts by created_at.
-- Covering is_deleted in the index lets Postgres satisfy the WHERE without a heap fetch when
-- only counting or checking existence.
CREATE INDEX IF NOT EXISTS "idx_01_fct_attachments_entity_active"
    ON "09_attachments"."01_fct_attachments" (entity_type, entity_id, created_at DESC)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS "idx_01_fct_attachments_tenant_key"
    ON "09_attachments"."01_fct_attachments" (tenant_key)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS "idx_01_fct_attachments_uploaded_by"
    ON "09_attachments"."01_fct_attachments" (uploaded_by)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS "idx_01_fct_attachments_virus_scan_status"
    ON "09_attachments"."01_fct_attachments" (virus_scan_status)
    WHERE is_deleted = FALSE;

-- BRIN index on the append-only created_at column.  Extremely compact; useful
-- for time-range scans on large tables where rows are inserted in order.
CREATE INDEX IF NOT EXISTS "idx_01_fct_attachments_created_at_brin"
    ON "09_attachments"."01_fct_attachments" USING BRIN (created_at);

-- ---------------------------------------------------------------------------
-- TRIGGER — auto-update updated_at on 01_fct_attachments
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION "09_attachments".fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_01_fct_attachments_updated_at
    BEFORE UPDATE ON "09_attachments"."01_fct_attachments"
    FOR EACH ROW EXECUTE FUNCTION "09_attachments".fn_update_timestamp();

-- ---------------------------------------------------------------------------
-- 02_trx_attachment_downloads — download tracking
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_attachments"."02_trx_attachment_downloads" (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    attachment_id   UUID        NOT NULL,
    downloaded_by   UUID        NOT NULL,
    downloaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_ip       TEXT,
    user_agent      TEXT,

    CONSTRAINT "02_trx_attachment_downloads_pkey" PRIMARY KEY (id),
    CONSTRAINT "02_trx_attachment_downloads_attachment_fk"
        FOREIGN KEY (attachment_id)
        REFERENCES "09_attachments"."01_fct_attachments" (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "idx_02_trx_attachment_downloads_attachment"
    ON "09_attachments"."02_trx_attachment_downloads" (attachment_id, downloaded_at DESC);

CREATE INDEX IF NOT EXISTS "idx_02_trx_attachment_downloads_downloaded_by"
    ON "09_attachments"."02_trx_attachment_downloads" (downloaded_by, downloaded_at DESC);

-- BRIN index for time-range queries on this high-volume append-only table.
CREATE INDEX IF NOT EXISTS "idx_02_trx_attachment_downloads_downloaded_at_brin"
    ON "09_attachments"."02_trx_attachment_downloads" USING BRIN (downloaded_at);

-- ---------------------------------------------------------------------------
-- 03_aud_attachment_events — audit log
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "09_attachments"."03_aud_attachment_events" (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    attachment_id   UUID,
    entity_type     TEXT        NOT NULL,
    entity_id       UUID        NOT NULL,
    event_type      TEXT        NOT NULL,  -- uploaded, downloaded, deleted, virus_scan_completed, description_updated
    actor_user_id   UUID        NOT NULL,
    tenant_key      TEXT        NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT "03_aud_attachment_events_pkey" PRIMARY KEY (id),
    CONSTRAINT "ck_03_aud_attachment_events_event_type" CHECK (
        event_type IN ('uploaded', 'downloaded', 'deleted', 'virus_scan_completed', 'description_updated')
    )
);

CREATE INDEX IF NOT EXISTS "idx_03_aud_attachment_events_attachment"
    ON "09_attachments"."03_aud_attachment_events" (attachment_id, created_at DESC);

CREATE INDEX IF NOT EXISTS "idx_03_aud_attachment_events_entity"
    ON "09_attachments"."03_aud_attachment_events" (entity_type, entity_id, created_at DESC);

CREATE INDEX IF NOT EXISTS "idx_03_aud_attachment_events_tenant_key"
    ON "09_attachments"."03_aud_attachment_events" (tenant_key, created_at DESC);

CREATE INDEX IF NOT EXISTS "idx_03_aud_attachment_events_actor"
    ON "09_attachments"."03_aud_attachment_events" (actor_user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS "idx_03_aud_attachment_events_event_type"
    ON "09_attachments"."03_aud_attachment_events" (event_type, created_at DESC);

-- BRIN index for time-range scans on the audit table.
CREATE INDEX IF NOT EXISTS "idx_03_aud_attachment_events_created_at_brin"
    ON "09_attachments"."03_aud_attachment_events" USING BRIN (created_at);

-- NOTE: 03_aud_attachment_events intentionally has NO FK to 01_fct_attachments.
-- Audit records must persist independently for compliance, even after hard deletes.
