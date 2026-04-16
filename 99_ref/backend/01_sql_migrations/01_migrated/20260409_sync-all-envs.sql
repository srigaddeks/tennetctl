-- ============================================================================
-- 20260409_sync-staging-to-dev.sql
-- Brings staging database schema to exact parity with dev.
-- Fully idempotent — safe to run on any environment.
-- ============================================================================


-- ── 03_auth_manage: column defaults ─────────────────────────────────────────

-- 45_dim_api_key_statuses: dev has NO default on id; staging has gen_random_uuid()
ALTER TABLE "03_auth_manage"."45_dim_api_key_statuses"
    ALTER COLUMN id DROP DEFAULT;

-- 46_fct_api_keys: dev has NO defaults on id, created_at, updated_at
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    ALTER COLUMN id DROP DEFAULT,
    ALTER COLUMN created_at DROP DEFAULT,
    ALTER COLUMN updated_at DROP DEFAULT;

-- 47_lnk_grc_role_assignments: dev has NO default on id
DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        ALTER COLUMN id DROP DEFAULT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

-- 48_lnk_grc_access_grants: dev has NO default on id
DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants"
        ALTER COLUMN id DROP DEFAULT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;


-- ── 03_auth_manage: FK ON DELETE RESTRICT alignment ─────────────────────────
-- Dev has ON DELETE RESTRICT on 5 core auth FKs; staging has bare (NO ACTION).
-- RESTRICT and NO ACTION are functionally identical in PG, but we align for
-- exact parity. Drop and re-add with RESTRICT.

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."04_dtl_user_identities"
        DROP CONSTRAINT IF EXISTS fk_04_dtl_user_identities_user_id_03_fct_users;
    ALTER TABLE "03_auth_manage"."04_dtl_user_identities"
        ADD CONSTRAINT fk_04_dtl_user_identities_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."05_dtl_user_credentials"
        DROP CONSTRAINT IF EXISTS fk_05_dtl_user_credentials_user_id_03_fct_users;
    ALTER TABLE "03_auth_manage"."05_dtl_user_credentials"
        ADD CONSTRAINT fk_05_dtl_user_credentials_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."06_trx_auth_sessions"
        DROP CONSTRAINT IF EXISTS fk_06_trx_auth_sessions_user_id_03_fct_users;
    ALTER TABLE "03_auth_manage"."06_trx_auth_sessions"
        ADD CONSTRAINT fk_06_trx_auth_sessions_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."07_trx_login_attempts"
        DROP CONSTRAINT IF EXISTS fk_07_trx_login_attempts_user_id_03_fct_users;
    ALTER TABLE "03_auth_manage"."07_trx_login_attempts"
        ADD CONSTRAINT fk_07_trx_login_attempts_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."08_trx_auth_challenges"
        DROP CONSTRAINT IF EXISTS fk_08_trx_auth_challenges_user_id_03_fct_users;
    ALTER TABLE "03_auth_manage"."08_trx_auth_challenges"
        ADD CONSTRAINT fk_08_trx_auth_challenges_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;
EXCEPTION WHEN undefined_table THEN NULL; END $$;


-- ── 03_auth_manage: API key indexes ─────────────────────────────────────────
-- Dev has partial indexes (WHERE is_deleted = false); staging has full indexes.
-- Also staging has idx_46_fct_api_keys_expires which dev doesn't.
-- Align to dev: partial indexes, no expires index.

DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_key_hash;
CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_key_hash
    ON "03_auth_manage"."46_fct_api_keys" USING btree (key_hash)
    WHERE (is_deleted = false);

DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_user_tenant;
CREATE INDEX IF NOT EXISTS idx_46_fct_api_keys_user_tenant
    ON "03_auth_manage"."46_fct_api_keys" USING btree (user_id, tenant_key)
    WHERE (is_deleted = false);

DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_expires;


-- ── 11_docs: add missing event types to CHECK constraint ────────────────────
-- Dev has 'replaced' and 'reverted' event types; staging doesn't.

ALTER TABLE "11_docs"."04_aud_doc_events"
    DROP CONSTRAINT IF EXISTS "04_aud_doc_events_event_type_check";

ALTER TABLE "11_docs"."04_aud_doc_events"
    ADD CONSTRAINT "04_aud_doc_events_event_type_check"
        CHECK (event_type = ANY (ARRAY[
            'uploaded'::text, 'downloaded'::text, 'deleted'::text,
            'description_updated'::text, 'tags_updated'::text,
            'title_updated'::text, 'version_updated'::text,
            'replaced'::text, 'reverted'::text,
            'virus_scan_completed'::text
        ]));


-- ── 12_engagements: add task_id column to auditor_requests ──────────────────

ALTER TABLE "12_engagements"."20_trx_auditor_requests"
    ADD COLUMN IF NOT EXISTS task_id uuid;

DO $$ BEGIN
    ALTER TABLE "12_engagements"."20_trx_auditor_requests"
        ADD CONSTRAINT "20_trx_auditor_requests_task_id_fkey"
            FOREIGN KEY (task_id) REFERENCES "08_tasks"."10_fct_tasks"(id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ── 14_risk_registry: add DEFAULT now() on timestamps ───────────────────────
-- Dev has DEFAULT now() on created_at/updated_at; staging doesn't.

ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN updated_at SET DEFAULT now();

ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
    ALTER COLUMN created_at SET DEFAULT now(),
    ALTER COLUMN updated_at SET DEFAULT now();


-- ── 15_sandbox: add missing CHECK constraint on runs ────────────────────────
-- Dev is missing ck_25_trx_runs_exec_time but staging has it.
-- This means STAGING is ahead — add it to dev too. We add it here idempotently
-- so both envs match. (The dev migration will also add it.)

DO $$ BEGIN
    ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
        ADD CONSTRAINT ck_25_trx_runs_exec_time
            CHECK ((execution_time_ms IS NULL) OR (execution_time_ms >= 0));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ── 05_grc_library: fix 40_vw_framework_catalog ─────────────────────────────
-- Dev has a JOIN bug (p_pub_type.property_key instead of p_pub_name.property_key)
-- and uses COALESCE for control_count. Staging is correct. Overwrite dev view
-- with the correct staging version. This migration runs on ALL envs so we just
-- CREATE OR REPLACE with the correct definition.

CREATE OR REPLACE VIEW "05_grc_library"."40_vw_framework_catalog" AS
 SELECT f.id,
    f.tenant_key,
    f.framework_code,
    f.framework_type_code,
    ft.name AS type_name,
    f.framework_category_code,
    fc.name AS category_name,
    f.scope_org_id,
    f.scope_workspace_id,
    f.approval_status,
    f.is_marketplace_visible,
    f.is_active,
    f.is_deleted,
    f.created_at,
    f.updated_at,
    f.created_by,
    p_name.property_value AS name,
    p_desc.property_value AS description,
    p_short.property_value AS short_description,
    p_pub_type.property_value AS publisher_type,
    p_pub_name.property_value AS publisher_name,
    p_logo.property_value AS logo_url,
    p_docs.property_value AS documentation_url,
    ( SELECT v.version_code
           FROM "05_grc_library"."11_fct_framework_versions" v
          WHERE v.framework_id = f.id
            AND (v.lifecycle_state)::text = 'published'::text
            AND v.is_deleted = false
          ORDER BY v.created_at DESC
         LIMIT 1) AS latest_version_code,
    ( SELECT count(*) AS count
           FROM "05_grc_library"."13_fct_controls" c
          WHERE c.framework_id = f.id
            AND c.is_deleted = false) AS control_count
   FROM ((((((((("05_grc_library"."10_fct_frameworks" f
     LEFT JOIN "05_grc_library"."02_dim_framework_types" ft
       ON ((ft.code)::text = (f.framework_type_code)::text))
     LEFT JOIN "05_grc_library"."03_dim_framework_categories" fc
       ON ((fc.code)::text = (f.framework_category_code)::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
       ON (p_name.framework_id = f.id AND (p_name.property_key)::text = 'name'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_desc
       ON (p_desc.framework_id = f.id AND (p_desc.property_key)::text = 'description'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_short
       ON (p_short.framework_id = f.id AND (p_short.property_key)::text = 'short_description'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub_type
       ON (p_pub_type.framework_id = f.id AND (p_pub_type.property_key)::text = 'publisher_type'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub_name
       ON (p_pub_name.framework_id = f.id AND (p_pub_name.property_key)::text = 'publisher_name'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_logo
       ON (p_logo.framework_id = f.id AND (p_logo.property_key)::text = 'logo_url'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_docs
       ON (p_docs.framework_id = f.id AND (p_docs.property_key)::text = 'documentation_url'::text))
  WHERE f.is_deleted = false;


-- ── 05_grc_library: fix 44_vw_framework_deployments ─────────────────────────
-- Three-way split: dev has source framework tracking, staging has release notes,
-- prod is minimal. Unify to the staging version (has release notes columns,
-- simplified latest version lookup, no source framework tracking).
-- Must DROP first because dev has extra columns that CREATE OR REPLACE can't remove.

DROP VIEW IF EXISTS "05_grc_library"."44_vw_framework_deployments";

CREATE VIEW "05_grc_library"."44_vw_framework_deployments" AS
 SELECT d.id,
    d.tenant_key,
    (d.org_id)::text AS org_id,
    (d.framework_id)::text AS framework_id,
    (d.deployed_version_id)::text AS deployed_version_id,
    d.deployment_status,
    (d.workspace_id)::text AS workspace_id,
    d.is_active,
    (d.created_at)::text AS created_at,
    (d.updated_at)::text AS updated_at,
    (d.created_by)::text AS created_by,
    f.framework_code,
    f.approval_status,
    f.is_marketplace_visible,
    fp_name.property_value AS framework_name,
    fp_desc.property_value AS framework_description,
    fp_pub.property_value AS publisher_name,
    fp_logo.property_value AS logo_url,
    v.version_code AS deployed_version_code,
    v.lifecycle_state AS deployed_lifecycle_state,
    (latest.id)::text AS latest_version_id,
    latest.version_code AS latest_version_code,
    (latest.id IS DISTINCT FROM d.deployed_version_id) AS has_update,
    latest_notes.property_value AS latest_release_notes,
    latest_severity.property_value AS latest_change_severity,
    latest_summary.property_value AS latest_change_summary
   FROM (((((((((("05_grc_library"."16_fct_framework_deployments" d
     JOIN "05_grc_library"."10_fct_frameworks" f
       ON (f.id = d.framework_id AND f.is_deleted = false))
     JOIN "05_grc_library"."11_fct_framework_versions" v
       ON (v.id = d.deployed_version_id))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_name
       ON (fp_name.framework_id = f.id AND (fp_name.property_key)::text = 'name'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_desc
       ON (fp_desc.framework_id = f.id AND (fp_desc.property_key)::text = 'description'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_pub
       ON (fp_pub.framework_id = f.id AND (fp_pub.property_key)::text = 'publisher_name'::text))
     LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp_logo
       ON (fp_logo.framework_id = f.id AND (fp_logo.property_key)::text = 'logo_url'::text))
     LEFT JOIN LATERAL ( SELECT fv.id, fv.version_code
           FROM "05_grc_library"."11_fct_framework_versions" fv
          WHERE fv.framework_id = d.framework_id
            AND (fv.lifecycle_state)::text = 'published'::text
            AND fv.is_deleted = false
          ORDER BY ((((fv.version_code)::text ~ '^[0-9]+$'::text))::integer) DESC,
                   fv.version_code DESC,
                   fv.created_at DESC
         LIMIT 1) latest ON (true))
     LEFT JOIN "05_grc_library"."21_dtl_version_properties" latest_notes
       ON (latest_notes.framework_version_id = latest.id
           AND (latest_notes.property_key)::text = 'release_notes'::text))
     LEFT JOIN "05_grc_library"."21_dtl_version_properties" latest_severity
       ON (latest_severity.framework_version_id = latest.id
           AND (latest_severity.property_key)::text = 'change_severity_label'::text))
     LEFT JOIN "05_grc_library"."21_dtl_version_properties" latest_summary
       ON (latest_summary.framework_version_id = latest.id
           AND (latest_summary.property_key)::text = 'change_summary'::text));


-- ── 08_tasks: add missing index ─────────────────────────────────────────────
-- Prod has idx_12_fct_task_criteria_task that dev/staging don't.
-- We add it everywhere for consistency.

CREATE INDEX IF NOT EXISTS idx_12_fct_task_criteria_task
    ON "08_tasks"."12_fct_task_criteria" USING btree (task_id)
    WHERE (is_deleted = false);
