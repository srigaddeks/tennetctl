-- =============================================================================
-- Migration: 20260406_sync-all-envs-schema-parity.sql
-- Description:
--   Brings dev, staging, and prod into full schema parity. Idempotent.
--
--   Fixes applied:
--     1. Creates missing indexes on dev (already exist on staging/prod)
--        - idx_46_fct_api_keys_expires   (03_auth_manage)
--        - idx_12_fct_task_criteria_task  (08_tasks)
--     2. Creates 87_vw_global_control_test_detail view on dev (exists on staging/prod)
--     3. Fixes duplicate/stale comment entity-type CHECK constraints (staging/prod)
--        - Drops old chk_ prefixed duplicate on 01_fct_comments
--        - Replaces ck_ constraint with dev-matching values on both tables
--     4. Fixes stale attachments entity-type CHECK constraint (staging/prod)
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Missing indexes on dev (IF NOT EXISTS = safe on staging/prod)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_expires
    ON "03_auth_manage"."46_fct_api_keys" USING btree (expires_at)
    WHERE (expires_at IS NOT NULL AND revoked_at IS NULL AND is_deleted = false);

CREATE INDEX IF NOT EXISTS idx_12_fct_task_criteria_task
    ON "08_tasks"."12_fct_task_criteria" USING btree (task_id)
    WHERE (is_deleted = false);


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. 87_vw_global_control_test_detail — missing on dev, exists on staging/prod
--    CREATE OR REPLACE is idempotent, so safe everywhere.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "15_sandbox"."87_vw_global_control_test_detail" AS
SELECT
    gt.id,
    gt.global_code,
    gt.connector_type_code,
    ct.name                AS connector_type_name,
    gt.version_number,
    gt.bundle,
    gt.source_signal_id,
    gt.source_policy_id,
    gt.source_library_id,
    gt.source_org_id,
    gt.linked_dataset_code,
    gt.publish_status,
    gt.is_featured,
    gt.download_count,
    gt.signal_count,
    gt.published_by,
    gt.published_at,
    gt.is_active,
    gt.is_deleted,
    gt.created_at,
    gt.updated_at,
    max(CASE WHEN p.property_key = 'name'                 THEN p.property_value END) AS name,
    max(CASE WHEN p.property_key = 'description'          THEN p.property_value END) AS description,
    max(CASE WHEN p.property_key = 'tags'                 THEN p.property_value END) AS tags,
    max(CASE WHEN p.property_key = 'category'             THEN p.property_value END) AS category,
    max(CASE WHEN p.property_key = 'changelog'            THEN p.property_value END) AS changelog,
    max(CASE WHEN p.property_key = 'compliance_references' THEN p.property_value END) AS compliance_references
FROM "15_sandbox"."84_fct_global_control_tests" gt
LEFT JOIN "15_sandbox"."85_dtl_global_control_test_properties" p ON p.test_id = gt.id
LEFT JOIN "15_sandbox"."03_dim_connector_types" ct ON ct.code = gt.connector_type_code
WHERE NOT gt.is_deleted
GROUP BY gt.id, ct.name;


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Fix comment entity-type CHECK constraints
--    Dev has the correct single ck_ constraint with all values.
--    Staging/prod have a duplicate chk_ (stricter) + ck_ (stale, missing 'comment').
--    Target state: single ck_ constraint matching dev.
-- ─────────────────────────────────────────────────────────────────────────────

-- 3a. 01_fct_comments — drop all variants, recreate with dev values
ALTER TABLE "08_comments"."01_fct_comments"
    DROP CONSTRAINT IF EXISTS chk_01_fct_comments_entity_type;

ALTER TABLE "08_comments"."01_fct_comments"
    DROP CONSTRAINT IF EXISTS ck_01_fct_comments_entity_type;

ALTER TABLE "08_comments"."01_fct_comments"
    DROP CONSTRAINT IF EXISTS "01_fct_comments_entity_type_check";

ALTER TABLE "08_comments"."01_fct_comments"
    ADD CONSTRAINT ck_01_fct_comments_entity_type CHECK (
        entity_type IN (
            'task', 'risk', 'control', 'framework',
            'engagement', 'evidence_template', 'test',
            'requirement', 'feedback_ticket',
            'org', 'workspace', 'comment'
        )
    );

-- 3b. 05_trx_comment_views — drop all variants, recreate with dev values
ALTER TABLE "08_comments"."05_trx_comment_views"
    DROP CONSTRAINT IF EXISTS chk_05_trx_comment_views_entity_type;

ALTER TABLE "08_comments"."05_trx_comment_views"
    DROP CONSTRAINT IF EXISTS ck_05_trx_comment_views_entity_type;

ALTER TABLE "08_comments"."05_trx_comment_views"
    DROP CONSTRAINT IF EXISTS "05_trx_comment_views_entity_type_check";

ALTER TABLE "08_comments"."05_trx_comment_views"
    ADD CONSTRAINT ck_05_trx_comment_views_entity_type CHECK (
        entity_type IN (
            'task', 'risk', 'control', 'framework',
            'engagement', 'evidence_template', 'test',
            'requirement', 'feedback_ticket',
            'org', 'workspace', 'comment'
        )
    );


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Fix attachments entity-type CHECK constraint
--    Dev has 'engagement'; staging/prod do not.
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE "09_attachments"."01_fct_attachments"
    DROP CONSTRAINT IF EXISTS ck_01_fct_attachments_entity_type;

ALTER TABLE "09_attachments"."01_fct_attachments"
    DROP CONSTRAINT IF EXISTS "01_fct_attachments_entity_type_check";

ALTER TABLE "09_attachments"."01_fct_attachments"
    ADD CONSTRAINT ck_01_fct_attachments_entity_type CHECK (
        entity_type IN (
            'task', 'risk', 'control', 'framework',
            'engagement', 'evidence_template', 'test',
            'comment', 'requirement', 'feedback_ticket',
            'org', 'workspace'
        )
    );
