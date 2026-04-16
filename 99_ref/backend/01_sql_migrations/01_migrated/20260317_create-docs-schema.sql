-- ===========================================================================
-- Migration: Document Library schema (11_docs)
-- Date: 2026-03-17
-- Description: Global and org-scoped document library for policies, compliance
--   guides, templates, and RAG knowledge base. Separate from entity-attachments.
-- ===========================================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- ---------------------------------------------------------------------------
-- Dimension: document categories
-- ---------------------------------------------------------------------------
CREATE TABLE "11_docs"."01_dim_doc_categories" (
    code            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    description     TEXT,
    sort_order      INT  NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

INSERT INTO "11_docs"."01_dim_doc_categories" (code, name, description, sort_order) VALUES
    ('policy',           'Policy',              'Organisational policies and governance documents',           10),
    ('procedure',        'Procedure',           'Standard operating procedures and runbooks',                 20),
    ('framework_guide',  'Framework Guide',     'Compliance framework reference guides (ISO, SOC 2, etc.)',   30),
    ('template',         'Template',            'Document templates for evidence, reports, assessments',      40),
    ('reference',        'Reference',           'Technical reference and architecture documentation',         50),
    ('compliance',       'Compliance',          'Compliance evidence, certificates, and attestations',        60),
    ('sandbox',          'Sandbox',             'K-Control Sandbox reference docs and signal libraries',      70),
    ('training',         'Training',            'Training materials and onboarding guides',                   80),
    ('other',            'Other',               'Miscellaneous documents',                                    90);

-- ---------------------------------------------------------------------------
-- Main document fact table
-- ---------------------------------------------------------------------------
CREATE TABLE "11_docs"."02_fct_documents" (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key          TEXT        NOT NULL,
    scope               TEXT        NOT NULL CHECK (scope IN ('global', 'org')),
    org_id              UUID,                           -- NULL for global docs
    category_code       TEXT        NOT NULL REFERENCES "11_docs"."01_dim_doc_categories"(code),
    title               TEXT        NOT NULL CHECK (char_length(title) BETWEEN 1 AND 500),
    description         TEXT,
    tags                TEXT[]      NOT NULL DEFAULT '{}',
    version_label       TEXT,                           -- e.g. "v2.1", "2024-Q1"
    -- storage
    original_filename   TEXT        NOT NULL,
    storage_key         TEXT        NOT NULL,
    storage_provider    TEXT        NOT NULL CHECK (storage_provider IN ('s3','gcs','azure','minio')),
    storage_bucket      TEXT        NOT NULL,
    storage_url         TEXT,
    content_type        TEXT        NOT NULL,
    file_size_bytes     BIGINT      NOT NULL DEFAULT 0,
    checksum_sha256     TEXT,
    -- virus scan
    virus_scan_status   TEXT        NOT NULL DEFAULT 'pending' CHECK (virus_scan_status IN ('pending','clean','infected','error','skipped')),
    virus_scan_at       TIMESTAMPTZ,
    -- lifecycle
    uploaded_by         UUID        NOT NULL,
    is_deleted          BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_at          TIMESTAMPTZ,
    deleted_by          UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_org_scope CHECK (
        (scope = 'global' AND org_id IS NULL) OR
        (scope = 'org' AND org_id IS NOT NULL)
    )
);

CREATE INDEX idx_02_fct_docs_global        ON "11_docs"."02_fct_documents" (scope, category_code, created_at DESC) WHERE scope = 'global' AND is_deleted = FALSE;
CREATE INDEX idx_02_fct_docs_org           ON "11_docs"."02_fct_documents" (org_id, category_code, created_at DESC) WHERE scope = 'org' AND is_deleted = FALSE;
CREATE INDEX idx_02_fct_docs_tenant        ON "11_docs"."02_fct_documents" (tenant_key, created_at DESC);
CREATE INDEX idx_02_fct_docs_uploaded_by   ON "11_docs"."02_fct_documents" (uploaded_by);
CREATE INDEX idx_02_fct_docs_tags          ON "11_docs"."02_fct_documents" USING GIN (tags);
CREATE INDEX idx_02_fct_docs_fts           ON "11_docs"."02_fct_documents" USING GIN (to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,'')));
CREATE INDEX brin_02_fct_docs_created      ON "11_docs"."02_fct_documents" USING BRIN (created_at);

CREATE OR REPLACE FUNCTION "11_docs".fn_update_doc_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$;
CREATE TRIGGER trg_02_fct_docs_updated_at
    BEFORE UPDATE ON "11_docs"."02_fct_documents"
    FOR EACH ROW EXECUTE FUNCTION "11_docs".fn_update_doc_timestamp();

-- ---------------------------------------------------------------------------
-- Download tracking
-- ---------------------------------------------------------------------------
CREATE TABLE "11_docs"."03_trx_doc_downloads" (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID        NOT NULL REFERENCES "11_docs"."02_fct_documents"(id) ON DELETE CASCADE,
    downloaded_by   UUID        NOT NULL,
    downloaded_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_ip       TEXT,
    user_agent      TEXT
);
CREATE INDEX idx_03_trx_downloads_doc ON "11_docs"."03_trx_doc_downloads" (document_id, downloaded_at DESC);
CREATE INDEX brin_03_trx_downloads_at ON "11_docs"."03_trx_doc_downloads" USING BRIN (downloaded_at);

-- ---------------------------------------------------------------------------
-- Audit log
-- ---------------------------------------------------------------------------
CREATE TABLE "11_docs"."04_aud_doc_events" (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID,                               -- nullable (doc may be deleted)
    scope           TEXT,
    org_id          UUID,
    event_type      TEXT        NOT NULL CHECK (event_type IN (
                        'uploaded', 'downloaded', 'deleted', 'description_updated',
                        'tags_updated', 'title_updated', 'version_updated',
                        'virus_scan_completed'
                    )),
    actor_user_id   UUID        NOT NULL,
    tenant_key      TEXT        NOT NULL,
    metadata        JSONB       NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_04_aud_doc_events_doc    ON "11_docs"."04_aud_doc_events" (document_id, created_at DESC);
CREATE INDEX idx_04_aud_doc_events_actor  ON "11_docs"."04_aud_doc_events" (actor_user_id, created_at DESC);
CREATE INDEX brin_04_aud_doc_events_at    ON "11_docs"."04_aud_doc_events" USING BRIN (created_at);
