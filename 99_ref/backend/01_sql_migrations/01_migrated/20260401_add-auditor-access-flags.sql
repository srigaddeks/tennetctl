-- =============================================================================
-- Migration: 20260401_add-auditor-access-flags.sql
-- Module:    09_attachments, 20_ai
-- Description: Adds auditor_access boolean to attachments and reports.
--              When TRUE, the attachment/report is visible to external auditors
--              via engagement endpoints. When FALSE (default), only internal
--              GRC team can see it. This enables the readiness → audit workflow
--              where internal teams prepare evidence and selectively publish
--              it for auditor review.
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Add auditor_access to attachments
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE "09_attachments"."01_fct_attachments"
    ADD COLUMN IF NOT EXISTS auditor_access BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN "09_attachments"."01_fct_attachments".auditor_access
    IS 'When TRUE, this attachment is visible to external auditors in audit engagements. Default FALSE (internal only). Set by GRC team when evidence is ready for auditor review.';

-- Add published_by and published_at for audit trail of who made it auditor-visible
ALTER TABLE "09_attachments"."01_fct_attachments"
    ADD COLUMN IF NOT EXISTS published_for_audit_by UUID;

ALTER TABLE "09_attachments"."01_fct_attachments"
    ADD COLUMN IF NOT EXISTS published_for_audit_at TIMESTAMP;

COMMENT ON COLUMN "09_attachments"."01_fct_attachments".published_for_audit_by
    IS 'UUID of the user who marked this attachment as auditor-visible. NULL if not published.';
COMMENT ON COLUMN "09_attachments"."01_fct_attachments".published_for_audit_at
    IS 'Timestamp when the attachment was marked as auditor-visible. NULL if not published.';

-- Index for fast auditor-visible queries
CREATE INDEX IF NOT EXISTS idx_01_fct_attachments_auditor_access
    ON "09_attachments"."01_fct_attachments" (entity_type, entity_id)
    WHERE auditor_access = TRUE AND is_deleted = FALSE;

COMMENT ON INDEX "09_attachments".idx_01_fct_attachments_auditor_access
    IS 'Fast lookup of auditor-visible attachments per entity.';

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Add auditor_access to reports
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE "20_ai"."50_fct_reports"
    ADD COLUMN IF NOT EXISTS auditor_access BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN "20_ai"."50_fct_reports".auditor_access
    IS 'When TRUE, this report is visible to external auditors in audit engagements. Default FALSE (internal only).';

ALTER TABLE "20_ai"."50_fct_reports"
    ADD COLUMN IF NOT EXISTS published_for_audit_by UUID;

ALTER TABLE "20_ai"."50_fct_reports"
    ADD COLUMN IF NOT EXISTS published_for_audit_at TIMESTAMP;

COMMENT ON COLUMN "20_ai"."50_fct_reports".published_for_audit_by
    IS 'UUID of the user who marked this report as auditor-visible. NULL if not published.';
COMMENT ON COLUMN "20_ai"."50_fct_reports".published_for_audit_at
    IS 'Timestamp when the report was marked as auditor-visible. NULL if not published.';

-- Index for fast auditor-visible report queries
CREATE INDEX IF NOT EXISTS idx_50_fct_reports_auditor_access
    ON "20_ai"."50_fct_reports" (trigger_entity_type, trigger_entity_id)
    WHERE auditor_access = TRUE;

COMMENT ON INDEX "20_ai".idx_50_fct_reports_auditor_access
    IS 'Fast lookup of auditor-visible reports per trigger entity.';


-- DOWN ========================================================================

DROP INDEX IF EXISTS "20_ai".idx_50_fct_reports_auditor_access;
ALTER TABLE "20_ai"."50_fct_reports" DROP COLUMN IF EXISTS published_for_audit_at;
ALTER TABLE "20_ai"."50_fct_reports" DROP COLUMN IF EXISTS published_for_audit_by;
ALTER TABLE "20_ai"."50_fct_reports" DROP COLUMN IF EXISTS auditor_access;

DROP INDEX IF EXISTS "09_attachments".idx_01_fct_attachments_auditor_access;
ALTER TABLE "09_attachments"."01_fct_attachments" DROP COLUMN IF EXISTS published_for_audit_at;
ALTER TABLE "09_attachments"."01_fct_attachments" DROP COLUMN IF EXISTS published_for_audit_by;
ALTER TABLE "09_attachments"."01_fct_attachments" DROP COLUMN IF EXISTS auditor_access;
