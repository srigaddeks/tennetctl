-- Enhance comments with markdown, visibility, and inline attachments
ALTER TABLE "08_comments"."01_fct_comments"
    ADD COLUMN IF NOT EXISTS content_format TEXT NOT NULL DEFAULT 'markdown',
    ADD COLUMN IF NOT EXISTS rendered_html TEXT,
    ADD COLUMN IF NOT EXISTS visibility TEXT NOT NULL DEFAULT 'external',
    ADD COLUMN IF NOT EXISTS is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS locked_by UUID,
    ADD COLUMN IF NOT EXISTS locked_at TIMESTAMPTZ;

ALTER TABLE "08_comments"."01_fct_comments"
    ADD CONSTRAINT ck_01_fct_comments_content_format
        CHECK (content_format IN ('plain_text', 'markdown')),
    ADD CONSTRAINT ck_01_fct_comments_visibility
        CHECK (visibility IN ('internal', 'external')),
    ADD CONSTRAINT ck_01_fct_comments_locked_coherence
        CHECK ((is_locked = FALSE AND locked_by IS NULL AND locked_at IS NULL)
            OR (is_locked = TRUE AND locked_by IS NOT NULL AND locked_at IS NOT NULL));

-- Comment-attachment linking
CREATE TABLE IF NOT EXISTS "08_comments"."06_lnk_comment_attachments" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID NOT NULL REFERENCES "08_comments"."01_fct_comments" (id) ON DELETE CASCADE,
    attachment_id UUID NOT NULL,
    sort_order INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_06_lnk_comment_attachments UNIQUE (comment_id, attachment_id)
);

CREATE INDEX idx_06_lnk_comment_attachments_comment
    ON "08_comments"."06_lnk_comment_attachments" (comment_id);
CREATE INDEX idx_06_lnk_comment_attachments_attachment
    ON "08_comments"."06_lnk_comment_attachments" (attachment_id);

-- Index for visibility filtering
CREATE INDEX idx_01_fct_comments_visibility
    ON "08_comments"."01_fct_comments" (entity_type, entity_id, visibility, is_deleted, created_at DESC);
