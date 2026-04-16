-- ============================================================
-- 20260318_add-copilot-attachments.sql
-- Conversation attachment tracking for AI copilot
-- Documents are chunked and stored in Qdrant kcontrol_copilot collection
-- ============================================================

BEGIN;

-- Track uploaded attachments per conversation
CREATE TABLE "20_ai"."44_fct_conversation_attachments" (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id     UUID         NOT NULL REFERENCES "20_ai"."20_fct_conversations"(id) ON DELETE CASCADE,
    tenant_key          VARCHAR(100) NOT NULL,
    user_id             UUID         NOT NULL,
    filename            VARCHAR(500) NOT NULL,
    content_type        VARCHAR(200) NOT NULL,
    file_size_bytes     INT          NOT NULL,
    chunk_count         INT          NOT NULL DEFAULT 0,
    ingest_status       VARCHAR(50)  NOT NULL DEFAULT 'pending'
                            CHECK (ingest_status IN ('pending', 'ingesting', 'ready', 'failed')),
    error_message       TEXT,
    qdrant_collection   VARCHAR(200) NOT NULL DEFAULT 'kcontrol_copilot',
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conv_attachments_conv    ON "20_ai"."44_fct_conversation_attachments"(conversation_id);
CREATE INDEX idx_conv_attachments_user    ON "20_ai"."44_fct_conversation_attachments"(user_id);
CREATE INDEX idx_conv_attachments_tenant  ON "20_ai"."44_fct_conversation_attachments"(tenant_key);
CREATE INDEX idx_conv_attachments_status  ON "20_ai"."44_fct_conversation_attachments"(ingest_status);

COMMIT;
