-- ============================================================================
-- 20260401_sync-dev-to-staging.sql
-- Brings dev database schema to parity with staging.
-- Fully idempotent — safe to run on staging where these objects already exist.
-- ============================================================================


-- ── 03_auth_manage ───────────────────────────────────────────────────────────

-- 45_dim_api_key_statuses: widen code and name columns
ALTER TABLE "03_auth_manage"."45_dim_api_key_statuses"
    ALTER COLUMN code TYPE character varying(50),
    ALTER COLUMN name TYPE character varying(100);

-- 46_fct_api_keys: widen name/key_prefix, make scopes nullable
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    ALTER COLUMN name TYPE character varying(255),
    ALTER COLUMN key_prefix TYPE character varying(16);

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."46_fct_api_keys" ALTER COLUMN scopes DROP NOT NULL;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."46_fct_api_keys" ALTER COLUMN scopes DROP DEFAULT;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."46_fct_api_keys"
        ADD CONSTRAINT fk_46_fct_api_keys_revoked_by
            FOREIGN KEY (revoked_by) REFERENCES "03_auth_manage"."03_fct_users"(id) ON DELETE RESTRICT;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- 47_lnk_grc_role_assignments: widen grc_role_code, add workspace_id, SET NOT NULL on assigned_by
-- v_grc_team depends on grc_role_code — drop then recreate after widening
-- NOTE: Table may not exist on envs that missed create-grc-role-assignments.sql.
--       All statements below are guarded; full-prod-sync.sql creates the table first.
DROP VIEW IF EXISTS "03_auth_manage".v_grc_team;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        ALTER COLUMN grc_role_code TYPE character varying(60);
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        ADD COLUMN IF NOT EXISTS workspace_id uuid;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    UPDATE "03_auth_manage"."47_lnk_grc_role_assignments"
       SET assigned_by = user_id
     WHERE assigned_by IS NULL;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        ALTER COLUMN assigned_by SET NOT NULL;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
        DROP CONSTRAINT IF EXISTS chk_47_grc_ra_role_code;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

-- Recreate view — only if the underlying table now exists
DO $$ BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = '03_auth_manage'
          AND table_name   = '47_lnk_grc_role_assignments'
    ) THEN
        EXECUTE $view$
            CREATE OR REPLACE VIEW "03_auth_manage".v_grc_team AS
             SELECT ra.id AS assignment_id,
                ra.org_id,
                ra.user_id,
                ra.grc_role_code,
                r.name AS role_name,
                r.description AS role_description,
                email.property_value AS email,
                dn.property_value AS display_name,
                ra.assigned_by,
                ra.assigned_at,
                ra.revoked_at,
                ra.created_at,
                ( SELECT count(*) AS count
                       FROM "03_auth_manage"."48_lnk_grc_access_grants" g
                      WHERE ((g.grc_role_assignment_id = ra.id) AND (g.revoked_at IS NULL))) AS active_grant_count
               FROM ((("03_auth_manage"."47_lnk_grc_role_assignments" ra
                 JOIN "03_auth_manage"."16_fct_roles" r ON ((((r.code)::text = (ra.grc_role_code)::text) AND (r.is_deleted = false) AND ((r.role_level_code)::text = 'workspace'::text))))
                 LEFT JOIN "03_auth_manage"."05_dtl_user_properties" email ON (((email.user_id = ra.user_id) AND ((email.property_key)::text = 'email'::text))))
                 LEFT JOIN "03_auth_manage"."05_dtl_user_properties" dn ON (((dn.user_id = ra.user_id) AND ((dn.property_key)::text = 'display_name'::text))))
              WHERE (ra.revoked_at IS NULL)
        $view$;
    END IF;
END $$;

-- 48_lnk_grc_access_grants: widen scope_type, drop old CHECK, add FK
DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants"
        ALTER COLUMN scope_type TYPE character varying(30);
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants"
        DROP CONSTRAINT IF EXISTS chk_48_grc_ag_scope_type;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants"
        ADD CONSTRAINT "48_lnk_grc_access_grants_grc_role_assignment_id_fkey"
            FOREIGN KEY (grc_role_assignment_id)
            REFERENCES "03_auth_manage"."47_lnk_grc_role_assignments"(id);
EXCEPTION WHEN undefined_table THEN NULL;
WHEN duplicate_object THEN NULL; END $$;


-- ── 03_notifications ─────────────────────────────────────────────────────────

DO $$ BEGIN
    ALTER TABLE "03_notifications"."12_fct_broadcasts"
        ADD CONSTRAINT ck_12_fct_broadcasts_severity
            CHECK (
                (severity IS NULL)
                OR ((severity)::text = ANY (ARRAY[
                    'critical'::text, 'high'::text, 'medium'::text,
                    'low'::text, 'info'::text
                ]))
            );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ── 08_tasks ─────────────────────────────────────────────────────────────────

UPDATE "08_tasks"."12_fct_task_criteria" SET sort_order = 0     WHERE sort_order IS NULL;
UPDATE "08_tasks"."12_fct_task_criteria" SET is_deleted = false  WHERE is_deleted IS NULL;
UPDATE "08_tasks"."12_fct_task_criteria" SET created_at = now()  WHERE created_at IS NULL;
UPDATE "08_tasks"."12_fct_task_criteria" SET updated_at = now()  WHERE updated_at IS NULL;

DO $$ BEGIN
    ALTER TABLE "08_tasks"."12_fct_task_criteria"
        ALTER COLUMN sort_order SET NOT NULL,
        ALTER COLUMN is_deleted SET NOT NULL,
        ALTER COLUMN created_at SET NOT NULL,
        ALTER COLUMN updated_at SET NOT NULL;
EXCEPTION WHEN others THEN NULL; END $$;

ALTER TABLE "08_tasks"."12_fct_task_criteria"
    DROP CONSTRAINT IF EXISTS "12_fct_task_criteria_task_id_fkey";

DO $$ BEGIN
    ALTER TABLE "08_tasks"."12_fct_task_criteria"
        ADD CONSTRAINT fk_12_fct_task_criteria_task
            FOREIGN KEY (task_id) REFERENCES "08_tasks"."10_fct_tasks"(id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ── 08_comments ──────────────────────────────────────────────────────────────

DO $$ BEGIN
    ALTER TABLE "08_comments"."01_fct_comments"
        ADD CONSTRAINT chk_01_fct_comments_entity_type
            CHECK (entity_type = ANY (ARRAY[
                'task'::text, 'risk'::text, 'control'::text, 'framework'::text,
                'evidence_template'::text, 'test'::text, 'requirement'::text,
                'feedback_ticket'::text
            ]));
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ── 12_engagements ───────────────────────────────────────────────────────────

ALTER TABLE "12_engagements"."21_trx_auditor_verifications"
    ADD COLUMN IF NOT EXISTS observations    text,
    ADD COLUMN IF NOT EXISTS finding_details text;


-- ── 14_risk_registry ─────────────────────────────────────────────────────────

ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
    ALTER COLUMN name           TYPE character varying(255),
    ALTER COLUMN intended_scope TYPE character varying(50),
    ALTER COLUMN current_status TYPE character varying(50);

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
        ALTER COLUMN intended_scope SET DEFAULT 'platform';
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
        ALTER COLUMN latest_version_number SET DEFAULT 0;
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
        ALTER COLUMN created_at TYPE timestamp without time zone USING created_at AT TIME ZONE 'UTC',
        ALTER COLUMN updated_at TYPE timestamp without time zone USING updated_at AT TIME ZONE 'UTC',
        ALTER COLUMN deleted_at TYPE timestamp without time zone USING deleted_at AT TIME ZONE 'UTC';
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
        RENAME CONSTRAINT ck_37_questionnaire_scope TO ck_37_fct_risk_questionnaires_scope;
EXCEPTION WHEN undefined_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
        RENAME CONSTRAINT ck_37_questionnaire_status TO ck_37_fct_risk_questionnaires_status;
EXCEPTION WHEN undefined_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."37_fct_risk_questionnaires"
        ADD CONSTRAINT fk_37_fct_risk_questionnaires_active_version
            FOREIGN KEY (active_version_id)
            REFERENCES "14_risk_registry"."38_vrs_risk_questionnaire_versions"(id)
            ON DELETE SET NULL;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
    ALTER COLUMN version_status TYPE character varying(50),
    ALTER COLUMN version_label  TYPE character varying(255);

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
        ALTER COLUMN published_at TYPE timestamp without time zone USING published_at AT TIME ZONE 'UTC',
        ALTER COLUMN created_at   TYPE timestamp without time zone USING created_at   AT TIME ZONE 'UTC',
        ALTER COLUMN updated_at   TYPE timestamp without time zone USING updated_at   AT TIME ZONE 'UTC';
EXCEPTION WHEN others THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
        RENAME CONSTRAINT ck_38_version_status TO ck_38_vrs_risk_questionnaire_versions_status;
EXCEPTION WHEN undefined_object THEN NULL; END $$;

DO $$ BEGIN
    ALTER TABLE "14_risk_registry"."38_vrs_risk_questionnaire_versions"
        RENAME CONSTRAINT fk_38_version_questionnaire
        TO fk_38_vrs_risk_questionnaire_versions_questionnaire;
EXCEPTION WHEN undefined_object THEN NULL; END $$;

ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    ALTER COLUMN assignment_scope TYPE character varying(50);

DO $$ BEGIN ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    RENAME CONSTRAINT fk_39_assignment_org TO fk_39_lnk_risk_questionnaire_assignments_org;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    RENAME CONSTRAINT fk_39_assignment_version TO fk_39_lnk_risk_questionnaire_assignments_version;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE "14_risk_registry"."39_lnk_risk_questionnaire_assignments"
    RENAME CONSTRAINT fk_39_assignment_workspace TO fk_39_lnk_risk_questionnaire_assignments_workspace;
EXCEPTION WHEN undefined_object THEN NULL; END $$;

DO $$ BEGIN ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    RENAME CONSTRAINT fk_41_response_org TO fk_41_fct_risk_questionnaire_responses_org;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    RENAME CONSTRAINT fk_41_response_version TO fk_41_fct_risk_questionnaire_responses_version;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN ALTER TABLE "14_risk_registry"."41_fct_risk_questionnaire_responses"
    RENAME CONSTRAINT fk_41_response_workspace TO fk_41_fct_risk_questionnaire_responses_workspace;
EXCEPTION WHEN undefined_object THEN NULL; END $$;

-- Questionnaire indexes
CREATE INDEX IF NOT EXISTS idx_37_fct_risk_questionnaires_active_version
    ON "14_risk_registry"."37_fct_risk_questionnaires" (active_version_id)
    WHERE active_version_id IS NOT NULL AND is_deleted = false;
CREATE INDEX IF NOT EXISTS idx_37_fct_risk_questionnaires_status
    ON "14_risk_registry"."37_fct_risk_questionnaires" (current_status)
    WHERE is_deleted = false;
CREATE INDEX IF NOT EXISTS idx_37_fct_risk_questionnaires_tenant
    ON "14_risk_registry"."37_fct_risk_questionnaires" (tenant_key)
    WHERE is_deleted = false;
CREATE INDEX IF NOT EXISTS idx_38_vrs_risk_questionnaire_versions_content
    ON "14_risk_registry"."38_vrs_risk_questionnaire_versions" USING gin (content_jsonb);
CREATE INDEX IF NOT EXISTS idx_38_vrs_risk_questionnaire_versions_questionnaire
    ON "14_risk_registry"."38_vrs_risk_questionnaire_versions" (questionnaire_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_38_vrs_risk_questionnaire_versions_status
    ON "14_risk_registry"."38_vrs_risk_questionnaire_versions" (version_status);
CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_org
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (org_id)
    WHERE is_active = true AND org_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_scope
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (tenant_key, assignment_scope)
    WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_tenant
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (tenant_key)
    WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_39_lnk_risk_questionnaire_assignments_workspace
    ON "14_risk_registry"."39_lnk_risk_questionnaire_assignments" (workspace_id)
    WHERE is_active = true AND workspace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_answers
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" USING gin (answers_jsonb);
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_lookup
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses"
    (tenant_key, org_id, questionnaire_version_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_org
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (org_id);
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_tenant
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (tenant_key);
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_version
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (questionnaire_version_id);
CREATE INDEX IF NOT EXISTS idx_41_fct_risk_questionnaire_responses_workspace
    ON "14_risk_registry"."41_fct_risk_questionnaire_responses" (workspace_id)
    WHERE workspace_id IS NOT NULL;

DROP INDEX IF EXISTS "14_risk_registry".idx_37_questionnaire_tenant;
DROP INDEX IF EXISTS "14_risk_registry".idx_38_version_questionnaire;
DROP INDEX IF EXISTS "14_risk_registry".idx_39_assignment_scope;
DROP INDEX IF EXISTS "14_risk_registry".idx_41_response_scope;


-- ── 15_sandbox ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "15_sandbox"."80_fct_global_libraries" (
    id                   uuid DEFAULT gen_random_uuid() NOT NULL,
    source_library_id    uuid NOT NULL,
    source_org_id        uuid NOT NULL,
    global_code          character varying(100) NOT NULL,
    global_name          character varying(255) NOT NULL,
    description          text,
    category_code        character varying(50),
    connector_type_codes text[] DEFAULT '{}'::text[] NOT NULL,
    curator_user_id      uuid NOT NULL,
    publish_status       character varying(20) DEFAULT 'draft'::character varying NOT NULL,
    is_featured          boolean DEFAULT false NOT NULL,
    download_count       integer DEFAULT 0 NOT NULL,
    version_number       integer DEFAULT 1 NOT NULL,
    published_at         timestamp with time zone,
    created_at           timestamp with time zone DEFAULT now() NOT NULL,
    updated_at           timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_publish_status CHECK (((publish_status)::text = ANY (
        (ARRAY['draft'::character varying, 'review'::character varying,
               'published'::character varying, 'deprecated'::character varying])::text[]
    )))
);
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '80_fct_global_libraries_pkey') THEN
        ALTER TABLE "15_sandbox"."80_fct_global_libraries" ADD CONSTRAINT "80_fct_global_libraries_pkey" PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '80_fct_global_libraries_global_code_key') THEN
        ALTER TABLE "15_sandbox"."80_fct_global_libraries" ADD CONSTRAINT "80_fct_global_libraries_global_code_key" UNIQUE (global_code);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '80_fct_global_libraries_source_library_id_fkey') THEN
        ALTER TABLE "15_sandbox"."80_fct_global_libraries" ADD CONSTRAINT "80_fct_global_libraries_source_library_id_fkey"
            FOREIGN KEY (source_library_id) REFERENCES "15_sandbox"."29_fct_libraries"(id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_global_libraries_category
    ON "15_sandbox"."80_fct_global_libraries" (category_code);
CREATE INDEX IF NOT EXISTS idx_global_libraries_status
    ON "15_sandbox"."80_fct_global_libraries" (publish_status);

CREATE TABLE IF NOT EXISTS "15_sandbox"."81_lnk_org_library_subscriptions" (
    id                  uuid DEFAULT gen_random_uuid() NOT NULL,
    org_id              uuid NOT NULL,
    global_library_id   uuid NOT NULL,
    subscribed_by       uuid NOT NULL,
    subscribed_version  integer NOT NULL,
    local_library_id    uuid,
    auto_update         boolean DEFAULT true NOT NULL,
    subscribed_at       timestamp with time zone DEFAULT now() NOT NULL
);
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '81_lnk_org_library_subscriptions_pkey') THEN
        ALTER TABLE "15_sandbox"."81_lnk_org_library_subscriptions" ADD CONSTRAINT "81_lnk_org_library_subscriptions_pkey" PRIMARY KEY (id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '81_lnk_org_library_subscriptions_org_id_global_library_id_key') THEN
        ALTER TABLE "15_sandbox"."81_lnk_org_library_subscriptions" ADD CONSTRAINT "81_lnk_org_library_subscriptions_org_id_global_library_id_key"
            UNIQUE (org_id, global_library_id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '81_lnk_org_library_subscriptions_global_library_id_fkey') THEN
        ALTER TABLE "15_sandbox"."81_lnk_org_library_subscriptions" ADD CONSTRAINT "81_lnk_org_library_subscriptions_global_library_id_fkey"
            FOREIGN KEY (global_library_id) REFERENCES "15_sandbox"."80_fct_global_libraries"(id);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '81_lnk_org_library_subscriptions_local_library_id_fkey') THEN
        ALTER TABLE "15_sandbox"."81_lnk_org_library_subscriptions" ADD CONSTRAINT "81_lnk_org_library_subscriptions_local_library_id_fkey"
            FOREIGN KEY (local_library_id) REFERENCES "15_sandbox"."29_fct_libraries"(id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_org_subscriptions_global
    ON "15_sandbox"."81_lnk_org_library_subscriptions" (global_library_id);
CREATE INDEX IF NOT EXISTS idx_org_subscriptions_org
    ON "15_sandbox"."81_lnk_org_library_subscriptions" (org_id);

DO $$ BEGIN
    CREATE TRIGGER trg_25_immutable
        BEFORE UPDATE ON "15_sandbox"."25_trx_sandbox_runs"
        FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_created_brin
    ON "15_sandbox"."25_trx_sandbox_runs" USING brin (created_at);
CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_dataset
    ON "15_sandbox"."25_trx_sandbox_runs" (dataset_id)
    WHERE dataset_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_exec_status
    ON "15_sandbox"."25_trx_sandbox_runs" (execution_status_code);
CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_session
    ON "15_sandbox"."25_trx_sandbox_runs" (live_session_id, created_at DESC)
    WHERE live_session_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_25_trx_runs_org_signal_result
    ON "15_sandbox"."25_trx_sandbox_runs" (org_id, signal_id, result_code, created_at DESC);


-- ── 20_ai ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "20_ai"."19_fct_attachments" (
    id              uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_key      character varying(100) NOT NULL,
    user_id         uuid NOT NULL,
    filename        character varying(500) NOT NULL,
    content_type    character varying(200),
    file_size_bytes integer,
    extracted_text  text,
    status_code     character varying(50) DEFAULT 'pending'::character varying NOT NULL,
    error_message   text,
    is_deleted      boolean DEFAULT false NOT NULL,
    created_at      timestamp with time zone DEFAULT now() NOT NULL,
    updated_at      timestamp with time zone DEFAULT now() NOT NULL,
    created_by      uuid,
    updated_by      uuid,
    CONSTRAINT "19_fct_attachments_status_code_check" CHECK (((status_code)::text = ANY (
        (ARRAY['pending'::character varying, 'processing'::character varying,
               'ready'::character varying, 'failed'::character varying])::text[]
    )))
);
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '19_fct_attachments_pkey') THEN
        ALTER TABLE "20_ai"."19_fct_attachments" ADD CONSTRAINT "19_fct_attachments_pkey" PRIMARY KEY (id);
    END IF;
END $$;
CREATE INDEX IF NOT EXISTS idx_19_fct_attachments_status
    ON "20_ai"."19_fct_attachments" (status_code)
    WHERE (status_code)::text = 'ready';
CREATE INDEX IF NOT EXISTS idx_19_fct_attachments_tenant
    ON "20_ai"."19_fct_attachments" (tenant_key);
CREATE INDEX IF NOT EXISTS idx_19_fct_attachments_user
    ON "20_ai"."19_fct_attachments" (user_id);
