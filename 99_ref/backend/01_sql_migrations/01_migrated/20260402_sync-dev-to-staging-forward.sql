-- =============================================================================
-- Migration: 20260402_sync-dev-to-staging-forward.sql
-- Description: Bring staging fully in sync with dev.
--              Adds all objects that exist in dev but not staging.
--              Also removes staging-only objects (indexes/FKs not in dev).
--              Run on STAGING only. Dev already has all of this.
-- =============================================================================

-- UP ==========================================================================

-- -----------------------------------------------------------------------------
-- SECTION 1: 12_engagements — engagement membership tables (missing in staging)
-- -----------------------------------------------------------------------------

-- Dim: membership statuses
CREATE TABLE IF NOT EXISTS "12_engagements"."05_dim_engagement_membership_statuses" (
    code        character varying(30)  NOT NULL,
    name        character varying(100) NOT NULL,
    description text,
    sort_order  integer DEFAULT 0,
    created_at  timestamp with time zone DEFAULT now(),
    CONSTRAINT "05_dim_engagement_membership_statuses_pkey" PRIMARY KEY (code)
);

INSERT INTO "12_engagements"."05_dim_engagement_membership_statuses"
    (code, name, description, sort_order)
VALUES
    ('pending', 'Pending', 'Membership exists but is not yet active for workspace access', 10),
    ('active',  'Active',  'Membership grants active engagement visibility',               20),
    ('revoked', 'Revoked', 'Membership was explicitly revoked',                            30),
    ('expired', 'Expired', 'Membership expired automatically',                             40)
ON CONFLICT (code) DO NOTHING;

-- Dim: membership types
CREATE TABLE IF NOT EXISTS "12_engagements"."06_dim_engagement_membership_types" (
    code        character varying(50)  NOT NULL,
    name        character varying(100) NOT NULL,
    description text,
    sort_order  integer DEFAULT 0,
    created_at  timestamp with time zone DEFAULT now(),
    CONSTRAINT "06_dim_engagement_membership_types_pkey" PRIMARY KEY (code)
);

INSERT INTO "12_engagements"."06_dim_engagement_membership_types"
    (code, name, description, sort_order)
VALUES
    ('external_auditor', 'External Auditor', 'External auditor invited into the engagement',    10),
    ('internal_auditor', 'Internal Auditor', 'Internal platform user acting as auditor',        20),
    ('grc_team',         'GRC Team',         'Internal GRC participant with engagement access', 30),
    ('observer',         'Observer',         'Read-only engagement participant',                 40)
ON CONFLICT (code) DO NOTHING;

-- Dim: membership property keys
CREATE TABLE IF NOT EXISTS "12_engagements"."07_dim_engagement_membership_property_keys" (
    id          uuid DEFAULT gen_random_uuid() NOT NULL,
    code        character varying(80)  NOT NULL,
    name        character varying(120) NOT NULL,
    description text,
    data_type   character varying(30)  DEFAULT 'text',
    is_required boolean DEFAULT false,
    sort_order  integer DEFAULT 0,
    created_at  timestamp with time zone DEFAULT now(),
    CONSTRAINT "07_dim_engagement_membership_property_keys_pkey"     PRIMARY KEY (id),
    CONSTRAINT "07_dim_engagement_membership_property_keys_code_key" UNIQUE (code)
);

INSERT INTO "12_engagements"."07_dim_engagement_membership_property_keys"
    (code, name, description, data_type, is_required, sort_order)
VALUES
    ('firm_name',      'Firm Name',      'Optional external audit firm label',    'text', false, 10),
    ('role_label',     'Role Label',     'Human readable role label',             'text', false, 20),
    ('invite_source',  'Invite Source',  'Originating invite or workflow source', 'text', false, 30),
    ('invited_by',     'Invited By',     'User id or label of inviter',           'text', false, 40),
    ('accepted_at',    'Accepted At',    'Acceptance timestamp metadata',         'date', false, 50),
    ('revoked_reason', 'Revoked Reason', 'Reason the membership was revoked',     'text', false, 60),
    ('notes',          'Notes',          'Optional freeform notes',               'text', false, 70)
ON CONFLICT (code) DO NOTHING;

-- Fact: engagement memberships
CREATE TABLE IF NOT EXISTS "12_engagements"."12_lnk_engagement_memberships" (
    id                   uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_key           text                           NOT NULL,
    engagement_id        uuid                           NOT NULL,
    org_id               uuid                           NOT NULL,
    workspace_id         uuid,
    user_id              uuid,
    external_email       text,
    membership_type_code character varying(50)          NOT NULL,
    status_code          character varying(30)          DEFAULT 'pending' NOT NULL,
    joined_at            timestamp with time zone,
    expires_at           timestamp with time zone,
    is_active            boolean DEFAULT true  NOT NULL,
    is_disabled          boolean DEFAULT false NOT NULL,
    is_deleted           boolean DEFAULT false NOT NULL,
    is_test              boolean DEFAULT false NOT NULL,
    is_system            boolean DEFAULT false NOT NULL,
    is_locked            boolean DEFAULT false NOT NULL,
    created_at           timestamp with time zone DEFAULT now() NOT NULL,
    updated_at           timestamp with time zone DEFAULT now() NOT NULL,
    created_by           uuid,
    updated_by           uuid,
    deleted_at           timestamp with time zone,
    deleted_by           uuid,
    CONSTRAINT "12_lnk_engagement_memberships_pkey"      PRIMARY KEY (id),
    CONSTRAINT ck_12_lnk_engagement_memberships_principal
        CHECK ((user_id IS NOT NULL) OR (external_email IS NOT NULL)),
    CONSTRAINT "12_lnk_engagement_memberships_engagement_id_fkey"
        FOREIGN KEY (engagement_id) REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    CONSTRAINT "12_lnk_engagement_memberships_org_id_fkey"
        FOREIGN KEY (org_id) REFERENCES "03_auth_manage"."29_fct_orgs"(id),
    CONSTRAINT "12_lnk_engagement_memberships_workspace_id_fkey"
        FOREIGN KEY (workspace_id) REFERENCES "03_auth_manage"."34_fct_workspaces"(id),
    CONSTRAINT "12_lnk_engagement_memberships_user_id_fkey"
        FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id),
    CONSTRAINT "12_lnk_engagement_memberships_status_code_fkey"
        FOREIGN KEY (status_code) REFERENCES "12_engagements"."05_dim_engagement_membership_statuses"(code),
    CONSTRAINT "12_lnk_engagement_memberships_membership_type_code_fkey"
        FOREIGN KEY (membership_type_code) REFERENCES "12_engagements"."06_dim_engagement_membership_types"(code)
);

CREATE INDEX IF NOT EXISTS idx_12_lnk_engagement_memberships_user_status
    ON "12_engagements"."12_lnk_engagement_memberships" USING btree
    (user_id, status_code, is_deleted, expires_at)
    WHERE (user_id IS NOT NULL);

CREATE INDEX IF NOT EXISTS idx_12_lnk_engagement_memberships_email_status
    ON "12_engagements"."12_lnk_engagement_memberships" USING btree
    (external_email, status_code, is_deleted, expires_at)
    WHERE (external_email IS NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS uq_12_lnk_engagement_memberships_engagement_user_active
    ON "12_engagements"."12_lnk_engagement_memberships" USING btree
    (engagement_id, user_id)
    WHERE ((user_id IS NOT NULL) AND (is_deleted = false));

CREATE UNIQUE INDEX IF NOT EXISTS uq_12_lnk_engagement_memberships_engagement_email_active
    ON "12_engagements"."12_lnk_engagement_memberships" USING btree
    (engagement_id, external_email)
    WHERE ((external_email IS NOT NULL) AND (is_deleted = false));

-- Fact: evidence access grants
CREATE TABLE IF NOT EXISTS "12_engagements"."13_lnk_evidence_access_grants" (
    id            uuid DEFAULT gen_random_uuid() NOT NULL,
    tenant_key    text                           NOT NULL,
    engagement_id uuid                           NOT NULL,
    request_id    uuid,
    membership_id uuid                           NOT NULL,
    attachment_id uuid                           NOT NULL,
    granted_at    timestamp with time zone DEFAULT now() NOT NULL,
    expires_at    timestamp with time zone,
    revoked_at    timestamp with time zone,
    revoked_by    uuid,
    is_active     boolean DEFAULT true  NOT NULL,
    is_deleted    boolean DEFAULT false NOT NULL,
    created_at    timestamp with time zone DEFAULT now() NOT NULL,
    updated_at    timestamp with time zone DEFAULT now() NOT NULL,
    created_by    uuid,
    updated_by    uuid,
    CONSTRAINT "13_lnk_evidence_access_grants_pkey" PRIMARY KEY (id),
    CONSTRAINT "13_lnk_evidence_access_grants_engagement_id_fkey"
        FOREIGN KEY (engagement_id) REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    CONSTRAINT "13_lnk_evidence_access_grants_membership_id_fkey"
        FOREIGN KEY (membership_id) REFERENCES "12_engagements"."12_lnk_engagement_memberships"(id),
    CONSTRAINT "13_lnk_evidence_access_grants_attachment_id_fkey"
        FOREIGN KEY (attachment_id) REFERENCES "09_attachments"."01_fct_attachments"(id),
    CONSTRAINT "13_lnk_evidence_access_grants_request_id_fkey"
        FOREIGN KEY (request_id) REFERENCES "12_engagements"."20_trx_auditor_requests"(id)
);

CREATE INDEX IF NOT EXISTS idx_13_lnk_evidence_access_grants_membership
    ON "12_engagements"."13_lnk_evidence_access_grants" USING btree
    (membership_id, engagement_id, attachment_id)
    WHERE ((revoked_at IS NULL) AND (is_active = true) AND (is_deleted = false));

CREATE UNIQUE INDEX IF NOT EXISTS uq_13_lnk_evidence_access_grants_active_membership_attachment
    ON "12_engagements"."13_lnk_evidence_access_grants" USING btree
    (engagement_id, membership_id, attachment_id)
    WHERE ((revoked_at IS NULL) AND (is_active = true) AND (is_deleted = false));

-- Detail: membership properties (EAV)
CREATE TABLE IF NOT EXISTS "12_engagements"."24_dtl_engagement_membership_properties" (
    id            uuid DEFAULT gen_random_uuid() NOT NULL,
    membership_id uuid NOT NULL,
    property_key  character varying(80) NOT NULL,
    property_value text                 NOT NULL,
    updated_at    timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "24_dtl_engagement_membership_properties_pkey"
        PRIMARY KEY (id),
    CONSTRAINT uq_24_dtl_engagement_membership_properties_key
        UNIQUE (membership_id, property_key),
    CONSTRAINT "24_dtl_engagement_membership_properties_membership_id_fkey"
        FOREIGN KEY (membership_id) REFERENCES "12_engagements"."12_lnk_engagement_memberships"(id),
    CONSTRAINT "24_dtl_engagement_membership_properties_property_key_fkey"
        FOREIGN KEY (property_key) REFERENCES "12_engagements"."07_dim_engagement_membership_property_keys"(code)
);

-- -----------------------------------------------------------------------------
-- SECTION 2: 14_risk_registry — add version column + recreate vw_risk_detail
-- -----------------------------------------------------------------------------

-- Add version column to 10_fct_risks (staging has it, dev does not — dev is wrong here)
-- (This is the one case where staging is ahead of dev. Already exists in staging, skip.)
-- ALTER TABLE "14_risk_registry"."10_fct_risks" ADD COLUMN IF NOT EXISTS version integer DEFAULT 1 NOT NULL;

-- Recreate the view to use the simplified query (dev's old double-join version replaced)
-- (Staging already has the correct view. No-op for staging.)

-- -----------------------------------------------------------------------------
-- SECTION 3: 09_attachments — auditor access index
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_01_fct_attachments_auditor_access
    ON "09_attachments"."01_fct_attachments" USING btree
    (entity_type, entity_id)
    WHERE (auditor_access = true AND is_deleted = false);

-- -----------------------------------------------------------------------------
-- SECTION 4: 15_sandbox — workspace indexes
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_20_connectors_workspace
    ON "15_sandbox"."20_fct_connector_instances" USING btree (workspace_id)
    WHERE ((workspace_id IS NOT NULL) AND is_active AND (NOT is_deleted));

CREATE INDEX IF NOT EXISTS idx_promoted_tests_workspace
    ON "15_sandbox"."35_fct_promoted_tests" USING btree
    (tenant_key, workspace_id, is_active, is_deleted)
    WHERE (workspace_id IS NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS uq_43_record_name_per_dataset
    ON "15_sandbox"."43_dtl_dataset_records" USING btree (dataset_id, record_name)
    WHERE ((record_name)::text <> ''::text);

-- -----------------------------------------------------------------------------
-- SECTION 5: 20_ai — auditor access index
-- -----------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_50_fct_reports_auditor_access
    ON "20_ai"."50_fct_reports" USING btree (trigger_entity_type, trigger_entity_id)
    WHERE (auditor_access = true);

-- -----------------------------------------------------------------------------
-- SECTION 6: grc_role_code CHECK — align dev to staging's canonical values
--            Staging has: grc_lead, grc_sme, grc_engineer, grc_ciso,
--                         grc_lead_auditor, grc_staff_auditor, grc_vendor
--            Dev has:     grc_practitioner instead of grc_lead + grc_sme
--            Resolution:  Dev was renamed via 20260401_rename-grc-lead-to-practitioner.sql
--                         but staging keeps the original. Drop dev's constraint and
--                         replace with staging's canonical set on BOTH envs.
-- NOTE: Run on STAGING only — dev already needs a separate fix (see section 7).
-- Staging constraint is already correct — no-op for staging.
-- -----------------------------------------------------------------------------

-- -----------------------------------------------------------------------------
-- SECTION 7: Remove staging-only objects not present in dev
-- -----------------------------------------------------------------------------

-- Drop idx_46_fct_api_keys_expires (not in dev)
DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_expires;

-- Recreate api_keys indexes WITHOUT the partial filter (match dev)
DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_key_hash;
CREATE INDEX idx_46_fct_api_keys_key_hash
    ON "03_auth_manage"."46_fct_api_keys" USING btree (key_hash);

DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_user_tenant;
CREATE INDEX idx_46_fct_api_keys_user_tenant
    ON "03_auth_manage"."46_fct_api_keys" USING btree (user_id, tenant_key);

-- Drop notification performance indexes (not in dev)
DROP INDEX IF EXISTS "03_notifications".idx_12_fct_broadcasts_tenant;
DROP INDEX IF EXISTS "03_notifications".idx_17_lnk_prefs_tenant_scope;
DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_audit_event;
DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_status_scheduled;
DROP INDEX IF EXISTS "03_notifications".idx_20_trx_queue_tenant_user;
DROP INDEX IF EXISTS "03_notifications".idx_21_trx_delivery_log_occurred;
DROP INDEX IF EXISTS "03_notifications".idx_22_trx_tracking_events_occurred;
DROP INDEX IF EXISTS "03_notifications".idx_25_fct_releases_date;
DROP INDEX IF EXISTS "03_notifications".idx_26_fct_incidents_started;

-- Drop task criteria index (not in dev)
DROP INDEX IF EXISTS "08_tasks".idx_12_fct_task_criteria_task;

-- Drop sandbox run FKs (not in dev)
ALTER TABLE IF EXISTS "15_sandbox"."25_trx_sandbox_runs"
    DROP CONSTRAINT IF EXISTS fk_25_trx_sandbox_runs_dataset;
ALTER TABLE IF EXISTS "15_sandbox"."25_trx_sandbox_runs"
    DROP CONSTRAINT IF EXISTS fk_25_trx_sandbox_runs_session;

-- Align FK ON DELETE behavior to match dev (no ON DELETE RESTRICT on api_keys)
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    DROP CONSTRAINT IF EXISTS fk_46_fct_api_keys_status_id;
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    ADD CONSTRAINT fk_46_fct_api_keys_status_id
        FOREIGN KEY (status_id) REFERENCES "03_auth_manage"."45_dim_api_key_statuses"(id);

ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    DROP CONSTRAINT IF EXISTS fk_46_fct_api_keys_user_id;
ALTER TABLE "03_auth_manage"."46_fct_api_keys"
    ADD CONSTRAINT fk_46_fct_api_keys_user_id
        FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);

-- Rename task criteria PK to match staging convention
-- (staging has pk_12_fct_task_criteria; dev has 12_fct_task_criteria_pkey)
-- Staging already has the correct name — no-op for staging.

-- -----------------------------------------------------------------------------
-- SECTION 8: Type/value mismatches — align staging to dev
-- -----------------------------------------------------------------------------

-- 8a. 43_dtl_dataset_records: widen record_name to varchar(200) and drop defaults
--     Staging already has varchar(200) with no default — no-op.
--     Dev has varchar(120) with default '' — dev needs a separate fix.

-- 8b. 41_fct_risk_questionnaire_responses: staging already has varchar(50) — correct.
--     Dev has varchar(30) — dev needs a separate fix.

-- 8c. Timestamp types on questionnaire tables — staging (without time zone) is the baseline.
--     Dev has 'with time zone' — dev needs fixing.

-- DOWN ========================================================================

-- Remove engagement membership tables (restore pre-migration state on staging)
DROP TABLE IF EXISTS "12_engagements"."24_dtl_engagement_membership_properties";
DROP TABLE IF EXISTS "12_engagements"."13_lnk_evidence_access_grants";
DROP TABLE IF EXISTS "12_engagements"."12_lnk_engagement_memberships";
DROP TABLE IF EXISTS "12_engagements"."07_dim_engagement_membership_property_keys";
DROP TABLE IF EXISTS "12_engagements"."06_dim_engagement_membership_types";
DROP TABLE IF EXISTS "12_engagements"."05_dim_engagement_membership_statuses";

-- Remove indexes added to staging
DROP INDEX IF EXISTS "09_attachments".idx_01_fct_attachments_auditor_access;
DROP INDEX IF EXISTS "15_sandbox".idx_20_connectors_workspace;
DROP INDEX IF EXISTS "15_sandbox".idx_promoted_tests_workspace;
DROP INDEX IF EXISTS "15_sandbox".uq_43_record_name_per_dataset;
DROP INDEX IF EXISTS "20_ai".idx_50_fct_reports_auditor_access;

-- Restore notification indexes
CREATE INDEX idx_12_fct_broadcasts_tenant ON "03_notifications"."12_fct_broadcasts"
    USING btree (tenant_key, created_at DESC) WHERE (is_deleted = false);
CREATE INDEX idx_17_lnk_prefs_tenant_scope ON "03_notifications"."17_lnk_user_notification_preferences"
    USING btree (tenant_key, scope_level);
CREATE INDEX idx_20_trx_queue_audit_event ON "03_notifications"."20_trx_notification_queue"
    USING btree (source_audit_event_id) WHERE (source_audit_event_id IS NOT NULL);
CREATE INDEX idx_20_trx_queue_status_scheduled ON "03_notifications"."20_trx_notification_queue"
    USING btree (status_code, scheduled_at)
    WHERE ((status_code)::text = ANY ((ARRAY['queued'::character varying, 'failed'::character varying])::text[]));
CREATE INDEX idx_20_trx_queue_tenant_user ON "03_notifications"."20_trx_notification_queue"
    USING btree (tenant_key, user_id, created_at DESC);
CREATE INDEX idx_21_trx_delivery_log_occurred ON "03_notifications"."21_trx_delivery_log"
    USING btree (occurred_at DESC);
CREATE INDEX idx_22_trx_tracking_events_occurred ON "03_notifications"."22_trx_tracking_events"
    USING btree (occurred_at DESC);
CREATE INDEX idx_25_fct_releases_date ON "03_notifications"."25_fct_releases"
    USING btree (release_date DESC NULLS LAST) WHERE (is_deleted = false);
CREATE INDEX idx_26_fct_incidents_started ON "03_notifications"."26_fct_incidents"
    USING btree (started_at DESC) WHERE (is_deleted = false);
CREATE INDEX idx_12_fct_task_criteria_task ON "08_tasks"."12_fct_task_criteria"
    USING btree (task_id) WHERE (is_deleted = false);

-- Restore api_keys indexes to partial form
DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_key_hash;
CREATE INDEX idx_46_fct_api_keys_key_hash ON "03_auth_manage"."46_fct_api_keys"
    USING btree (key_hash) WHERE (is_deleted = false);
DROP INDEX IF EXISTS "03_auth_manage".idx_46_fct_api_keys_user_tenant;
CREATE INDEX idx_46_fct_api_keys_user_tenant ON "03_auth_manage"."46_fct_api_keys"
    USING btree (user_id, tenant_key) WHERE (is_deleted = false);
CREATE INDEX idx_46_fct_api_keys_expires ON "03_auth_manage"."46_fct_api_keys"
    USING btree (expires_at)
    WHERE ((expires_at IS NOT NULL) AND (revoked_at IS NULL) AND (is_deleted = false));

-- Restore sandbox run FKs
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    ADD CONSTRAINT fk_25_trx_sandbox_runs_dataset
        FOREIGN KEY (dataset_id) REFERENCES "15_sandbox"."21_fct_datasets"(id);
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    ADD CONSTRAINT fk_25_trx_sandbox_runs_session
        FOREIGN KEY (live_session_id) REFERENCES "15_sandbox"."28_fct_live_sessions"(id);
