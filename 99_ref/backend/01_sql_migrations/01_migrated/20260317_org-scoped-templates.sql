-- ============================================================================
-- Org-Scoped Templates + Enhanced Broadcasts
-- ============================================================================
-- Adds org_id to templates for per-org overrides, and static_variables
-- to broadcasts for admin-set variables that merge with per-recipient resolution.
-- ============================================================================

-- ── Add org_id to templates ─────────────────────────────────────────────────

ALTER TABLE "03_notifications"."10_fct_templates"
    ADD COLUMN IF NOT EXISTS org_id UUID NULL;

-- Drop old unique constraint and add new one that allows per-org overrides
ALTER TABLE "03_notifications"."10_fct_templates"
    DROP CONSTRAINT IF EXISTS uq_10_fct_templates_code;

-- NULL-safe unique: one platform template + one per-org override per code
CREATE UNIQUE INDEX IF NOT EXISTS uq_10_fct_templates_code_org
    ON "03_notifications"."10_fct_templates" (
        tenant_key, code, COALESCE(org_id, '00000000-0000-0000-0000-000000000000'::uuid)
    )
    WHERE is_deleted = FALSE;

-- Index for org-specific template lookups
CREATE INDEX IF NOT EXISTS idx_10_fct_templates_org
    ON "03_notifications"."10_fct_templates" (org_id)
    WHERE org_id IS NOT NULL AND is_active = TRUE AND is_deleted = FALSE;

-- ── Add static_variables to broadcasts ──────────────────────────────────────

ALTER TABLE "03_notifications"."12_fct_broadcasts"
    ADD COLUMN IF NOT EXISTS static_variables JSONB NOT NULL DEFAULT '{}'::jsonb;
