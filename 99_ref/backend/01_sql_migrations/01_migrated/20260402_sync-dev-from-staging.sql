-- =============================================================================
-- Migration: 20260402_sync-dev-from-staging.sql
-- Description: Fix dev-side schema mismatches to match staging (the canonical baseline).
--              Run on DEV only. Staging already has all of this correctly.
-- =============================================================================

-- UP ==========================================================================

-- -----------------------------------------------------------------------------
-- SECTION 1: 14_risk_registry — add version column + fix vw_risk_detail
--            Staging has version column on 10_fct_risks; dev does not.
-- -----------------------------------------------------------------------------

ALTER TABLE "14_risk_registry"."10_fct_risks"
    ADD COLUMN IF NOT EXISTS version integer DEFAULT 1 NOT NULL;

-- Recreate view to use the clean single-pass query (drop old double-join version)
DROP VIEW IF EXISTS "14_risk_registry"."40_vw_risk_detail";

CREATE VIEW "14_risk_registry"."40_vw_risk_detail" AS
 SELECT r.id,
    r.tenant_key,
    r.risk_code,
    r.org_id,
    r.workspace_id,
    r.risk_category_code,
    rc.name AS category_name,
    r.risk_level_code,
    rl.name AS risk_level_name,
    rl.color_hex AS risk_level_color,
    r.treatment_type_code,
    rt.name AS treatment_type_name,
    r.source_type,
    r.risk_status,
    r.is_active,
    r.is_deleted,
    r.created_at,
    r.updated_at,
    r.created_by,
    r.version,
    p_title.property_value AS title,
    p_desc.property_value AS description,
    p_notes.property_value AS notes,
    p_owner.property_value AS owner_user_id,
    p_impact.property_value AS business_impact,
    ( SELECT ra.risk_score
           FROM "14_risk_registry"."32_trx_risk_assessments" ra
          WHERE ((ra.risk_id = r.id) AND ((ra.assessment_type)::text = 'inherent'::text))
          ORDER BY ra.assessed_at DESC
         LIMIT 1) AS inherent_risk_score,
    ( SELECT ra.risk_score
           FROM "14_risk_registry"."32_trx_risk_assessments" ra
          WHERE ((ra.risk_id = r.id) AND ((ra.assessment_type)::text = 'residual'::text))
          ORDER BY ra.assessed_at DESC
         LIMIT 1) AS residual_risk_score,
    ( SELECT count(*) AS count
           FROM "14_risk_registry"."30_lnk_risk_control_mappings" m
          WHERE (m.risk_id = r.id)) AS linked_control_count,
    ( SELECT tp.plan_status
           FROM "14_risk_registry"."11_fct_risk_treatment_plans" tp
          WHERE ((tp.risk_id = r.id) AND (tp.is_deleted = false))
         LIMIT 1) AS treatment_plan_status,
    ( SELECT (tp.target_date)::text AS target_date
           FROM "14_risk_registry"."11_fct_risk_treatment_plans" tp
          WHERE ((tp.risk_id = r.id) AND (tp.is_deleted = false))
         LIMIT 1) AS treatment_plan_target_date
   FROM (((((((("14_risk_registry"."10_fct_risks" r
     LEFT JOIN "14_risk_registry"."02_dim_risk_categories" rc ON (((rc.code)::text = (r.risk_category_code)::text)))
     LEFT JOIN "14_risk_registry"."04_dim_risk_levels" rl ON (((rl.code)::text = (r.risk_level_code)::text)))
     LEFT JOIN "14_risk_registry"."03_dim_risk_treatment_types" rt ON (((rt.code)::text = (r.treatment_type_code)::text)))
     LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_title ON (((p_title.risk_id = r.id) AND ((p_title.property_key)::text = 'title'::text))))
     LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_desc ON (((p_desc.risk_id = r.id) AND ((p_desc.property_key)::text = 'description'::text))))
     LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_notes ON (((p_notes.risk_id = r.id) AND ((p_notes.property_key)::text = 'notes'::text))))
     LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_owner ON (((p_owner.risk_id = r.id) AND ((p_owner.property_key)::text = 'owner_user_id'::text))))
     LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_impact ON (((p_impact.risk_id = r.id) AND ((p_impact.property_key)::text = 'business_impact'::text))))
  WHERE (r.is_deleted = false);

-- -----------------------------------------------------------------------------
-- SECTION 2: 41_fct_risk_questionnaire_responses — widen response_status,
--            fix timestamp types, rename constraint
-- -----------------------------------------------------------------------------

-- Widen response_status from varchar(30) to varchar(50) (staging has 50)
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    ALTER COLUMN response_status TYPE character varying(50);

-- Fix completed_at timestamp type from with time zone to without time zone
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    ALTER COLUMN completed_at TYPE timestamp without time zone
    USING completed_at AT TIME ZONE 'UTC';

-- Fix created_at / updated_at types
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    ALTER COLUMN created_at TYPE timestamp without time zone
    USING created_at AT TIME ZONE 'UTC',
    ALTER COLUMN created_at DROP DEFAULT,
    ALTER COLUMN updated_at TYPE timestamp without time zone
    USING updated_at AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at DROP DEFAULT;

-- Rename CHECK constraint to match staging convention
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    DROP CONSTRAINT IF EXISTS ck_41_response_status;
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    ADD CONSTRAINT ck_41_fct_risk_questionnaire_responses_status
        CHECK (((response_status)::text = ANY ((ARRAY['draft'::character varying, 'completed'::character varying])::text[])));

-- -----------------------------------------------------------------------------
-- SECTION 3: 39_lnk_risk_questionnaire_assignments — fix timestamp types,
--            rename constraint
-- -----------------------------------------------------------------------------

-- Fix created_at / updated_at types from with time zone to without time zone
ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    ALTER COLUMN created_at TYPE timestamp without time zone
    USING created_at AT TIME ZONE 'UTC',
    ALTER COLUMN created_at DROP DEFAULT,
    ALTER COLUMN updated_at TYPE timestamp without time zone
    USING updated_at AT TIME ZONE 'UTC',
    ALTER COLUMN updated_at DROP DEFAULT;

-- Rename CHECK constraint to match staging convention
ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    DROP CONSTRAINT IF EXISTS ck_39_assignment_scope;
ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    ADD CONSTRAINT ck_39_lnk_risk_questionnaire_assignments_scope
        CHECK (((assignment_scope)::text = ANY (ARRAY[('platform'::character varying)::text, ('org'::character varying)::text, ('workspace'::character varying)::text])));

-- Rename UNIQUE constraint to match staging
ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
    DROP CONSTRAINT IF EXISTS uq_38_questionnaire_version;
ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
    ADD CONSTRAINT uq_38_vrs_risk_questionnaire_versions_num
        UNIQUE (questionnaire_id, version_number);

-- -----------------------------------------------------------------------------
-- SECTION 4: 15_sandbox.43_dtl_dataset_records — widen record_name, drop defaults
--            Staging has varchar(200) with no default; dev has varchar(120) default ''
-- -----------------------------------------------------------------------------

ALTER TABLE "15_sandbox"."43_dtl_dataset_records"
    ALTER COLUMN record_name TYPE character varying(200),
    ALTER COLUMN record_name DROP DEFAULT,
    ALTER COLUMN description DROP DEFAULT;

-- -----------------------------------------------------------------------------
-- SECTION 5: grc_role_code CHECK — align dev to staging's canonical values
--            Staging: grc_lead, grc_sme, grc_engineer, grc_ciso,
--                     grc_lead_auditor, grc_staff_auditor, grc_vendor
--            Dev:     grc_practitioner (instead of grc_lead + grc_sme)
-- -----------------------------------------------------------------------------

ALTER TABLE "03_auth_manage"."47_fct_grc_role_assignments"
    DROP CONSTRAINT IF EXISTS chk_47_grc_ra_role_code;
ALTER TABLE "03_auth_manage"."47_fct_grc_role_assignments"
    ADD CONSTRAINT chk_47_grc_ra_role_code
        CHECK (((grc_role_code)::text = ANY ((ARRAY[
            'grc_lead'::character varying,
            'grc_sme'::character varying,
            'grc_engineer'::character varying,
            'grc_ciso'::character varying,
            'grc_lead_auditor'::character varying,
            'grc_staff_auditor'::character varying,
            'grc_vendor'::character varying
        ])::text[])));

-- -----------------------------------------------------------------------------
-- SECTION 6: 03_auth_manage — add notification performance indexes to dev
--            (these exist in staging but not dev — add them to dev as well)
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_expires
    ON "03_auth_manage"."46_fct_api_keys" USING btree (expires_at)
    WHERE ((expires_at IS NOT NULL) AND (revoked_at IS NULL) AND (is_deleted = false));

-- Upgrade api_keys indexes to partial (match staging)
DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_key_hash;
CREATE INDEX idx_46_fct_api_keys_key_hash
    ON "03_auth_manage"."46_fct_api_keys" USING btree (key_hash)
    WHERE (is_deleted = false);

DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_user_tenant;
CREATE INDEX idx_46_fct_api_keys_user_tenant
    ON "03_auth_manage"."46_fct_api_keys" USING btree (user_id, tenant_key)
    WHERE (is_deleted = false);

-- Add notification indexes to dev
CREATE INDEX IF NOT EXISTS idx_12_fct_broadcasts_tenant
    ON "03_notifications"."12_fct_broadcasts" USING btree (tenant_key, created_at DESC)
    WHERE (is_deleted = false);

CREATE INDEX IF NOT EXISTS idx_17_lnk_prefs_tenant_scope
    ON "03_notifications"."17_lnk_user_notification_preferences" USING btree (tenant_key, scope_level);

CREATE INDEX IF NOT EXISTS idx_20_trx_queue_audit_event
    ON "03_notifications"."20_trx_notification_queue" USING btree (source_audit_event_id)
    WHERE (source_audit_event_id IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_20_trx_queue_status_scheduled
    ON "03_notifications"."20_trx_notification_queue" USING btree (status_code, scheduled_at)
    WHERE ((status_code)::text = ANY ((ARRAY['queued'::character varying, 'failed'::character varying])::text[]));

CREATE INDEX IF NOT EXISTS idx_20_trx_queue_tenant_user
    ON "03_notifications"."20_trx_notification_queue" USING btree (tenant_key, user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_21_trx_delivery_log_occurred
    ON "03_notifications"."21_trx_delivery_log" USING btree (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_22_trx_tracking_events_occurred
    ON "03_notifications"."22_trx_tracking_events" USING btree (occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_25_fct_releases_date
    ON "03_notifications"."25_fct_releases" USING btree (release_date DESC NULLS LAST)
    WHERE (is_deleted = false);

CREATE INDEX IF NOT EXISTS idx_26_fct_incidents_started
    ON "03_notifications"."26_fct_incidents" USING btree (started_at DESC)
    WHERE (is_deleted = false);

-- Add task criteria index to dev
CREATE INDEX IF NOT EXISTS idx_12_fct_task_criteria_task
    ON "08_tasks"."12_fct_task_criteria" USING btree (task_id)
    WHERE (is_deleted = false);

-- Add sandbox run FKs to dev
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    DROP CONSTRAINT IF EXISTS fk_25_trx_sandbox_runs_dataset;
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    ADD CONSTRAINT fk_25_trx_sandbox_runs_dataset
        FOREIGN KEY (dataset_id) REFERENCES "15_sandbox"."21_fct_datasets"(id);

ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    DROP CONSTRAINT IF EXISTS fk_25_trx_sandbox_runs_session;
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    ADD CONSTRAINT fk_25_trx_sandbox_runs_session
        FOREIGN KEY (live_session_id) REFERENCES "15_sandbox"."28_fct_live_sessions"(id);

-- Rename task criteria PK to match staging convention
ALTER TABLE "08_tasks"."12_fct_task_criteria"
    DROP CONSTRAINT IF EXISTS "12_fct_task_criteria_pkey";
ALTER TABLE "08_tasks"."12_fct_task_criteria"
    ADD CONSTRAINT pk_12_fct_task_criteria PRIMARY KEY (id);

-- Align FK ON DELETE behavior to match staging on api_keys
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    DROP CONSTRAINT IF EXISTS fk_46_fct_api_keys_status_id;
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    ADD CONSTRAINT fk_46_fct_api_keys_status_id
        FOREIGN KEY (status_id) REFERENCES "03_auth_manage"."45_dim_api_key_statuses"(id) ON DELETE RESTRICT;

ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    DROP CONSTRAINT IF EXISTS fk_46_fct_api_keys_user_id;
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    ADD CONSTRAINT fk_46_fct_api_keys_user_id
        FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;

-- DOWN ========================================================================

-- Reverse version column on 10_fct_risks
ALTER TABLE "14_risk_registry"."10_fct_risks"
    DROP COLUMN IF EXISTS version;

-- Restore old vw_risk_detail (double-join version — use the staging view as baseline)
-- (omitted: restoring broken view is not useful)

-- Restore response_status width
ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    ALTER COLUMN response_status TYPE character varying(30);

-- Restore grc_role_code CHECK to dev's original values
ALTER TABLE "03_auth_manage"."47_fct_grc_role_assignments"
    DROP CONSTRAINT IF EXISTS chk_47_grc_ra_role_code;
ALTER TABLE "03_auth_manage"."47_fct_grc_role_assignments"
    ADD CONSTRAINT chk_47_grc_ra_role_code
        CHECK (((grc_role_code)::text = ANY ((ARRAY[
            'grc_practitioner'::character varying,
            'grc_engineer'::character varying,
            'grc_ciso'::character varying,
            'grc_lead_auditor'::character varying,
            'grc_staff_auditor'::character varying,
            'grc_vendor'::character varying
        ])::text[])));

-- Remove indexes added to dev
DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_expires;
DROP INDEX IF EXISTS "03_notifications".idx_12_fct_broadcasts_tenant;
DROP INDEX IF EXISTS "03_notifications".idx_17_lnk_prefs_tenant_scope;
DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_audit_event;
DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_status_scheduled;
DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_tenant_user;
DROP INDEX IF EXISTS "03_notifications".idx_21_trx_delivery_log_occurred;
DROP INDEX IF EXISTS "03_notifications".idx_22_trx_tracking_events_occurred;
DROP INDEX IF EXISTS "03_notifications".idx_25_fct_releases_date;
DROP INDEX IF EXISTS "03_notifications".idx_26_fct_incidents_started;
DROP INDEX IF EXISTS "08_tasks".idx_12_fct_task_criteria_task;
