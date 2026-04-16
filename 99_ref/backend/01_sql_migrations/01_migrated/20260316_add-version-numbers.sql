-- ============================================================================
-- Add version numbers to GRC entities
-- ============================================================================
-- Adds a `version` INTEGER column (1-based, auto-increments on each update)
-- to controls, risks, and tasks. The audit trail in 40_aud_events already
-- captures the full field-level change history — this column lets the UI
-- display the current version at a glance and filter audit events by version.
-- ============================================================================

-- Controls
ALTER TABLE "05_grc_library"."13_fct_controls"
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Risks
ALTER TABLE "14_risk_registry"."10_fct_risks"
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Tasks
ALTER TABLE "08_tasks"."10_fct_tasks"
    ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1;

-- Framework versions table already tracks version_code as a sequential int,
-- no change needed there.
