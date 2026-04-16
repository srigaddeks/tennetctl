-- =============================================================================
-- Migration: 20260401_seed-engagement-type-and-comment-entity.sql
-- Module:    12_engagements, 08_comments
-- Description: Seeds engagement_type property key in engagement dimensions and
--              adds 'engagement' to the comment entity type CHECK constraint
--              so comments can be attached to audit engagements.
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Seed engagement_type property key (readiness | audit)
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "12_engagements"."03_dim_engagement_property_keys"
    (id, code, name, description, data_type, is_required, sort_order, created_at)
SELECT
    gen_random_uuid(),
    'engagement_type',
    'Engagement Type',
    'Type of engagement: readiness (internal prep) or audit (external verification)',
    'text',
    FALSE,
    100,
    CURRENT_TIMESTAMP
WHERE NOT EXISTS (
    SELECT 1 FROM "12_engagements"."03_dim_engagement_property_keys"
    WHERE code = 'engagement_type'
);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Update comment entity type constraint to include 'engagement'
--    The CHECK constraint on 08_comments.01_fct_comments.entity_type needs
--    to allow 'engagement' as a valid value. Drop and recreate the constraint.
-- ─────────────────────────────────────────────────────────────────────────────

-- Drop the old constraint if it exists (name may vary by environment)
DO $$
BEGIN
    -- Try dropping known constraint names
    BEGIN
        ALTER TABLE "08_comments"."01_fct_comments"
            DROP CONSTRAINT IF EXISTS chk_01_fct_comments_entity_type;
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
    BEGIN
        ALTER TABLE "08_comments"."01_fct_comments"
            DROP CONSTRAINT IF EXISTS "01_fct_comments_entity_type_check";
    EXCEPTION WHEN OTHERS THEN NULL;
    END;
END $$;

-- Recreate with engagement included
ALTER TABLE "08_comments"."01_fct_comments"
    ADD CONSTRAINT chk_01_fct_comments_entity_type CHECK (
        entity_type IN (
            'task', 'risk', 'control', 'framework', 'engagement',
            'evidence_template', 'test', 'requirement', 'feedback_ticket'
        )
    );

COMMENT ON CONSTRAINT chk_01_fct_comments_entity_type
    ON "08_comments"."01_fct_comments"
    IS 'Allowed entity types for comments. Includes engagement for audit workflow messages.';


-- DOWN ========================================================================

-- Revert constraint to exclude engagement
ALTER TABLE "08_comments"."01_fct_comments"
    DROP CONSTRAINT IF EXISTS chk_01_fct_comments_entity_type;

ALTER TABLE "08_comments"."01_fct_comments"
    ADD CONSTRAINT chk_01_fct_comments_entity_type CHECK (
        entity_type IN (
            'task', 'risk', 'control', 'framework',
            'evidence_template', 'test', 'requirement', 'feedback_ticket'
        )
    );

-- Remove engagement_type property key
DELETE FROM "12_engagements"."03_dim_engagement_property_keys"
WHERE code = 'engagement_type';
