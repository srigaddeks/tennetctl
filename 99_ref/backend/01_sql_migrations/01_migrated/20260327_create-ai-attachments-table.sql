-- ─────────────────────────────────────────────────────────────────────────────
-- AI Attachments: document text extraction for framework builder agent
-- Stores pre-extracted text from uploaded documents for AI consumption
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "20_ai"."19_fct_attachments" (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key      VARCHAR(100) NOT NULL,
    user_id         UUID         NOT NULL,
    filename        VARCHAR(500) NOT NULL,
    content_type    VARCHAR(200) NULL,
    file_size_bytes INTEGER      NULL,
    extracted_text  TEXT         NULL,
    status_code     VARCHAR(50)  NOT NULL DEFAULT 'pending'
                        CHECK (status_code IN ('pending', 'processing', 'ready', 'failed')),
    error_message   TEXT         NULL,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,
    updated_by      UUID         NULL
);

CREATE INDEX IF NOT EXISTS idx_19_fct_attachments_tenant
    ON "20_ai"."19_fct_attachments" (tenant_key);
CREATE INDEX IF NOT EXISTS idx_19_fct_attachments_user
    ON "20_ai"."19_fct_attachments" (user_id);
CREATE INDEX IF NOT EXISTS idx_19_fct_attachments_status
    ON "20_ai"."19_fct_attachments" (status_code)
    WHERE status_code = 'ready';
