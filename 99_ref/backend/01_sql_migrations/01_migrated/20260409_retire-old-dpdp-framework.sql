-- =============================================================================
-- Migration: 20260409_retire-old-dpdp-framework.sql
-- Description: Retire the old DPDP framework (dpdp_3, bf4ae427) from the global
--              marketplace. It has been superseded by dpdp_4 (490f2f7d, 77
--              controls) which is the new authoritative DPDP entry.
--
--              On staging/prod: the old dpdp_3 is sentinel-scoped + marketplace
--                               visible. This migration hides and soft-deletes it.
--              On dev:          the old dpdp_3 is already in a real workspace
--                               scope and not the global entry, so hiding/deleting
--                               it is also the desired outcome.
-- =============================================================================

-- UP ==========================================================================

UPDATE "05_grc_library"."10_fct_frameworks"
SET
    is_marketplace_visible = FALSE,
    is_deleted             = TRUE,
    deleted_at             = COALESCE(deleted_at, NOW())
WHERE id = 'bf4ae427-bdbd-469d-9731-2c9ce5f37db4';

-- DOWN ========================================================================

-- UPDATE "05_grc_library"."10_fct_frameworks"
-- SET is_marketplace_visible = TRUE, is_deleted = FALSE, deleted_at = NULL
-- WHERE id = 'bf4ae427-bdbd-469d-9731-2c9ce5f37db4';
