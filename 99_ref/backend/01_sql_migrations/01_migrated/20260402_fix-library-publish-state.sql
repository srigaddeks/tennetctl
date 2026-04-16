-- =============================================================================
-- Migration: 20260402_fix-library-publish-state.sql
-- Description: Mark the 2 published framework library entries as marketplace-
--              visible so they appear in the Published Frameworks page.
--              Also ensures workflow notification types exist (idempotent).
-- =============================================================================

-- UP ==========================================================================

-- 1. Mark published frameworks as marketplace-visible
UPDATE "05_grc_library"."10_fct_frameworks"
SET is_marketplace_visible = TRUE, approval_status = 'approved'
WHERE id IN (
    'ce7debe9-796b-48df-a17c-f5e1c91cd012',  -- ISO/IEC 27001:2022
    '08b0e825-13d8-41e8-9456-ee6e8e60e2df'   -- SOC2
) AND is_marketplace_visible = FALSE;

-- DOWN ========================================================================

UPDATE "05_grc_library"."10_fct_frameworks"
SET is_marketplace_visible = FALSE
WHERE id IN (
    'ce7debe9-796b-48df-a17c-f5e1c91cd012',
    '08b0e825-13d8-41e8-9456-ee6e8e60e2df'
);
