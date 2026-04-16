-- =============================================================================
-- Migration: 20260401_full-prod-sync.sql
-- Description: Full idempotent sync — brings staging and prod fully in line
--              with dev. Creates missing tables, adds missing columns, recreates
--              views. Every statement is guarded with IF NOT EXISTS / IF EXISTS.
--              Safe to run on any environment any number of times.
--
-- Covers:
--   NEW TABLES    — 03_auth_manage: 01_dim_identity_types, 04_dtl_user_identities,
--                   05_dtl_user_credentials, 06_trx_auth_sessions,
--                   07_trx_login_attempts, 08_trx_auth_challenges,
--                   09_aud_auth_events, 22_aud_access_events,
--                   27_aud_product_events, 32_aud_org_events,
--                   37_aud_workspace_events, 47_lnk_grc_role_assignments,
--                   48_lnk_grc_access_grants
--                 — 03_notifications: 09_dim_variable_queries
--                 — 05_grc_library: 32_lnk_cross_framework_equivalences
--   MISSING COLS  — 03_auth_manage.18_lnk_group_memberships: scope_org_id, scope_workspace_id
--                 — 03_auth_manage.48_lnk_grc_access_grants: created_at, granted_by, revoked_by
--                 — 09_attachments.01_fct_attachments: auditor_access, published_for_audit_*
--                 — 20_ai.45_fct_job_queue: progress_pct
--                 — 20_ai.50_fct_reports: auditor_access, published_for_audit_*
--   VIEWS         — 03_auth_manage: 10_vw_auth_users, v_grc_team
--                 — 12_engagements: 40_vw_engagement_detail (updated)
--   GRANTS        — write + read roles on all new tables (env-aware, no-op if role absent)
-- =============================================================================


-- =============================================================================
-- SECTION 1: NEW TABLES — 03_auth_manage schema
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 1.1  01_dim_identity_types  (dimension — seeds included)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."01_dim_identity_types" (
    id          uuid                        NOT NULL,
    code        character varying(50)       NOT NULL,
    name        character varying(100)      NOT NULL,
    description text,
    sort_order  integer                     NOT NULL,
    created_at  timestamp without time zone NOT NULL,
    updated_at  timestamp without time zone NOT NULL
);

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_01_dim_identity_types'
          AND conrelid = '"03_auth_manage"."01_dim_identity_types"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."01_dim_identity_types"
            ADD CONSTRAINT pk_01_dim_identity_types PRIMARY KEY (id);
    END IF;
END $$;

-- Unique code
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_01_dim_identity_types_code'
          AND conrelid = '"03_auth_manage"."01_dim_identity_types"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."01_dim_identity_types"
            ADD CONSTRAINT uq_01_dim_identity_types_code UNIQUE (code);
    END IF;
END $$;

-- Seed data (idempotent)
INSERT INTO "03_auth_manage"."01_dim_identity_types" (id, code, name, description, sort_order, created_at, updated_at)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'email',    'Email',    'Primary email identifier',      10, '2026-03-13 00:00:00', '2026-03-13 00:00:00'),
    ('00000000-0000-0000-0000-000000000002', 'username', 'Username', 'Optional alternate identifier',  20, '2026-03-13 00:00:00', '2026-03-13 00:00:00')
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE "03_auth_manage"."01_dim_identity_types" IS 'Reference values for supported local identity types.';


-- ---------------------------------------------------------------------------
-- 1.2  04_dtl_user_identities  (email / username identifiers per user)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."04_dtl_user_identities" (
    id                  uuid                        NOT NULL,
    user_id             uuid                        NOT NULL,
    tenant_key          character varying(100)      NOT NULL,
    identity_type_code  character varying(50)       NOT NULL,
    display_value       character varying(320)      NOT NULL,
    normalized_value    character varying(320)      NOT NULL,
    is_primary          boolean                     NOT NULL DEFAULT false,
    is_verified         boolean                     NOT NULL DEFAULT false,
    verified_at         timestamp without time zone,
    is_active           boolean                     NOT NULL DEFAULT true,
    is_disabled         boolean                     NOT NULL DEFAULT false,
    is_deleted          boolean                     NOT NULL DEFAULT false,
    is_test             boolean                     NOT NULL DEFAULT false,
    is_system           boolean                     NOT NULL DEFAULT false,
    is_locked           boolean                     NOT NULL DEFAULT false,
    created_at          timestamp without time zone NOT NULL,
    updated_at          timestamp without time zone NOT NULL,
    created_by          uuid,
    updated_by          uuid,
    deleted_at          timestamp without time zone,
    deleted_by          uuid
);

COMMENT ON TABLE "03_auth_manage"."04_dtl_user_identities" IS 'Email and username identifiers attached to a local auth user.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_04_dtl_user_identities'
          AND conrelid = '"03_auth_manage"."04_dtl_user_identities"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."04_dtl_user_identities"
            ADD CONSTRAINT pk_04_dtl_user_identities PRIMARY KEY (id);
    END IF;
END $$;

-- Unique (tenant, type, normalized) — enforces one email/username per tenant
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_04_dtl_user_identities_tenant_type_normalized'
          AND conrelid = '"03_auth_manage"."04_dtl_user_identities"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."04_dtl_user_identities"
            ADD CONSTRAINT uq_04_dtl_user_identities_tenant_type_normalized
            UNIQUE (tenant_key, identity_type_code, normalized_value);
    END IF;
END $$;

-- FK to users
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_04_dtl_user_identities_user_id_03_fct_users'
          AND conrelid = '"03_auth_manage"."04_dtl_user_identities"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."04_dtl_user_identities"
            ADD CONSTRAINT fk_04_dtl_user_identities_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_03_auth_manage_04_dtl_user_identities_user_id
    ON "03_auth_manage"."04_dtl_user_identities" USING btree (user_id);

CREATE INDEX IF NOT EXISTS idx_03_auth_manage_04_dtl_user_identities_lookup
    ON "03_auth_manage"."04_dtl_user_identities" USING btree (tenant_key, identity_type_code, normalized_value);


-- ---------------------------------------------------------------------------
-- 1.3  05_dtl_user_credentials  (hashed passwords per user)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."05_dtl_user_credentials" (
    id                  uuid                        NOT NULL,
    user_id             uuid                        NOT NULL,
    tenant_key          character varying(100)      NOT NULL,
    credential_type     character varying(50)       NOT NULL,
    password_hash       character varying(512)      NOT NULL,
    password_version    integer                     NOT NULL,
    password_changed_at timestamp without time zone NOT NULL,
    is_active           boolean                     NOT NULL DEFAULT true,
    is_disabled         boolean                     NOT NULL DEFAULT false,
    is_deleted          boolean                     NOT NULL DEFAULT false,
    is_test             boolean                     NOT NULL DEFAULT false,
    is_system           boolean                     NOT NULL DEFAULT false,
    is_locked           boolean                     NOT NULL DEFAULT false,
    created_at          timestamp without time zone NOT NULL,
    updated_at          timestamp without time zone NOT NULL,
    created_by          uuid,
    updated_by          uuid,
    deleted_at          timestamp without time zone,
    deleted_by          uuid
);

COMMENT ON TABLE "03_auth_manage"."05_dtl_user_credentials" IS 'Hashed credential records for local auth users.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_05_dtl_user_credentials'
          AND conrelid = '"03_auth_manage"."05_dtl_user_credentials"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."05_dtl_user_credentials"
            ADD CONSTRAINT pk_05_dtl_user_credentials PRIMARY KEY (id);
    END IF;
END $$;

-- FK to users
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_05_dtl_user_credentials_user_id_03_fct_users'
          AND conrelid = '"03_auth_manage"."05_dtl_user_credentials"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."05_dtl_user_credentials"
            ADD CONSTRAINT fk_05_dtl_user_credentials_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);
    END IF;
END $$;

-- Index
CREATE INDEX IF NOT EXISTS idx_03_auth_manage_05_dtl_user_credentials_user_id
    ON "03_auth_manage"."05_dtl_user_credentials" USING btree (user_id);


-- ---------------------------------------------------------------------------
-- 1.4  06_trx_auth_sessions  (new session table — replaces 10_trx_auth_sessions)
--       Note: 10_trx_auth_sessions is kept for backwards compatibility.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."06_trx_auth_sessions" (
    id                        uuid                        NOT NULL,
    user_id                   uuid                        NOT NULL,
    tenant_key                character varying(100)      NOT NULL,
    refresh_token_hash        character varying(128)      NOT NULL,
    refresh_token_expires_at  timestamp without time zone NOT NULL,
    rotated_at                timestamp without time zone,
    revoked_at                timestamp without time zone,
    revocation_reason         character varying(100),
    client_ip                 character varying(64),
    user_agent                character varying(512),
    rotation_counter          integer                     NOT NULL,
    created_at                timestamp without time zone NOT NULL,
    updated_at                timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."06_trx_auth_sessions" IS 'Active refresh-token sessions (new schema, replaces 10_trx_auth_sessions).';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_06_trx_auth_sessions'
          AND conrelid = '"03_auth_manage"."06_trx_auth_sessions"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."06_trx_auth_sessions"
            ADD CONSTRAINT pk_06_trx_auth_sessions PRIMARY KEY (id);
    END IF;
END $$;

-- FK to users
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_06_trx_auth_sessions_user_id_03_fct_users'
          AND conrelid = '"03_auth_manage"."06_trx_auth_sessions"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."06_trx_auth_sessions"
            ADD CONSTRAINT fk_06_trx_auth_sessions_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);
    END IF;
END $$;

-- Index: active sessions per user
CREATE INDEX IF NOT EXISTS idx_03_auth_manage_06_trx_auth_sessions_user_revoked
    ON "03_auth_manage"."06_trx_auth_sessions" USING btree (user_id, revoked_at);


-- ---------------------------------------------------------------------------
-- 1.5  07_trx_login_attempts  (new — replaces 11_trx_login_attempts)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."07_trx_login_attempts" (
    id                    uuid                        NOT NULL,
    tenant_key            character varying(100)      NOT NULL,
    normalized_identifier character varying(320)      NOT NULL,
    identity_type_code    character varying(50),
    user_id               uuid,
    outcome               character varying(50)       NOT NULL,
    failure_reason        character varying(100),
    client_ip             character varying(64),
    occurred_at           timestamp without time zone NOT NULL,
    created_at            timestamp without time zone NOT NULL,
    updated_at            timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."07_trx_login_attempts" IS 'Login attempt audit log (new schema, replaces 11_trx_login_attempts).';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_07_trx_login_attempts'
          AND conrelid = '"03_auth_manage"."07_trx_login_attempts"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."07_trx_login_attempts"
            ADD CONSTRAINT pk_07_trx_login_attempts PRIMARY KEY (id);
    END IF;
END $$;

-- FK to users (nullable — pre-resolve user)
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_07_trx_login_attempts_user_id_03_fct_users'
          AND conrelid = '"03_auth_manage"."07_trx_login_attempts"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."07_trx_login_attempts"
            ADD CONSTRAINT fk_07_trx_login_attempts_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);
    END IF;
END $$;

-- Index: lookup by tenant + identifier + time (rate-limit / lockout checks)
CREATE INDEX IF NOT EXISTS idx_03_auth_manage_07_trx_login_attempts_lookup
    ON "03_auth_manage"."07_trx_login_attempts" USING btree (tenant_key, normalized_identifier, occurred_at);


-- ---------------------------------------------------------------------------
-- 1.6  08_trx_auth_challenges  (new — replaces 12_trx_auth_challenges)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."08_trx_auth_challenges" (
    id                  uuid                        NOT NULL,
    tenant_key          character varying(100)      NOT NULL,
    user_id             uuid,
    challenge_type_code character varying(50)       NOT NULL,
    target_value        character varying(320)      NOT NULL,
    secret_hash         character varying(128)      NOT NULL,
    expires_at          timestamp without time zone NOT NULL,
    consumed_at         timestamp without time zone,
    requested_ip        character varying(64),
    created_at          timestamp without time zone NOT NULL,
    updated_at          timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."08_trx_auth_challenges" IS 'One-time challenge tokens for password reset and email verify (replaces 12_trx_auth_challenges).';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_08_trx_auth_challenges'
          AND conrelid = '"03_auth_manage"."08_trx_auth_challenges"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."08_trx_auth_challenges"
            ADD CONSTRAINT pk_08_trx_auth_challenges PRIMARY KEY (id);
    END IF;
END $$;

-- FK to users
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_08_trx_auth_challenges_user_id_03_fct_users'
          AND conrelid = '"03_auth_manage"."08_trx_auth_challenges"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."08_trx_auth_challenges"
            ADD CONSTRAINT fk_08_trx_auth_challenges_user_id_03_fct_users
            FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- 1.7  09_aud_auth_events  (domain-specific auth audit — replaces 40_aud_events)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."09_aud_auth_events" (
    id              uuid                        NOT NULL,
    entity_type     character varying(100)      NOT NULL,
    entity_id       uuid                        NOT NULL,
    event_type      character varying(100)      NOT NULL,
    event_key       character varying(100)      NOT NULL,
    previous_value  text,
    new_value       text,
    actor_id        uuid,
    approver_id     uuid,
    occurred_at     timestamp without time zone NOT NULL,
    ip_address      character varying(64),
    session_id      uuid,
    created_at      timestamp without time zone NOT NULL,
    updated_at      timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."09_aud_auth_events" IS 'Domain-specific audit trail for all auth events.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_09_aud_auth_events'
          AND conrelid = '"03_auth_manage"."09_aud_auth_events"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."09_aud_auth_events"
            ADD CONSTRAINT pk_09_aud_auth_events PRIMARY KEY (id);
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- 1.8  22_aud_access_events  (access / RBAC audit events)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."22_aud_access_events" (
    id              uuid                        NOT NULL,
    entity_type     character varying(100)      NOT NULL,
    entity_id       uuid                        NOT NULL,
    event_type      character varying(100)      NOT NULL,
    event_key       character varying(100)      NOT NULL,
    previous_value  text,
    new_value       text,
    actor_id        uuid,
    approver_id     uuid,
    occurred_at     timestamp without time zone NOT NULL,
    ip_address      character varying(64),
    session_id      uuid,
    created_at      timestamp without time zone NOT NULL,
    updated_at      timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."22_aud_access_events" IS 'Audit trail for role / group / access context changes.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_22_aud_access_events'
          AND conrelid = '"03_auth_manage"."22_aud_access_events"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."22_aud_access_events"
            ADD CONSTRAINT pk_22_aud_access_events PRIMARY KEY (id);
    END IF;
END $$;

-- Index: entity + time
CREATE INDEX IF NOT EXISTS idx_03_auth_manage_22_aud_access_events_entity_occurred
    ON "03_auth_manage"."22_aud_access_events" USING btree (entity_type, entity_id, occurred_at);


-- ---------------------------------------------------------------------------
-- 1.9  27_aud_product_events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."27_aud_product_events" (
    id              uuid                        NOT NULL,
    entity_type     character varying(100)      NOT NULL,
    entity_id       uuid                        NOT NULL,
    event_type      character varying(100)      NOT NULL,
    event_key       character varying(100)      NOT NULL,
    previous_value  text,
    new_value       text,
    actor_id        uuid,
    approver_id     uuid,
    occurred_at     timestamp without time zone NOT NULL,
    ip_address      character varying(64),
    session_id      uuid,
    created_at      timestamp without time zone NOT NULL,
    updated_at      timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."27_aud_product_events" IS 'Audit trail for product-scoped changes.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_27_aud_product_events'
          AND conrelid = '"03_auth_manage"."27_aud_product_events"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."27_aud_product_events"
            ADD CONSTRAINT pk_27_aud_product_events PRIMARY KEY (id);
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- 1.10  32_aud_org_events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."32_aud_org_events" (
    id              uuid                        NOT NULL,
    entity_type     character varying(100)      NOT NULL,
    entity_id       uuid                        NOT NULL,
    event_type      character varying(100)      NOT NULL,
    event_key       character varying(100)      NOT NULL,
    previous_value  text,
    new_value       text,
    actor_id        uuid,
    approver_id     uuid,
    occurred_at     timestamp without time zone NOT NULL,
    ip_address      character varying(64),
    session_id      uuid,
    created_at      timestamp without time zone NOT NULL,
    updated_at      timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."32_aud_org_events" IS 'Audit trail for organisation-scoped changes.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_32_aud_org_events'
          AND conrelid = '"03_auth_manage"."32_aud_org_events"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."32_aud_org_events"
            ADD CONSTRAINT pk_32_aud_org_events PRIMARY KEY (id);
    END IF;
END $$;


-- ---------------------------------------------------------------------------
-- 1.11  37_aud_workspace_events
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_auth_manage"."37_aud_workspace_events" (
    id              uuid                        NOT NULL,
    entity_type     character varying(100)      NOT NULL,
    entity_id       uuid                        NOT NULL,
    event_type      character varying(100)      NOT NULL,
    event_key       character varying(100)      NOT NULL,
    previous_value  text,
    new_value       text,
    actor_id        uuid,
    approver_id     uuid,
    occurred_at     timestamp without time zone NOT NULL,
    ip_address      character varying(64),
    session_id      uuid,
    created_at      timestamp without time zone NOT NULL,
    updated_at      timestamp without time zone NOT NULL
);

COMMENT ON TABLE "03_auth_manage"."37_aud_workspace_events" IS 'Audit trail for workspace-scoped changes.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_37_aud_workspace_events'
          AND conrelid = '"03_auth_manage"."37_aud_workspace_events"'::regclass
    ) THEN
        ALTER TABLE "03_auth_manage"."37_aud_workspace_events"
            ADD CONSTRAINT pk_37_aud_workspace_events PRIMARY KEY (id);
    END IF;
END $$;


-- =============================================================================
-- SECTION 2: NEW TABLES — 03_notifications schema
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 2.1  09_dim_variable_queries  (templated SQL queries for notification vars)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "03_notifications"."09_dim_variable_queries" (
    id              uuid                     NOT NULL DEFAULT gen_random_uuid(),
    slug            character varying(100)   NOT NULL,
    name            character varying(200)   NOT NULL,
    description     text                     NOT NULL DEFAULT '',
    sql_template    text                     NOT NULL,
    bind_params     jsonb                    NOT NULL DEFAULT '[]'::jsonb,
    preview_default text,
    is_active       boolean                  NOT NULL DEFAULT true,
    created_at      timestamp with time zone NOT NULL DEFAULT now(),
    updated_at      timestamp with time zone NOT NULL DEFAULT now()
);

COMMENT ON TABLE "03_notifications"."09_dim_variable_queries" IS 'Parameterised SQL queries that back dynamic notification template variables.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = '09_dim_variable_queries_pkey'
          AND conrelid = '"03_notifications"."09_dim_variable_queries"'::regclass
    ) THEN
        ALTER TABLE "03_notifications"."09_dim_variable_queries"
            ADD CONSTRAINT "09_dim_variable_queries_pkey" PRIMARY KEY (id);
    END IF;
END $$;

-- Unique slug
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = '09_dim_variable_queries_slug_key'
          AND conrelid = '"03_notifications"."09_dim_variable_queries"'::regclass
    ) THEN
        ALTER TABLE "03_notifications"."09_dim_variable_queries"
            ADD CONSTRAINT "09_dim_variable_queries_slug_key" UNIQUE (slug);
    END IF;
END $$;


-- =============================================================================
-- SECTION 3: NEW TABLES — 05_grc_library schema
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 3.1  32_lnk_cross_framework_equivalences
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "05_grc_library"."32_lnk_cross_framework_equivalences" (
    id                uuid                    NOT NULL,
    source_control_id uuid                    NOT NULL,
    target_control_id uuid                    NOT NULL,
    equivalence_type  character varying(30)   NOT NULL DEFAULT 'related',
    confidence        character varying(20)   NOT NULL DEFAULT 'medium',
    created_at        timestamp without time zone NOT NULL,
    created_by        uuid,
    CONSTRAINT ck_32_lnk_cross_fw_equivalences_type
        CHECK (equivalence_type = ANY (ARRAY['equivalent', 'partial', 'related'])),
    CONSTRAINT ck_32_lnk_cross_fw_equivalences_conf
        CHECK (confidence = ANY (ARRAY['high', 'medium', 'low']))
);

COMMENT ON TABLE "05_grc_library"."32_lnk_cross_framework_equivalences" IS 'Cross-framework control equivalence mapping.';

-- Primary key
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'pk_32_lnk_cross_fw_equivalences'
          AND conrelid = '"05_grc_library"."32_lnk_cross_framework_equivalences"'::regclass
    ) THEN
        ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
            ADD CONSTRAINT pk_32_lnk_cross_fw_equivalences PRIMARY KEY (id);
    END IF;
END $$;

-- Unique pair
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'uq_32_lnk_cross_fw_equivalences'
          AND conrelid = '"05_grc_library"."32_lnk_cross_framework_equivalences"'::regclass
    ) THEN
        ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
            ADD CONSTRAINT uq_32_lnk_cross_fw_equivalences UNIQUE (source_control_id, target_control_id);
    END IF;
END $$;

-- FK: source control
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_32_lnk_cross_fw_equivalences_source'
          AND conrelid = '"05_grc_library"."32_lnk_cross_framework_equivalences"'::regclass
    ) THEN
        ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
            ADD CONSTRAINT fk_32_lnk_cross_fw_equivalences_source
            FOREIGN KEY (source_control_id)
            REFERENCES "05_grc_library"."13_fct_controls"(id) ON DELETE CASCADE;
    END IF;
END $$;

-- FK: target control
DO $$ BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'fk_32_lnk_cross_fw_equivalences_target'
          AND conrelid = '"05_grc_library"."32_lnk_cross_framework_equivalences"'::regclass
    ) THEN
        ALTER TABLE "05_grc_library"."32_lnk_cross_framework_equivalences"
            ADD CONSTRAINT fk_32_lnk_cross_fw_equivalences_target
            FOREIGN KEY (target_control_id)
            REFERENCES "05_grc_library"."13_fct_controls"(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_32_lnk_cross_fw_equiv_source
    ON "05_grc_library"."32_lnk_cross_framework_equivalences" USING btree (source_control_id);

CREATE INDEX IF NOT EXISTS idx_32_lnk_cross_fw_equiv_target
    ON "05_grc_library"."32_lnk_cross_framework_equivalences" USING btree (target_control_id);


-- =============================================================================
-- SECTION 3b: ENSURE GRC TABLES EXIST
-- (47_ and 48_ may be missing in prod even though create-grc-role-assignments.sql
--  is recorded as applied — its DDL never actually landed)
-- =============================================================================

CREATE TABLE IF NOT EXISTS "03_auth_manage"."47_lnk_grc_role_assignments" (
    id              uuid                        NOT NULL,
    org_id          uuid                        NOT NULL,
    user_id         uuid                        NOT NULL,
    grc_role_code   character varying(60)       NOT NULL,
    workspace_id    uuid,
    assigned_by     uuid,
    assigned_at     timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at      timestamp without time zone,
    revoked_by      uuid,
    created_at      timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='pk_47_lnk_grc_role_assignments') THEN
        ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments" ADD CONSTRAINT pk_47_lnk_grc_role_assignments PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_47_grc_ra_org') THEN
        ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
            ADD CONSTRAINT fk_47_grc_ra_org FOREIGN KEY (org_id) REFERENCES "03_auth_manage"."29_fct_orgs"(id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_47_grc_ra_user') THEN
        ALTER TABLE "03_auth_manage"."47_lnk_grc_role_assignments"
            ADD CONSTRAINT fk_47_grc_ra_user FOREIGN KEY (user_id) REFERENCES "03_auth_manage"."03_fct_users"(id);
    END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS uq_47_grc_ra_active
    ON "03_auth_manage"."47_lnk_grc_role_assignments" (org_id, user_id, grc_role_code)
    WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_47_grc_ra_org
    ON "03_auth_manage"."47_lnk_grc_role_assignments" (org_id)
    WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_47_grc_ra_user
    ON "03_auth_manage"."47_lnk_grc_role_assignments" (user_id)
    WHERE revoked_at IS NULL;

CREATE TABLE IF NOT EXISTS "03_auth_manage"."48_lnk_grc_access_grants" (
    id                      uuid                        NOT NULL,
    grc_role_assignment_id  uuid                        NOT NULL,
    scope_type              character varying(30)       NOT NULL,
    scope_id                uuid                        NOT NULL,
    granted_by              uuid,
    granted_at              timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    revoked_at              timestamp without time zone,
    revoked_by              uuid,
    created_at              timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP
);
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='pk_48_lnk_grc_access_grants') THEN
        ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants" ADD CONSTRAINT pk_48_lnk_grc_access_grants PRIMARY KEY (id);
    END IF;
END $$;
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname='fk_48_grc_ag_assignment') THEN
        ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants"
            ADD CONSTRAINT fk_48_grc_ag_assignment
            FOREIGN KEY (grc_role_assignment_id) REFERENCES "03_auth_manage"."47_lnk_grc_role_assignments"(id);
    END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS uq_48_grc_ag_active
    ON "03_auth_manage"."48_lnk_grc_access_grants" (grc_role_assignment_id, scope_type, scope_id)
    WHERE revoked_at IS NULL;


-- =============================================================================
-- SECTION 4: MISSING COLUMNS ON EXISTING TABLES
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 4.1  03_auth_manage.18_lnk_group_memberships
--       Missing: scope_org_id, scope_workspace_id
-- ---------------------------------------------------------------------------
ALTER TABLE "03_auth_manage"."18_lnk_group_memberships"
    ADD COLUMN IF NOT EXISTS scope_org_id       uuid,
    ADD COLUMN IF NOT EXISTS scope_workspace_id uuid;

-- Indexes for new scope columns (partial — only non-null, non-deleted rows)
CREATE INDEX IF NOT EXISTS idx_18_gm_scope_org
    ON "03_auth_manage"."18_lnk_group_memberships" USING btree (scope_org_id, group_id)
    WHERE scope_org_id IS NOT NULL AND is_deleted = false;

CREATE INDEX IF NOT EXISTS idx_18_gm_scope_ws
    ON "03_auth_manage"."18_lnk_group_memberships" USING btree (scope_workspace_id, group_id)
    WHERE scope_workspace_id IS NOT NULL AND is_deleted = false;


-- ---------------------------------------------------------------------------
-- 4.2  03_auth_manage.48_lnk_grc_access_grants
--       Missing: created_at, granted_by, revoked_by
--       (section 3b creates these columns if the table was just created)
-- ---------------------------------------------------------------------------
DO $$ BEGIN
    ALTER TABLE "03_auth_manage"."48_lnk_grc_access_grants"
        ADD COLUMN IF NOT EXISTS created_at timestamp without time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ADD COLUMN IF NOT EXISTS granted_by uuid,
        ADD COLUMN IF NOT EXISTS revoked_by uuid;
EXCEPTION WHEN undefined_table THEN NULL; END $$;

-- Indexes (also covered by section 3b but idempotent)
CREATE INDEX IF NOT EXISTS idx_48_grc_ag_assignment
    ON "03_auth_manage"."48_lnk_grc_access_grants" USING btree (grc_role_assignment_id)
    WHERE revoked_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_48_grc_ag_active
    ON "03_auth_manage"."48_lnk_grc_access_grants" USING btree (grc_role_assignment_id, scope_type, scope_id)
    WHERE revoked_at IS NULL;


-- ---------------------------------------------------------------------------
-- 4.3  09_attachments.01_fct_attachments
--       Missing: auditor_access, published_for_audit_at, published_for_audit_by
-- ---------------------------------------------------------------------------
ALTER TABLE "09_attachments"."01_fct_attachments"
    ADD COLUMN IF NOT EXISTS auditor_access          boolean                     NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS published_for_audit_at  timestamp without time zone,
    ADD COLUMN IF NOT EXISTS published_for_audit_by  uuid;


-- ---------------------------------------------------------------------------
-- 4.4  20_ai.45_fct_job_queue
--       Missing: progress_pct
-- ---------------------------------------------------------------------------
ALTER TABLE "20_ai"."45_fct_job_queue"
    ADD COLUMN IF NOT EXISTS progress_pct integer DEFAULT 0;


-- ---------------------------------------------------------------------------
-- 4.5  20_ai.50_fct_reports
--       Missing: auditor_access, published_for_audit_at, published_for_audit_by
-- ---------------------------------------------------------------------------
ALTER TABLE "20_ai"."50_fct_reports"
    ADD COLUMN IF NOT EXISTS auditor_access          boolean                     NOT NULL DEFAULT false,
    ADD COLUMN IF NOT EXISTS published_for_audit_at  timestamp without time zone,
    ADD COLUMN IF NOT EXISTS published_for_audit_by  uuid;


-- =============================================================================
-- SECTION 5: VIEWS — create missing, replace updated
-- =============================================================================

-- ---------------------------------------------------------------------------
-- 5.1  03_auth_manage.10_vw_auth_users  (new view — depends on 04_dtl_user_identities)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "03_auth_manage"."10_vw_auth_users" AS
SELECT
    u.id              AS user_id,
    u.tenant_key,
    email.display_value                    AS email,
    username.display_value                 AS username,
    COALESCE(email.is_verified, false)     AS email_verified,
    u.account_status
FROM "03_auth_manage"."03_fct_users" u
LEFT JOIN "03_auth_manage"."04_dtl_user_identities" email
    ON email.user_id = u.id
    AND email.identity_type_code = 'email'
    AND email.is_deleted = false
LEFT JOIN "03_auth_manage"."04_dtl_user_identities" username
    ON username.user_id = u.id
    AND username.identity_type_code = 'username'
    AND username.is_deleted = false
WHERE u.is_deleted = false
  AND u.is_test    = false;

COMMENT ON VIEW "03_auth_manage"."10_vw_auth_users" IS 'Resolved email and username per user from the new identity model.';


-- ---------------------------------------------------------------------------
-- 5.2  03_auth_manage.v_grc_team  (new view — GRC role assignments with user info)
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "03_auth_manage"."v_grc_team" AS
SELECT
    ra.id                   AS assignment_id,
    ra.org_id,
    ra.user_id,
    ra.grc_role_code,
    r.name                  AS role_name,
    r.description           AS role_description,
    email.property_value    AS email,
    dn.property_value       AS display_name,
    ra.assigned_by,
    ra.assigned_at,
    ra.revoked_at,
    ra.created_at,
    (
        SELECT count(*)
        FROM "03_auth_manage"."48_lnk_grc_access_grants" g
        WHERE g.grc_role_assignment_id = ra.id
          AND g.revoked_at IS NULL
    ) AS active_grant_count
FROM "03_auth_manage"."47_lnk_grc_role_assignments" ra
JOIN "03_auth_manage"."16_fct_roles" r
    ON r.code = ra.grc_role_code
    AND r.is_deleted = false
    AND r.role_level_code = 'workspace'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" email
    ON email.user_id = ra.user_id AND email.property_key = 'email'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" dn
    ON dn.user_id = ra.user_id AND dn.property_key = 'display_name'
WHERE ra.revoked_at IS NULL;

COMMENT ON VIEW "03_auth_manage"."v_grc_team" IS 'GRC team members with active role assignments and access grant counts.';


-- ---------------------------------------------------------------------------
-- 5.3  12_engagements.40_vw_engagement_detail  (updated — adds engagement_type, removes org_name)
--
-- The existing staging view has a different column layout (includes org_name,
-- different column order).  CREATE OR REPLACE VIEW cannot rename/reorder
-- existing columns, so we drop and recreate.  The view carries no data.
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS "12_engagements"."40_vw_engagement_detail";

CREATE VIEW "12_engagements"."40_vw_engagement_detail" AS
SELECT
    e.id,
    e.tenant_key,
    e.org_id,
    e.engagement_code,
    e.framework_id,
    e.framework_deployment_id,
    e.status_code,
    s.name                          AS status_name,
    e.target_completion_date,
    name_prop.property_value        AS engagement_name,
    firm_prop.property_value        AS auditor_firm,
    scope_prop.property_value       AS scope_description,
    p_start.property_value          AS audit_period_start,
    p_end.property_value            AS audit_period_end,
    p_sme.property_value            AS lead_grc_sme,
    p_type.property_value           AS engagement_type,
    (
        SELECT count(lvc.*)::integer
        FROM "05_grc_library"."31_lnk_framework_version_controls" lvc
        JOIN "05_grc_library"."16_fct_framework_deployments" fd ON fd.id = e.framework_deployment_id
        WHERE lvc.framework_version_id = fd.deployed_version_id
    )                               AS total_controls_count,
    (
        SELECT count(r.*)::integer
        FROM "12_engagements"."20_trx_auditor_requests" r
        WHERE r.engagement_id = e.id AND r.request_status = 'open'
    )                               AS open_requests_count,
    (
        SELECT count(v.*)::integer
        FROM "12_engagements"."21_trx_auditor_verifications" v
        WHERE v.engagement_id = e.id
    )                               AS verified_controls_count,
    e.is_active,
    e.created_at,
    e.updated_at
FROM "12_engagements"."10_fct_audit_engagements" e
JOIN "12_engagements"."02_dim_engagement_statuses" s
    ON s.code = e.status_code
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" name_prop
    ON name_prop.engagement_id = e.id AND name_prop.property_key = 'engagement_name'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" firm_prop
    ON firm_prop.engagement_id = e.id AND firm_prop.property_key = 'auditor_firm'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" scope_prop
    ON scope_prop.engagement_id = e.id AND scope_prop.property_key = 'scope_description'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_start
    ON p_start.engagement_id = e.id AND p_start.property_key = 'audit_period_start'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_end
    ON p_end.engagement_id = e.id AND p_end.property_key = 'audit_period_end'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_sme
    ON p_sme.engagement_id = e.id AND p_sme.property_key = 'lead_grc_sme'
LEFT JOIN "12_engagements"."22_dtl_engagement_properties" p_type
    ON p_type.engagement_id = e.id AND p_type.property_key = 'engagement_type'
WHERE e.is_deleted = false;

COMMENT ON VIEW "12_engagements"."40_vw_engagement_detail" IS 'Full engagement detail with resolved property EAV values including engagement_type.';


-- =============================================================================
-- SECTION 6: GRANTS (staging / prod role names)
-- =============================================================================
-- Grants are environment-aware: the write/read role suffixes vary.
-- This block uses DO $$ to silently skip if a role does not exist
-- (e.g., running on an environment with a different naming convention).

DO $$ BEGIN
    -- 03_auth_manage new tables
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_database() || '_write'
                  OR rolname = replace(current_database(), 'kcontrol_', 'kcontrol_') || '_write') THEN
        NULL; -- placeholder
    END IF;
END $$;

-- Attempt grants for staging roles (will succeed on staging, silently logged error on prod if names differ)
DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."01_dim_identity_types" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."01_dim_identity_types" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."04_dtl_user_identities" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."04_dtl_user_identities" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."05_dtl_user_credentials" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."05_dtl_user_credentials" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."06_trx_auth_sessions" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."06_trx_auth_sessions" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."07_trx_login_attempts" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."07_trx_login_attempts" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."08_trx_auth_challenges" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."08_trx_auth_challenges" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."09_aud_auth_events" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."09_aud_auth_events" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."22_aud_access_events" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."22_aud_access_events" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."27_aud_product_events" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."27_aud_product_events" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."32_aud_org_events" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."32_aud_org_events" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_auth_manage"."37_aud_workspace_events" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_auth_manage"."37_aud_workspace_events" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "03_notifications"."09_dim_variable_queries" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "03_notifications"."09_dim_variable_queries" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT, INSERT, UPDATE, DELETE, REFERENCES, TRIGGER, TRUNCATE ON TABLE "05_grc_library"."32_lnk_cross_framework_equivalences" TO %I',
        current_database() || '_write'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;

DO $$ BEGIN
    EXECUTE format(
        'GRANT SELECT ON TABLE "05_grc_library"."32_lnk_cross_framework_equivalences" TO %I',
        current_database() || '_read'
    );
EXCEPTION WHEN undefined_object THEN NULL;
END $$;


-- =============================================================================
-- SECTION 7: VERIFICATION QUERIES  (run after migration to confirm success)
-- =============================================================================
-- Uncomment to run inline, or paste into psql for manual check.

/*
-- Count new tables
SELECT COUNT(*) AS new_tables_present FROM (
    SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '01_dim_identity_types'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '04_dtl_user_identities'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '05_dtl_user_credentials'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '06_trx_auth_sessions'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '07_trx_login_attempts'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '08_trx_auth_challenges'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '09_aud_auth_events'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '22_aud_access_events'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '27_aud_product_events'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '32_aud_org_events'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_auth_manage' AND table_name = '37_aud_workspace_events'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '03_notifications' AND table_name = '09_dim_variable_queries'
    UNION ALL SELECT 1 FROM information_schema.tables WHERE table_schema = '05_grc_library' AND table_name = '32_lnk_cross_framework_equivalences'
) t;  -- Expected: 13

-- Verify identity type seed data
SELECT code, name FROM "03_auth_manage"."01_dim_identity_types" ORDER BY sort_order;

-- Verify new columns
SELECT column_name FROM information_schema.columns
WHERE table_schema = '03_auth_manage' AND table_name = '18_lnk_group_memberships'
  AND column_name IN ('scope_org_id', 'scope_workspace_id');

SELECT column_name FROM information_schema.columns
WHERE table_schema = '03_auth_manage' AND table_name = '48_lnk_grc_access_grants'
  AND column_name IN ('created_at', 'granted_by', 'revoked_by');

SELECT column_name FROM information_schema.columns
WHERE table_schema = '09_attachments' AND table_name = '01_fct_attachments'
  AND column_name IN ('auditor_access', 'published_for_audit_at', 'published_for_audit_by');

SELECT column_name FROM information_schema.columns
WHERE table_schema = '20_ai' AND table_name = '45_fct_job_queue'
  AND column_name = 'progress_pct';

SELECT column_name FROM information_schema.columns
WHERE table_schema = '20_ai' AND table_name = '50_fct_reports'
  AND column_name IN ('auditor_access', 'published_for_audit_at', 'published_for_audit_by');

-- Verify views
SELECT table_name FROM information_schema.views
WHERE table_schema = '03_auth_manage' AND table_name IN ('10_vw_auth_users', 'v_grc_team');

SELECT table_name FROM information_schema.views
WHERE table_schema = '12_engagements' AND table_name = '40_vw_engagement_detail';
*/

-- =============================================================================
-- END OF MIGRATION
-- =============================================================================
