-- PageIndex columns on conversation attachments
-- Adds three columns to support hierarchical TOC-based RAG alongside vector RAG.
-- pageindex_status: none | indexing | ready | failed
-- pageindex_tree:   JSONB TOC hierarchy built by Phase 1 LLM call
-- pageindex_error:  last error message if status=failed

ALTER TABLE "20_ai"."44_fct_conversation_attachments"
    ADD COLUMN IF NOT EXISTS pageindex_status  VARCHAR(50) NOT NULL DEFAULT 'none',
    ADD COLUMN IF NOT EXISTS pageindex_tree    JSONB       DEFAULT NULL,
    ADD COLUMN IF NOT EXISTS pageindex_error   TEXT        DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_44_fct_conv_att_pageindex_status
    ON "20_ai"."44_fct_conversation_attachments" (pageindex_status)
    WHERE pageindex_status != 'none';
