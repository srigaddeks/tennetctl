-- ─────────────────────────────────────────────────────────────────────────
-- NOTIFICATION SYSTEM SCHEMA
-- ─────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS "03_notifications";

-- ─────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES (02-09)
-- ─────────────────────────────────────────────────────────────────────────

-- 02_dim_notification_channels: Delivery channels
CREATE TABLE IF NOT EXISTS "03_notifications"."02_dim_notification_channels" (
    id           UUID         NOT NULL,
    code         VARCHAR(50)  NOT NULL,
    name         VARCHAR(100) NOT NULL,
    description  TEXT         NOT NULL,
    is_available BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order   INTEGER      NOT NULL,
    created_at   TIMESTAMP    NOT NULL,
    updated_at   TIMESTAMP    NOT NULL,
    CONSTRAINT pk_02_dim_notification_channels      PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_notification_channels_code UNIQUE (code)
);

-- 03_dim_notification_categories: Logical groupings for preference hierarchy
CREATE TABLE IF NOT EXISTS "03_notifications"."03_dim_notification_categories" (
    id           UUID         NOT NULL,
    code         VARCHAR(50)  NOT NULL,
    name         VARCHAR(100) NOT NULL,
    description  TEXT         NOT NULL,
    is_mandatory BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order   INTEGER      NOT NULL,
    created_at   TIMESTAMP    NOT NULL,
    updated_at   TIMESTAMP    NOT NULL,
    CONSTRAINT pk_03_dim_notification_categories      PRIMARY KEY (id),
    CONSTRAINT uq_03_dim_notification_categories_code UNIQUE (code)
);

-- 04_dim_notification_types: Specific notification triggers
CREATE TABLE IF NOT EXISTS "03_notifications"."04_dim_notification_types" (
    id                UUID         NOT NULL,
    code              VARCHAR(100) NOT NULL,
    name              VARCHAR(150) NOT NULL,
    description       TEXT         NOT NULL,
    category_code     VARCHAR(50)  NOT NULL,
    is_mandatory      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_user_triggered BOOLEAN      NOT NULL DEFAULT TRUE,
    default_enabled   BOOLEAN      NOT NULL DEFAULT TRUE,
    cooldown_seconds  INTEGER      NULL,
    sort_order        INTEGER      NOT NULL,
    created_at        TIMESTAMP    NOT NULL,
    updated_at        TIMESTAMP    NOT NULL,
    CONSTRAINT pk_04_dim_notification_types      PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_notification_types_code UNIQUE (code),
    CONSTRAINT fk_04_dim_notification_types_category_03_dim
        FOREIGN KEY (category_code)
        REFERENCES "03_notifications"."03_dim_notification_categories" (code)
        ON DELETE RESTRICT
);

-- 05_dim_notification_statuses: Lifecycle statuses for queued notifications
CREATE TABLE IF NOT EXISTS "03_notifications"."05_dim_notification_statuses" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_05_dim_notification_statuses      PRIMARY KEY (id),
    CONSTRAINT uq_05_dim_notification_statuses_code UNIQUE (code)
);

-- 06_dim_notification_priorities: Priority levels for queue ordering
CREATE TABLE IF NOT EXISTS "03_notifications"."06_dim_notification_priorities" (
    id                       UUID         NOT NULL,
    code                     VARCHAR(30)  NOT NULL,
    name                     VARCHAR(100) NOT NULL,
    description              TEXT         NOT NULL,
    weight                   INTEGER      NOT NULL,
    max_retry_attempts       INTEGER      NOT NULL,
    retry_base_delay_seconds INTEGER      NOT NULL,
    sort_order               INTEGER      NOT NULL,
    created_at               TIMESTAMP    NOT NULL,
    updated_at               TIMESTAMP    NOT NULL,
    CONSTRAINT pk_06_dim_notification_priorities      PRIMARY KEY (id),
    CONSTRAINT uq_06_dim_notification_priorities_code UNIQUE (code)
);

-- 07_dim_notification_channel_types: Matrix of which channels each notification type supports
CREATE TABLE IF NOT EXISTS "03_notifications"."07_dim_notification_channel_types" (
    id                     UUID         NOT NULL,
    notification_type_code VARCHAR(100) NOT NULL,
    channel_code           VARCHAR(50)  NOT NULL,
    priority_code          VARCHAR(30)  NOT NULL DEFAULT 'normal',
    is_default             BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    CONSTRAINT pk_07_dim_notification_channel_types PRIMARY KEY (id),
    CONSTRAINT uq_07_dim_nct_type_channel UNIQUE (notification_type_code, channel_code),
    CONSTRAINT fk_07_dim_nct_type_04_dim
        FOREIGN KEY (notification_type_code)
        REFERENCES "03_notifications"."04_dim_notification_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_07_dim_nct_channel_02_dim
        FOREIGN KEY (channel_code)
        REFERENCES "03_notifications"."02_dim_notification_channels" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_07_dim_nct_priority_06_dim
        FOREIGN KEY (priority_code)
        REFERENCES "03_notifications"."06_dim_notification_priorities" (code)
        ON DELETE RESTRICT
);

-- 08_dim_template_variable_keys: Valid placeholder variables for templates
-- resolution_source tells the system WHERE to get the value:
--   'audit_property' = from audit event properties dict
--   'user_property'  = from 05_dtl_user_properties (by recipient user_id)
--   'actor_property' = from 05_dtl_user_properties (by actor_id)
--   'org'            = from 29_fct_orgs (by org_id from audit properties)
--   'workspace'      = from 34_fct_workspaces (by workspace_id from audit properties)
--   'settings'       = from application settings (platform.name, etc.)
--   'computed'       = computed at runtime (timestamp, action_url)
-- resolution_key is the specific field/property_key to query (e.g. 'display_name', 'email', 'name')
CREATE TABLE IF NOT EXISTS "03_notifications"."08_dim_template_variable_keys" (
    id                UUID         NOT NULL,
    code              VARCHAR(100) NOT NULL,
    name              VARCHAR(150) NOT NULL,
    description       TEXT         NOT NULL,
    data_type         VARCHAR(30)  NOT NULL DEFAULT 'string',
    example_value     TEXT         NULL,
    resolution_source VARCHAR(50)  NOT NULL DEFAULT 'audit_property',
    resolution_key    VARCHAR(100) NULL,
    sort_order        INTEGER      NOT NULL,
    created_at        TIMESTAMP    NOT NULL,
    updated_at        TIMESTAMP    NOT NULL,
    CONSTRAINT pk_08_dim_template_variable_keys      PRIMARY KEY (id),
    CONSTRAINT uq_08_dim_template_variable_keys_code UNIQUE (code),
    CONSTRAINT ck_08_dim_template_variable_keys_source
        CHECK (resolution_source IN ('audit_property', 'user_property', 'actor_property', 'user_group', 'tenant', 'org', 'workspace', 'settings', 'computed'))
);

-- 09_dim_tracking_event_types: Types of delivery/tracking events
CREATE TABLE IF NOT EXISTS "03_notifications"."09_dim_tracking_event_types" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_09_dim_tracking_event_types      PRIMARY KEY (id),
    CONSTRAINT uq_09_dim_tracking_event_types_code UNIQUE (code)
);

-- ─────────────────────────────────────────────────────────────────────────
-- FACT TABLES (10-13)
-- ─────────────────────────────────────────────────────────────────────────

-- 10_fct_templates: Notification template registry
-- NOTE: active_version_id FK is added via ALTER TABLE after 14_dtl_template_versions exists
CREATE TABLE IF NOT EXISTS "03_notifications"."10_fct_templates" (
    id                     UUID         NOT NULL,
    tenant_key             VARCHAR(100) NOT NULL,
    code                   VARCHAR(100) NOT NULL,
    name                   VARCHAR(200) NOT NULL,
    description            TEXT         NOT NULL,
    notification_type_code VARCHAR(100) NOT NULL,
    channel_code           VARCHAR(50)  NOT NULL,
    active_version_id      UUID         NULL,
    base_template_id       UUID         NULL,
    is_active              BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled            BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test                BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system              BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked              BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    created_by             UUID         NULL,
    updated_by             UUID         NULL,
    deleted_at             TIMESTAMP    NULL,
    deleted_by             UUID         NULL,
    CONSTRAINT pk_10_fct_templates PRIMARY KEY (id),
    CONSTRAINT uq_10_fct_templates_tenant_code UNIQUE (tenant_key, code),
    CONSTRAINT fk_10_fct_templates_type_04_dim
        FOREIGN KEY (notification_type_code)
        REFERENCES "03_notifications"."04_dim_notification_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_10_fct_templates_channel_02_dim
        FOREIGN KEY (channel_code)
        REFERENCES "03_notifications"."02_dim_notification_channels" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_10_fct_templates_base_10_fct
        FOREIGN KEY (base_template_id)
        REFERENCES "03_notifications"."10_fct_templates" (id)
        ON DELETE SET NULL
);

-- 11_fct_notification_rules: Maps audit events to notification dispatch
CREATE TABLE IF NOT EXISTS "03_notifications"."11_fct_notification_rules" (
    id                     UUID         NOT NULL,
    tenant_key             VARCHAR(100) NOT NULL,
    code                   VARCHAR(100) NOT NULL,
    name                   VARCHAR(200) NOT NULL,
    description            TEXT         NOT NULL,
    source_event_type      VARCHAR(100) NOT NULL,
    source_event_category  VARCHAR(50)  NULL,
    notification_type_code VARCHAR(100) NOT NULL,
    recipient_strategy     VARCHAR(50)  NOT NULL,
    recipient_filter_json  TEXT         NULL,
    priority_code          VARCHAR(30)  NOT NULL DEFAULT 'normal',
    delay_seconds          INTEGER      NOT NULL DEFAULT 0,
    is_active              BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled            BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test                BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system              BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked              BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    created_by             UUID         NULL,
    updated_by             UUID         NULL,
    deleted_at             TIMESTAMP    NULL,
    deleted_by             UUID         NULL,
    CONSTRAINT pk_11_fct_notification_rules PRIMARY KEY (id),
    CONSTRAINT uq_11_fct_notification_rules_tenant_code UNIQUE (tenant_key, code),
    CONSTRAINT fk_11_fct_rules_type_04_dim
        FOREIGN KEY (notification_type_code)
        REFERENCES "03_notifications"."04_dim_notification_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_11_fct_rules_priority_06_dim
        FOREIGN KEY (priority_code)
        REFERENCES "03_notifications"."06_dim_notification_priorities" (code)
        ON DELETE RESTRICT,
    CONSTRAINT ck_11_fct_rules_recipient_strategy
        CHECK (recipient_strategy IN ('actor', 'entity_owner', 'org_members', 'workspace_members', 'all_users', 'specific_users'))
);

-- 12_fct_broadcasts: Admin-initiated broadcast notifications
CREATE TABLE IF NOT EXISTS "03_notifications"."12_fct_broadcasts" (
    id                     UUID         NOT NULL,
    tenant_key             VARCHAR(100) NOT NULL,
    title                  VARCHAR(300) NOT NULL,
    body_text              TEXT         NOT NULL,
    body_html              TEXT         NULL,
    scope                  VARCHAR(30)  NOT NULL,
    scope_org_id           UUID         NULL,
    scope_workspace_id     UUID         NULL,
    notification_type_code VARCHAR(100) NOT NULL,
    priority_code          VARCHAR(30)  NOT NULL DEFAULT 'normal',
    severity               VARCHAR(30)  NULL,
    is_critical            BOOLEAN      NOT NULL DEFAULT FALSE,
    template_code          VARCHAR(100) NULL,
    scheduled_at           TIMESTAMP    NULL,
    sent_at                TIMESTAMP    NULL,
    total_recipients       INTEGER      NULL,
    is_active              BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted             BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    created_by             UUID         NOT NULL,
    CONSTRAINT pk_12_fct_broadcasts PRIMARY KEY (id),
    CONSTRAINT fk_12_fct_broadcasts_type_04_dim
        FOREIGN KEY (notification_type_code)
        REFERENCES "03_notifications"."04_dim_notification_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_12_fct_broadcasts_priority_06_dim
        FOREIGN KEY (priority_code)
        REFERENCES "03_notifications"."06_dim_notification_priorities" (code)
        ON DELETE RESTRICT,
    CONSTRAINT ck_12_fct_broadcasts_scope
        CHECK (scope IN ('global', 'org', 'workspace')),
    CONSTRAINT ck_12_fct_broadcasts_severity
        CHECK (severity IS NULL OR severity IN ('critical', 'high', 'medium', 'low', 'info'))
);

-- 13_fct_web_push_subscriptions: Web Push subscription storage
CREATE TABLE IF NOT EXISTS "03_notifications"."13_fct_web_push_subscriptions" (
    id           UUID         NOT NULL,
    user_id      UUID         NOT NULL,
    tenant_key   VARCHAR(100) NOT NULL,
    endpoint     TEXT         NOT NULL,
    p256dh_key   TEXT         NOT NULL,
    auth_key     TEXT         NOT NULL,
    user_agent   VARCHAR(512) NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted   BOOLEAN      NOT NULL DEFAULT FALSE,
    last_used_at TIMESTAMP    NULL,
    created_at   TIMESTAMP    NOT NULL,
    updated_at   TIMESTAMP    NOT NULL,
    CONSTRAINT pk_13_fct_web_push_subscriptions PRIMARY KEY (id),
    CONSTRAINT uq_13_fct_web_push_user_endpoint UNIQUE (user_id, endpoint),
    CONSTRAINT fk_13_fct_web_push_user_03_auth_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────
-- DETAIL / EAV TABLES (14-16)
-- ─────────────────────────────────────────────────────────────────────────

-- 14_dtl_template_versions: Versioned template content
CREATE TABLE IF NOT EXISTS "03_notifications"."14_dtl_template_versions" (
    id             UUID         NOT NULL,
    template_id    UUID         NOT NULL,
    version_number INTEGER      NOT NULL,
    subject_line   VARCHAR(500) NULL,
    body_html      TEXT         NULL,
    body_text      TEXT         NULL,
    body_short     VARCHAR(500) NULL,
    metadata_json  TEXT         NULL,
    change_notes   TEXT         NULL,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    CONSTRAINT pk_14_dtl_template_versions PRIMARY KEY (id),
    CONSTRAINT uq_14_dtl_template_versions_tpl_ver UNIQUE (template_id, version_number),
    CONSTRAINT fk_14_dtl_template_versions_tpl_10_fct
        FOREIGN KEY (template_id)
        REFERENCES "03_notifications"."10_fct_templates" (id)
        ON DELETE CASCADE
);

-- Add deferred FK from 10_fct_templates.active_version_id -> 14_dtl_template_versions.id
ALTER TABLE "03_notifications"."10_fct_templates"
    ADD CONSTRAINT fk_10_fct_templates_active_version_14_dtl
        FOREIGN KEY (active_version_id)
        REFERENCES "03_notifications"."14_dtl_template_versions" (id)
        ON DELETE SET NULL;

-- 15_dtl_template_placeholders: Required/optional placeholders per template
CREATE TABLE IF NOT EXISTS "03_notifications"."15_dtl_template_placeholders" (
    id                UUID         NOT NULL,
    template_id       UUID         NOT NULL,
    variable_key_code VARCHAR(100) NOT NULL,
    is_required       BOOLEAN      NOT NULL DEFAULT TRUE,
    default_value     TEXT         NULL,
    created_at        TIMESTAMP    NOT NULL,
    updated_at        TIMESTAMP    NOT NULL,
    CONSTRAINT pk_15_dtl_template_placeholders PRIMARY KEY (id),
    CONSTRAINT uq_15_dtl_template_placeholders_tpl_var UNIQUE (template_id, variable_key_code),
    CONSTRAINT fk_15_dtl_placeholders_tpl_10_fct
        FOREIGN KEY (template_id)
        REFERENCES "03_notifications"."10_fct_templates" (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_15_dtl_placeholders_var_08_dim
        FOREIGN KEY (variable_key_code)
        REFERENCES "03_notifications"."08_dim_template_variable_keys" (code)
        ON DELETE RESTRICT
);

-- 16_dtl_notification_properties: EAV properties for queue items
-- NOTE: FK to 20_trx_notification_queue is added via ALTER TABLE after that table exists
CREATE TABLE IF NOT EXISTS "03_notifications"."16_dtl_notification_properties" (
    id              UUID         NOT NULL,
    notification_id UUID         NOT NULL,
    property_key    VARCHAR(100) NOT NULL,
    property_value  TEXT         NULL,
    CONSTRAINT pk_16_dtl_notification_properties PRIMARY KEY (id),
    CONSTRAINT uq_16_dtl_notification_properties_nid_key UNIQUE (notification_id, property_key)
);

-- ─────────────────────────────────────────────────────────────────────────
-- LINK TABLES (17-18)
-- ─────────────────────────────────────────────────────────────────────────

-- 17_lnk_user_notification_preferences: Granular hierarchical user preference toggles
CREATE TABLE IF NOT EXISTS "03_notifications"."17_lnk_user_notification_preferences" (
    id                     UUID         NOT NULL,
    user_id                UUID         NOT NULL,
    tenant_key             VARCHAR(100) NOT NULL,
    scope_level            VARCHAR(30)  NOT NULL,
    channel_code           VARCHAR(50)  NULL,
    category_code          VARCHAR(50)  NULL,
    notification_type_code VARCHAR(100) NULL,
    scope_org_id           UUID         NULL,
    scope_workspace_id     UUID         NULL,
    is_enabled             BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    CONSTRAINT pk_17_lnk_user_notification_preferences PRIMARY KEY (id),
    CONSTRAINT fk_17_lnk_prefs_user_03_auth_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_17_lnk_prefs_channel_02_dim
        FOREIGN KEY (channel_code)
        REFERENCES "03_notifications"."02_dim_notification_channels" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_17_lnk_prefs_category_03_dim
        FOREIGN KEY (category_code)
        REFERENCES "03_notifications"."03_dim_notification_categories" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_17_lnk_prefs_type_04_dim
        FOREIGN KEY (notification_type_code)
        REFERENCES "03_notifications"."04_dim_notification_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT ck_17_lnk_prefs_scope_level
        CHECK (scope_level IN ('global', 'channel', 'category', 'type'))
);

-- Unique index using COALESCE for nullable columns
CREATE UNIQUE INDEX IF NOT EXISTS uq_17_lnk_prefs_composite
    ON "03_notifications"."17_lnk_user_notification_preferences" (
        user_id,
        tenant_key,
        scope_level,
        COALESCE(channel_code, ''),
        COALESCE(category_code, ''),
        COALESCE(notification_type_code, ''),
        COALESCE(scope_org_id, '00000000-0000-0000-0000-000000000000'),
        COALESCE(scope_workspace_id, '00000000-0000-0000-0000-000000000000')
    );

-- 18_lnk_notification_rule_channels: Which channels each rule dispatches to
CREATE TABLE IF NOT EXISTS "03_notifications"."18_lnk_notification_rule_channels" (
    id            UUID         NOT NULL,
    rule_id       UUID         NOT NULL,
    channel_code  VARCHAR(50)  NOT NULL,
    template_code VARCHAR(100) NULL,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    CONSTRAINT pk_18_lnk_notification_rule_channels PRIMARY KEY (id),
    CONSTRAINT uq_18_lnk_rule_channels_rule_channel UNIQUE (rule_id, channel_code),
    CONSTRAINT fk_18_lnk_rule_channels_rule_11_fct
        FOREIGN KEY (rule_id)
        REFERENCES "03_notifications"."11_fct_notification_rules" (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_18_lnk_rule_channels_channel_02_dim
        FOREIGN KEY (channel_code)
        REFERENCES "03_notifications"."02_dim_notification_channels" (code)
        ON DELETE RESTRICT
);

-- 19_dtl_rule_conditions: Configurable conditions for notification rules
-- Enables UI-driven campaign definitions like "inactivity_days >= 7" or
-- "notification not opened after 48 hours" without code changes.
-- condition_type: 'property_check' | 'inactivity' | 'engagement' | 'schedule'
-- operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in' | 'contains' | 'is_null' | 'is_not_null'
CREATE TABLE IF NOT EXISTS "03_notifications"."19_dtl_rule_conditions" (
    id              UUID         NOT NULL,
    rule_id         UUID         NOT NULL,
    condition_type  VARCHAR(50)  NOT NULL,
    field_key       VARCHAR(150) NOT NULL,
    operator        VARCHAR(20)  NOT NULL,
    value           TEXT         NULL,
    value_type      VARCHAR(30)  NOT NULL DEFAULT 'string',
    logical_group   INTEGER      NOT NULL DEFAULT 0,
    sort_order      INTEGER      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP    NOT NULL,
    updated_at      TIMESTAMP    NOT NULL,
    CONSTRAINT pk_19_dtl_rule_conditions PRIMARY KEY (id),
    CONSTRAINT fk_19_dtl_rule_conditions_rule_11_fct
        FOREIGN KEY (rule_id)
        REFERENCES "03_notifications"."11_fct_notification_rules" (id)
        ON DELETE CASCADE,
    CONSTRAINT ck_19_dtl_rule_conditions_type
        CHECK (condition_type IN ('property_check', 'inactivity', 'engagement', 'schedule')),
    CONSTRAINT ck_19_dtl_rule_conditions_operator
        CHECK (operator IN ('eq', 'neq', 'gt', 'gte', 'lt', 'lte', 'in', 'not_in', 'contains', 'is_null', 'is_not_null'))
);

-- Index for fast rule condition lookups
CREATE INDEX IF NOT EXISTS idx_19_dtl_rule_conditions_rule
    ON "03_notifications"."19_dtl_rule_conditions" (rule_id)
    WHERE is_active = TRUE;

-- 24_trx_campaign_runs: Tracks periodic/scheduled campaign executions
-- Each campaign run evaluates rules with conditions and dispatches notifications
CREATE TABLE IF NOT EXISTS "03_notifications"."24_trx_campaign_runs" (
    id               UUID         NOT NULL,
    tenant_key       VARCHAR(100) NOT NULL,
    rule_id          UUID         NOT NULL,
    run_type         VARCHAR(30)  NOT NULL,
    started_at       TIMESTAMP    NOT NULL,
    completed_at     TIMESTAMP    NULL,
    users_evaluated  INTEGER      NOT NULL DEFAULT 0,
    users_matched    INTEGER      NOT NULL DEFAULT 0,
    notifications_created INTEGER NOT NULL DEFAULT 0,
    status           VARCHAR(30)  NOT NULL DEFAULT 'running',
    error_message    TEXT         NULL,
    created_at       TIMESTAMP    NOT NULL,
    CONSTRAINT pk_24_trx_campaign_runs PRIMARY KEY (id),
    CONSTRAINT fk_24_trx_campaign_runs_rule_11_fct
        FOREIGN KEY (rule_id)
        REFERENCES "03_notifications"."11_fct_notification_rules" (id)
        ON DELETE CASCADE,
    CONSTRAINT ck_24_trx_campaign_runs_type
        CHECK (run_type IN ('scheduled', 'manual', 'periodic')),
    CONSTRAINT ck_24_trx_campaign_runs_status
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS idx_24_trx_campaign_runs_rule
    ON "03_notifications"."24_trx_campaign_runs" (rule_id, created_at DESC);

-- ─────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLES (20-23)
-- ─────────────────────────────────────────────────────────────────────────

-- 20_trx_notification_queue: The outbound notification queue
CREATE TABLE IF NOT EXISTS "03_notifications"."20_trx_notification_queue" (
    id                     UUID         NOT NULL,
    tenant_key             VARCHAR(100) NOT NULL,
    user_id                UUID         NOT NULL,
    notification_type_code VARCHAR(100) NOT NULL,
    channel_code           VARCHAR(50)  NOT NULL,
    status_code            VARCHAR(50)  NOT NULL,
    priority_code          VARCHAR(30)  NOT NULL DEFAULT 'normal',
    template_id            UUID         NULL,
    template_version_id    UUID         NULL,
    source_audit_event_id  UUID         NULL,
    source_rule_id         UUID         NULL,
    broadcast_id           UUID         NULL,
    rendered_subject       VARCHAR(500) NULL,
    rendered_body          TEXT         NULL,
    recipient_email        VARCHAR(320) NULL,
    recipient_push_endpoint TEXT        NULL,
    scheduled_at           TIMESTAMP    NOT NULL,
    attempt_count          INTEGER      NOT NULL DEFAULT 0,
    max_attempts           INTEGER      NOT NULL DEFAULT 3,
    next_retry_at          TIMESTAMP    NULL,
    last_error             TEXT         NULL,
    idempotency_key        VARCHAR(200) NULL,
    created_at             TIMESTAMP    NOT NULL,
    updated_at             TIMESTAMP    NOT NULL,
    completed_at           TIMESTAMP    NULL,
    CONSTRAINT pk_20_trx_notification_queue PRIMARY KEY (id),
    CONSTRAINT fk_20_trx_queue_user_03_auth_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_20_trx_queue_type_04_dim
        FOREIGN KEY (notification_type_code)
        REFERENCES "03_notifications"."04_dim_notification_types" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_20_trx_queue_channel_02_dim
        FOREIGN KEY (channel_code)
        REFERENCES "03_notifications"."02_dim_notification_channels" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_20_trx_queue_status_05_dim
        FOREIGN KEY (status_code)
        REFERENCES "03_notifications"."05_dim_notification_statuses" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_20_trx_queue_priority_06_dim
        FOREIGN KEY (priority_code)
        REFERENCES "03_notifications"."06_dim_notification_priorities" (code)
        ON DELETE RESTRICT,
    CONSTRAINT fk_20_trx_queue_template_10_fct
        FOREIGN KEY (template_id)
        REFERENCES "03_notifications"."10_fct_templates" (id)
        ON DELETE SET NULL,
    CONSTRAINT fk_20_trx_queue_version_14_dtl
        FOREIGN KEY (template_version_id)
        REFERENCES "03_notifications"."14_dtl_template_versions" (id)
        ON DELETE SET NULL,
    CONSTRAINT fk_20_trx_queue_rule_11_fct
        FOREIGN KEY (source_rule_id)
        REFERENCES "03_notifications"."11_fct_notification_rules" (id)
        ON DELETE SET NULL,
    CONSTRAINT fk_20_trx_queue_broadcast_12_fct
        FOREIGN KEY (broadcast_id)
        REFERENCES "03_notifications"."12_fct_broadcasts" (id)
        ON DELETE SET NULL
);

-- Add deferred FK on 16_dtl_notification_properties -> 20_trx_notification_queue
ALTER TABLE "03_notifications"."16_dtl_notification_properties"
    ADD CONSTRAINT fk_16_dtl_notification_properties_nid_20_trx
        FOREIGN KEY (notification_id)
        REFERENCES "03_notifications"."20_trx_notification_queue" (id)
        ON DELETE CASCADE;

-- 21_trx_delivery_log: Immutable log of every delivery attempt
CREATE TABLE IF NOT EXISTS "03_notifications"."21_trx_delivery_log" (
    id                  UUID         NOT NULL,
    notification_id     UUID         NOT NULL,
    channel_code        VARCHAR(50)  NOT NULL,
    attempt_number      INTEGER      NOT NULL,
    status              VARCHAR(50)  NOT NULL,
    provider_response   TEXT         NULL,
    provider_message_id VARCHAR(200) NULL,
    error_code          VARCHAR(100) NULL,
    error_message       TEXT         NULL,
    duration_ms         INTEGER      NULL,
    occurred_at         TIMESTAMP    NOT NULL,
    created_at          TIMESTAMP    NOT NULL,
    CONSTRAINT pk_21_trx_delivery_log PRIMARY KEY (id),
    CONSTRAINT fk_21_trx_delivery_log_nid_20_trx
        FOREIGN KEY (notification_id)
        REFERENCES "03_notifications"."20_trx_notification_queue" (id)
        ON DELETE CASCADE
);

-- 22_trx_tracking_events: Email opens, clicks, push interactions
CREATE TABLE IF NOT EXISTS "03_notifications"."22_trx_tracking_events" (
    id                       UUID         NOT NULL,
    notification_id          UUID         NOT NULL,
    tracking_event_type_code VARCHAR(50)  NOT NULL,
    channel_code             VARCHAR(50)  NOT NULL,
    click_url                TEXT         NULL,
    user_agent               VARCHAR(512) NULL,
    ip_address               VARCHAR(64)  NULL,
    occurred_at              TIMESTAMP    NOT NULL,
    created_at               TIMESTAMP    NOT NULL,
    CONSTRAINT pk_22_trx_tracking_events PRIMARY KEY (id),
    CONSTRAINT fk_22_trx_tracking_nid_20_trx
        FOREIGN KEY (notification_id)
        REFERENCES "03_notifications"."20_trx_notification_queue" (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_22_trx_tracking_type_09_dim
        FOREIGN KEY (tracking_event_type_code)
        REFERENCES "03_notifications"."09_dim_tracking_event_types" (code)
        ON DELETE RESTRICT
);

-- 23_trx_inactivity_snapshots: Tracks user activity for inactivity alerts
CREATE TABLE IF NOT EXISTS "03_notifications"."23_trx_inactivity_snapshots" (
    id                UUID         NOT NULL,
    user_id           UUID         NOT NULL,
    tenant_key        VARCHAR(100) NOT NULL,
    last_login_at     TIMESTAMP    NULL,
    last_notified_at  TIMESTAMP    NULL,
    inactivity_days   INTEGER      NOT NULL,
    notification_sent BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP    NOT NULL,
    updated_at        TIMESTAMP    NOT NULL,
    CONSTRAINT pk_23_trx_inactivity_snapshots PRIMARY KEY (id),
    CONSTRAINT uq_23_trx_inactivity_snapshots_user UNIQUE (user_id),
    CONSTRAINT fk_23_trx_inactivity_user_03_auth_users
        FOREIGN KEY (user_id)
        REFERENCES "03_auth_manage"."03_fct_users" (id)
        ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────

-- Queue polling index (most critical for performance)
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_processing
    ON "03_notifications"."20_trx_notification_queue" (priority_code, scheduled_at)
    WHERE status_code IN ('queued', 'processing');

-- User notification history
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_user_timeline
    ON "03_notifications"."20_trx_notification_queue" (user_id, created_at);

-- Retry polling
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_retry
    ON "03_notifications"."20_trx_notification_queue" (next_retry_at)
    WHERE status_code = 'failed' AND attempt_count < max_attempts;

-- Idempotency check
CREATE UNIQUE INDEX IF NOT EXISTS idx_20_trx_queue_idempotency
    ON "03_notifications"."20_trx_notification_queue" (idempotency_key)
    WHERE idempotency_key IS NOT NULL;

-- Broadcast tracking
CREATE INDEX IF NOT EXISTS idx_20_trx_queue_broadcast
    ON "03_notifications"."20_trx_notification_queue" (broadcast_id)
    WHERE broadcast_id IS NOT NULL;

-- Delivery log by notification
CREATE INDEX IF NOT EXISTS idx_21_trx_delivery_log_nid
    ON "03_notifications"."21_trx_delivery_log" (notification_id, attempt_number);

-- Tracking events by notification
CREATE INDEX IF NOT EXISTS idx_22_trx_tracking_events_nid
    ON "03_notifications"."22_trx_tracking_events" (notification_id, occurred_at);

-- Template lookup by type and channel
CREATE INDEX IF NOT EXISTS idx_10_fct_templates_type_channel
    ON "03_notifications"."10_fct_templates" (notification_type_code, channel_code)
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- Rules lookup by event type
CREATE INDEX IF NOT EXISTS idx_11_fct_rules_event_type
    ON "03_notifications"."11_fct_notification_rules" (source_event_type)
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- Web push subscriptions by user
CREATE INDEX IF NOT EXISTS idx_13_fct_web_push_user
    ON "03_notifications"."13_fct_web_push_subscriptions" (user_id)
    WHERE is_deleted = FALSE AND is_active = TRUE;

-- User preferences by user
CREATE INDEX IF NOT EXISTS idx_17_lnk_prefs_user
    ON "03_notifications"."17_lnk_user_notification_preferences" (user_id, tenant_key);

-- ─────────────────────────────────────────────────────────────────────────
-- VIEWS (40-42)
-- ─────────────────────────────────────────────────────────────────────────

-- 40_vw_notification_delivery_summary
CREATE OR REPLACE VIEW "03_notifications"."40_vw_notification_delivery_summary" AS
SELECT
    q.tenant_key,
    q.notification_type_code,
    q.channel_code,
    q.status_code,
    COUNT(*) AS total_count,
    DATE_TRUNC('hour', q.created_at) AS hour_bucket
FROM "03_notifications"."20_trx_notification_queue" q
GROUP BY q.tenant_key, q.notification_type_code, q.channel_code, q.status_code, DATE_TRUNC('hour', q.created_at);

-- 41_vw_user_preference_matrix: Effective preferences per user
CREATE OR REPLACE VIEW "03_notifications"."41_vw_user_preference_matrix" AS
SELECT
    u.id AS user_id,
    u.tenant_key,
    nt.code AS notification_type_code,
    nc.code AS category_code,
    ch.code AS channel_code,
    nt.is_mandatory OR nc.is_mandatory AS is_mandatory,
    COALESCE(
        type_pref.is_enabled,
        cat_pref.is_enabled,
        chan_pref.is_enabled,
        global_pref.is_enabled,
        nct.is_default,
        nt.default_enabled
    ) AS effective_enabled
FROM "03_auth_manage"."03_fct_users" u
CROSS JOIN "03_notifications"."04_dim_notification_types" nt
CROSS JOIN "03_notifications"."02_dim_notification_channels" ch
JOIN "03_notifications"."03_dim_notification_categories" nc ON nc.code = nt.category_code
LEFT JOIN "03_notifications"."07_dim_notification_channel_types" nct
    ON nct.notification_type_code = nt.code AND nct.channel_code = ch.code
LEFT JOIN "03_notifications"."17_lnk_user_notification_preferences" global_pref
    ON global_pref.user_id = u.id AND global_pref.tenant_key = u.tenant_key
    AND global_pref.scope_level = 'global'
    AND global_pref.scope_org_id IS NULL AND global_pref.scope_workspace_id IS NULL
LEFT JOIN "03_notifications"."17_lnk_user_notification_preferences" chan_pref
    ON chan_pref.user_id = u.id AND chan_pref.tenant_key = u.tenant_key
    AND chan_pref.scope_level = 'channel' AND chan_pref.channel_code = ch.code
    AND chan_pref.scope_org_id IS NULL AND chan_pref.scope_workspace_id IS NULL
LEFT JOIN "03_notifications"."17_lnk_user_notification_preferences" cat_pref
    ON cat_pref.user_id = u.id AND cat_pref.tenant_key = u.tenant_key
    AND cat_pref.scope_level = 'category' AND cat_pref.category_code = nc.code
    AND (cat_pref.channel_code = ch.code OR cat_pref.channel_code IS NULL)
    AND cat_pref.scope_org_id IS NULL AND cat_pref.scope_workspace_id IS NULL
LEFT JOIN "03_notifications"."17_lnk_user_notification_preferences" type_pref
    ON type_pref.user_id = u.id AND type_pref.tenant_key = u.tenant_key
    AND type_pref.scope_level = 'type' AND type_pref.notification_type_code = nt.code
    AND (type_pref.channel_code = ch.code OR type_pref.channel_code IS NULL)
    AND type_pref.scope_org_id IS NULL AND type_pref.scope_workspace_id IS NULL
WHERE u.is_deleted = FALSE AND ch.is_available = TRUE;

-- 42_vw_template_catalog: Templates with active version info
CREATE OR REPLACE VIEW "03_notifications"."42_vw_template_catalog" AS
SELECT
    t.id AS template_id,
    t.tenant_key,
    t.code AS template_code,
    t.name AS template_name,
    t.notification_type_code,
    t.channel_code,
    t.is_active,
    v.version_number AS active_version,
    v.subject_line,
    v.created_at AS version_created_at,
    t.created_at,
    t.updated_at
FROM "03_notifications"."10_fct_templates" t
LEFT JOIN "03_notifications"."14_dtl_template_versions" v ON v.id = t.active_version_id
WHERE t.is_deleted = FALSE;

-- ─────────────────────────────────────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────────────────────────────────────

-- Channels
INSERT INTO "03_notifications"."02_dim_notification_channels" (id, code, name, description, is_available, sort_order, created_at, updated_at) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'email', 'Email', 'Email notifications via SMTP or API provider', TRUE, 1, NOW(), NOW()),
    ('a0000000-0000-0000-0000-000000000002', 'web_push', 'Web Push', 'Browser push notifications via Web Push API', TRUE, 2, NOW(), NOW()),
    ('a0000000-0000-0000-0000-000000000003', 'whatsapp', 'WhatsApp', 'WhatsApp messaging notifications', FALSE, 3, NOW(), NOW()),
    ('a0000000-0000-0000-0000-000000000004', 'slack', 'Slack', 'Slack workspace notifications', FALSE, 4, NOW(), NOW()),
    ('a0000000-0000-0000-0000-000000000005', 'gchat', 'Google Chat', 'Google Chat notifications', FALSE, 5, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Categories
INSERT INTO "03_notifications"."03_dim_notification_categories" (id, code, name, description, is_mandatory, sort_order, created_at, updated_at) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'security', 'Security', 'Security-related notifications that cannot be disabled', TRUE, 1, NOW(), NOW()),
    ('b0000000-0000-0000-0000-000000000002', 'transactional', 'Transactional', 'Transaction confirmations and mandatory system responses', TRUE, 2, NOW(), NOW()),
    ('b0000000-0000-0000-0000-000000000003', 'system', 'System', 'Platform-wide system notifications and announcements', FALSE, 3, NOW(), NOW()),
    ('b0000000-0000-0000-0000-000000000004', 'org', 'Organization', 'Organization-related notifications', FALSE, 4, NOW(), NOW()),
    ('b0000000-0000-0000-0000-000000000005', 'workspace', 'Workspace', 'Workspace-related notifications', FALSE, 5, NOW(), NOW()),
    ('b0000000-0000-0000-0000-000000000006', 'engagement', 'Engagement', 'User engagement and activity notifications', FALSE, 6, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Notification types
INSERT INTO "03_notifications"."04_dim_notification_types" (id, code, name, description, category_code, is_mandatory, is_user_triggered, default_enabled, cooldown_seconds, sort_order, created_at, updated_at) VALUES
    -- Security (mandatory)
    ('c0000000-0000-0000-0000-000000000001', 'password_reset', 'Password Reset', 'Password reset OTP or link notification', 'security', TRUE, TRUE, TRUE, NULL, 1, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000002', 'email_verification', 'Email Verification', 'Email verification code or link', 'security', TRUE, TRUE, TRUE, NULL, 2, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000003', 'login_from_new_device', 'Login From New Device', 'Alert when login occurs from unrecognized device or IP', 'security', TRUE, TRUE, TRUE, 3600, 3, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000004', 'api_key_created', 'API Key Created', 'Notification when a new API key is created for the account', 'security', TRUE, TRUE, TRUE, NULL, 4, NOW(), NOW()),
    -- Transactional (mandatory)
    ('c0000000-0000-0000-0000-000000000005', 'password_changed', 'Password Changed', 'Confirmation that password was changed', 'transactional', TRUE, TRUE, TRUE, NULL, 5, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000006', 'email_verified', 'Email Verified', 'Confirmation that email was verified', 'transactional', TRUE, TRUE, TRUE, NULL, 6, NOW(), NOW()),
    -- Org
    ('c0000000-0000-0000-0000-000000000007', 'org_invite_received', 'Organization Invite Received', 'Notification when user is invited to an organization', 'org', FALSE, FALSE, TRUE, NULL, 7, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000008', 'org_member_added', 'Organization Member Added', 'Notification when a new member joins the organization', 'org', FALSE, FALSE, TRUE, NULL, 8, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000009', 'org_member_removed', 'Organization Member Removed', 'Notification when a member is removed from the organization', 'org', FALSE, FALSE, TRUE, NULL, 9, NOW(), NOW()),
    ('c0000000-0000-0000-0000-00000000000a', 'org_broadcast', 'Organization Broadcast', 'Admin broadcast to all organization members', 'org', FALSE, FALSE, TRUE, NULL, 10, NOW(), NOW()),
    -- Workspace
    ('c0000000-0000-0000-0000-00000000000b', 'workspace_invite_received', 'Workspace Invite Received', 'Notification when user is invited to a workspace', 'workspace', FALSE, FALSE, TRUE, NULL, 11, NOW(), NOW()),
    ('c0000000-0000-0000-0000-00000000000c', 'workspace_member_added', 'Workspace Member Added', 'Notification when a new member joins the workspace', 'workspace', FALSE, FALSE, TRUE, NULL, 12, NOW(), NOW()),
    ('c0000000-0000-0000-0000-00000000000d', 'workspace_member_removed', 'Workspace Member Removed', 'Notification when a member is removed from the workspace', 'workspace', FALSE, FALSE, TRUE, NULL, 13, NOW(), NOW()),
    ('c0000000-0000-0000-0000-00000000000e', 'workspace_broadcast', 'Workspace Broadcast', 'Admin broadcast to all workspace members', 'workspace', FALSE, FALSE, TRUE, NULL, 14, NOW(), NOW()),
    -- System
    ('c0000000-0000-0000-0000-00000000000f', 'global_broadcast', 'Global Broadcast', 'Platform-wide broadcast to all users', 'system', FALSE, FALSE, TRUE, NULL, 15, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000010', 'role_changed', 'Role Changed', 'Notification when user role is changed', 'system', FALSE, FALSE, TRUE, NULL, 16, NOW(), NOW()),
    -- Engagement
    ('c0000000-0000-0000-0000-000000000011', 'inactivity_reminder', 'Inactivity Reminder', 'Reminder sent when user has not logged in for configured period', 'engagement', FALSE, FALSE, TRUE, 86400, 17, NOW(), NOW()),
    -- Platform announcements
    ('c0000000-0000-0000-0000-000000000012', 'platform_release', 'Platform Release', 'New platform version or feature release notification', 'system', FALSE, FALSE, TRUE, NULL, 18, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000013', 'platform_incident', 'Platform Incident', 'Platform incident or outage notification', 'system', FALSE, FALSE, TRUE, NULL, 19, NOW(), NOW()),
    ('c0000000-0000-0000-0000-000000000014', 'platform_maintenance', 'Scheduled Maintenance', 'Scheduled platform maintenance window notification', 'system', FALSE, FALSE, TRUE, NULL, 20, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Statuses
INSERT INTO "03_notifications"."05_dim_notification_statuses" (id, code, name, description, is_terminal, sort_order, created_at, updated_at) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'queued', 'Queued', 'Notification is queued for processing', FALSE, 1, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000002', 'processing', 'Processing', 'Notification is being processed by a worker', FALSE, 2, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000003', 'sent', 'Sent', 'Notification was sent to the provider', FALSE, 3, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000004', 'delivered', 'Delivered', 'Provider confirmed delivery to recipient', TRUE, 4, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000005', 'opened', 'Opened', 'Recipient opened the notification', TRUE, 5, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000006', 'clicked', 'Clicked', 'Recipient clicked a link in the notification', TRUE, 6, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000007', 'failed', 'Failed', 'Delivery attempt failed, may be retried', FALSE, 7, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000008', 'bounced', 'Bounced', 'Email bounced or push endpoint invalid', TRUE, 8, NOW(), NOW()),
    ('d0000000-0000-0000-0000-000000000009', 'suppressed', 'Suppressed', 'Notification suppressed due to user preference', TRUE, 9, NOW(), NOW()),
    ('d0000000-0000-0000-0000-00000000000a', 'dead_letter', 'Dead Letter', 'All retry attempts exhausted', TRUE, 10, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Priorities
INSERT INTO "03_notifications"."06_dim_notification_priorities" (id, code, name, description, weight, max_retry_attempts, retry_base_delay_seconds, sort_order, created_at, updated_at) VALUES
    ('e0000000-0000-0000-0000-000000000001', 'critical', 'Critical', 'Highest priority, processed first with maximum retries', 100, 5, 30, 1, NOW(), NOW()),
    ('e0000000-0000-0000-0000-000000000002', 'high', 'High', 'High priority with elevated retry attempts', 75, 4, 60, 2, NOW(), NOW()),
    ('e0000000-0000-0000-0000-000000000003', 'normal', 'Normal', 'Standard priority for most notifications', 50, 3, 120, 3, NOW(), NOW()),
    ('e0000000-0000-0000-0000-000000000004', 'low', 'Low', 'Low priority for non-urgent notifications', 25, 2, 300, 4, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Channel-Type matrix (which notification types support which channels)
INSERT INTO "03_notifications"."07_dim_notification_channel_types" (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at) VALUES
    -- Security notifications: email only, critical priority
    ('f0000000-0000-0000-0000-000000000001', 'password_reset', 'email', 'critical', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000002', 'email_verification', 'email', 'critical', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000003', 'login_from_new_device', 'email', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000004', 'login_from_new_device', 'web_push', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000005', 'api_key_created', 'email', 'high', TRUE, NOW(), NOW()),
    -- Transactional: email only
    ('f0000000-0000-0000-0000-000000000006', 'password_changed', 'email', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000007', 'email_verified', 'email', 'normal', TRUE, NOW(), NOW()),
    -- Org: email + web_push
    ('f0000000-0000-0000-0000-000000000008', 'org_invite_received', 'email', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000009', 'org_invite_received', 'web_push', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000000a', 'org_member_added', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000000b', 'org_member_added', 'web_push', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000000c', 'org_member_removed', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000000d', 'org_broadcast', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000000e', 'org_broadcast', 'web_push', 'normal', TRUE, NOW(), NOW()),
    -- Workspace: email + web_push
    ('f0000000-0000-0000-0000-00000000000f', 'workspace_invite_received', 'email', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000010', 'workspace_invite_received', 'web_push', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000011', 'workspace_member_added', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000012', 'workspace_member_added', 'web_push', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000013', 'workspace_member_removed', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000014', 'workspace_broadcast', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000015', 'workspace_broadcast', 'web_push', 'normal', TRUE, NOW(), NOW()),
    -- System: email + web_push
    ('f0000000-0000-0000-0000-000000000016', 'global_broadcast', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000017', 'global_broadcast', 'web_push', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000018', 'role_changed', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000019', 'role_changed', 'web_push', 'normal', TRUE, NOW(), NOW()),
    -- Engagement: email only
    ('f0000000-0000-0000-0000-00000000001a', 'inactivity_reminder', 'email', 'low', TRUE, NOW(), NOW()),
    -- Platform announcements: email + web_push
    ('f0000000-0000-0000-0000-00000000001b', 'platform_release', 'email', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000001c', 'platform_release', 'web_push', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000001d', 'platform_incident', 'email', 'critical', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000001e', 'platform_incident', 'web_push', 'critical', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-00000000001f', 'platform_maintenance', 'email', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000020', 'platform_maintenance', 'web_push', 'high', TRUE, NOW(), NOW())
ON CONFLICT (notification_type_code, channel_code) DO NOTHING;

-- Template variable keys (with resolution_source + resolution_key for smart variable population)
INSERT INTO "03_notifications"."08_dim_template_variable_keys" (id, code, name, description, data_type, example_value, resolution_source, resolution_key, sort_order, created_at, updated_at) VALUES
    ('10000000-0000-0000-0000-000000000001', 'user.display_name', 'User Display Name', 'The display name of the recipient user', 'string', 'John Doe', 'user_property', 'display_name', 1, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000002', 'user.email', 'User Email', 'The email address of the recipient user', 'email', 'john@example.com', 'user_property', 'email', 2, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000011', 'user.first_name', 'User First Name', 'The first name of the recipient user', 'string', 'John', 'user_property', 'first_name', 3, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000012', 'user.last_name', 'User Last Name', 'The last name of the recipient user', 'string', 'Doe', 'user_property', 'last_name', 4, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000013', 'user.username', 'Username', 'The username of the recipient user', 'string', 'johndoe', 'user_property', 'username', 5, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000003', 'org.name', 'Organization Name', 'The name of the relevant organization', 'string', 'Acme Corp', 'org', 'name', 6, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000014', 'org.slug', 'Organization Slug', 'The URL slug of the relevant organization', 'string', 'acme-corp', 'org', 'slug', 7, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000004', 'workspace.name', 'Workspace Name', 'The name of the relevant workspace', 'string', 'Engineering', 'workspace', 'name', 8, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000015', 'workspace.slug', 'Workspace Slug', 'The URL slug of the relevant workspace', 'string', 'engineering', 'workspace', 'slug', 9, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000005', 'action_url', 'Action URL', 'The URL for the primary call-to-action', 'url', 'https://app.example.com/verify?token=abc', 'audit_property', 'action_url', 10, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000006', 'token', 'Token', 'A verification or reset token', 'string', 'abc123def456', 'audit_property', 'token', 11, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000007', 'platform.name', 'Platform Name', 'The name of the platform', 'string', 'kcontrol', 'settings', 'notification_from_name', 12, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000008', 'expiry_hours', 'Expiry Hours', 'Number of hours until a token or link expires', 'integer', '24', 'audit_property', 'expiry_hours', 13, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000009', 'ip_address', 'IP Address', 'Client IP address associated with the event', 'string', '192.168.1.1', 'audit_property', 'ip_address', 14, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000000a', 'device_info', 'Device Info', 'User agent or device information', 'string', 'Chrome on macOS', 'audit_property', 'device_info', 15, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000000b', 'timestamp', 'Timestamp', 'Human-readable timestamp of the event', 'string', '2026-03-15 14:30:00 UTC', 'computed', 'event_timestamp', 16, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000000c', 'actor.display_name', 'Actor Display Name', 'The display name of the user who performed the action', 'string', 'Jane Admin', 'actor_property', 'display_name', 17, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000016', 'actor.email', 'Actor Email', 'The email address of the user who performed the action', 'email', 'jane@example.com', 'actor_property', 'email', 18, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000000d', 'role.name', 'Role Name', 'The name of the role being assigned or changed', 'string', 'Workspace Admin', 'audit_property', 'role_name', 19, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000000e', 'api_key.name', 'API Key Name', 'The name/label of the API key', 'string', 'Production Key', 'audit_property', 'api_key_name', 20, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000000f', 'broadcast.title', 'Broadcast Title', 'The title of the broadcast message', 'string', 'Important Update', 'audit_property', 'broadcast_title', 21, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000010', 'broadcast.body', 'Broadcast Body', 'The body content of the broadcast message', 'string', 'Please read this important announcement...', 'audit_property', 'broadcast_body', 22, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000017', 'unsubscribe_url', 'Unsubscribe URL', 'URL for user to manage notification preferences', 'url', 'https://app.example.com/settings/notifications', 'computed', 'unsubscribe_url', 23, NOW(), NOW()),
    -- User group variables
    ('10000000-0000-0000-0000-000000000018', 'group.name', 'User Group Name', 'The name of the user''s primary group', 'string', 'Engineering Team', 'user_group', 'name', 24, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000019', 'group.code', 'User Group Code', 'The code of the user''s primary group', 'string', 'engineering', 'user_group', 'code', 25, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000001a', 'group.description', 'User Group Description', 'The description of the user''s primary group', 'string', 'Platform engineering team', 'user_group', 'description', 26, NOW(), NOW()),
    -- Tenant-level variables
    ('10000000-0000-0000-0000-00000000001b', 'tenant.key', 'Tenant Key', 'The tenant identifier', 'string', 'acme', 'tenant', 'tenant_key', 27, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000001c', 'tenant.user_count', 'Tenant User Count', 'Total active users in the tenant', 'integer', '150', 'tenant', 'user_count', 28, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000001d', 'tenant.org_count', 'Tenant Org Count', 'Total active organizations in the tenant', 'integer', '5', 'tenant', 'org_count', 29, NOW(), NOW()),
    -- Release/incident variables
    ('10000000-0000-0000-0000-00000000001e', 'release.version', 'Release Version', 'Version number of the platform release', 'string', 'v2.1.0', 'audit_property', 'release_version', 30, NOW(), NOW()),
    ('10000000-0000-0000-0000-00000000001f', 'release.title', 'Release Title', 'Title of the platform release', 'string', 'Performance Improvements', 'audit_property', 'release_title', 31, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000020', 'release.summary', 'Release Summary', 'Brief summary of the release', 'string', 'Bug fixes and performance improvements', 'audit_property', 'release_summary', 32, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000021', 'release.changelog_url', 'Changelog URL', 'URL to the full release changelog', 'url', 'https://docs.example.com/changelog/v2.1.0', 'audit_property', 'changelog_url', 33, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000022', 'incident.title', 'Incident Title', 'Title of the platform incident', 'string', 'API Latency Degradation', 'audit_property', 'incident_title', 34, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000023', 'incident.severity', 'Incident Severity', 'Severity level of the incident', 'string', 'major', 'audit_property', 'incident_severity', 35, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000024', 'incident.status', 'Incident Status', 'Current status of the incident', 'string', 'investigating', 'audit_property', 'incident_status', 36, NOW(), NOW()),
    ('10000000-0000-0000-0000-000000000025', 'incident.affected_components', 'Affected Components', 'Components affected by the incident', 'string', 'API, Dashboard', 'audit_property', 'affected_components', 37, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Tracking event types
INSERT INTO "03_notifications"."09_dim_tracking_event_types" (id, code, name, description, sort_order, created_at, updated_at) VALUES
    ('20000000-0000-0000-0000-000000000001', 'queued', 'Queued', 'Notification entered the queue', 1, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000002', 'sent', 'Sent', 'Notification sent to provider', 2, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000003', 'delivered', 'Delivered', 'Provider confirmed delivery', 3, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000004', 'opened', 'Opened', 'Recipient opened the notification', 4, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000005', 'clicked', 'Clicked', 'Recipient clicked a link', 5, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000006', 'bounced', 'Bounced', 'Notification bounced', 6, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000007', 'failed', 'Failed', 'Delivery failed', 7, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000008', 'dismissed', 'Dismissed', 'Push notification dismissed by user', 8, NOW(), NOW()),
    ('20000000-0000-0000-0000-000000000009', 'unsubscribed', 'Unsubscribed', 'User unsubscribed via notification link', 9, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────
-- SEED NOTIFICATION RULES (map existing audit events to notifications)
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."11_fct_notification_rules" (id, tenant_key, code, name, description, source_event_type, source_event_category, notification_type_code, recipient_strategy, priority_code, is_active, is_system, created_at, updated_at) VALUES
    ('30000000-0000-0000-0000-000000000001', 'default', 'rule_password_reset', 'Password Reset Notification', 'Send password reset link/OTP to user', 'password_reset_requested', 'auth', 'password_reset', 'actor', 'critical', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000002', 'default', 'rule_email_verification', 'Email Verification Notification', 'Send email verification link to user', 'email_verification_requested', 'auth', 'email_verification', 'actor', 'critical', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000003', 'default', 'rule_password_changed', 'Password Changed Confirmation', 'Confirm password change to user', 'password_changed', 'auth', 'password_changed', 'actor', 'high', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000004', 'default', 'rule_email_verified', 'Email Verified Confirmation', 'Confirm email verification to user', 'email_verification_completed', 'auth', 'email_verified', 'actor', 'normal', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000005', 'default', 'rule_api_key_created', 'API Key Created Alert', 'Alert user when new API key is created', 'api_key_created', 'auth', 'api_key_created', 'actor', 'high', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000006', 'default', 'rule_org_invite', 'Organization Invite', 'Notify user of organization invitation', 'invite_created', 'org', 'org_invite_received', 'specific_users', 'high', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000007', 'default', 'rule_org_member_added', 'Org Member Added', 'Notify org admins when member is added', 'org_member_added', 'org', 'org_member_added', 'org_members', 'normal', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000008', 'default', 'rule_workspace_member_added', 'Workspace Member Added', 'Notify workspace admins when member is added', 'workspace_member_added', 'workspace', 'workspace_member_added', 'workspace_members', 'normal', TRUE, TRUE, NOW(), NOW()),
    ('30000000-0000-0000-0000-000000000009', 'default', 'rule_role_changed', 'Role Changed', 'Notify user when their role changes', 'group_role_assigned', 'access', 'role_changed', 'actor', 'normal', TRUE, TRUE, NOW(), NOW())
ON CONFLICT (tenant_key, code) DO NOTHING;

-- Seed: inactivity campaign rule (evaluated by campaign runner, not by audit events)
-- source_event_type = '__campaign__' means this rule is not triggered by audit events
INSERT INTO "03_notifications"."11_fct_notification_rules" (id, tenant_key, code, name, description, source_event_type, source_event_category, notification_type_code, recipient_strategy, priority_code, is_active, is_system, created_at, updated_at) VALUES
    ('30000000-0000-0000-0000-000000000010', 'default', 'campaign_inactivity_7d', 'Inactivity Reminder (7 days)', 'Send reminder to users inactive for 7+ days', '__campaign__', NULL, 'inactivity_reminder', 'all_users', 'low', TRUE, TRUE, NOW(), NOW())
ON CONFLICT (tenant_key, code) DO NOTHING;

-- Seed: condition for the inactivity campaign
INSERT INTO "03_notifications"."19_dtl_rule_conditions" (id, rule_id, condition_type, field_key, operator, value, value_type, logical_group, sort_order, is_active, created_at, updated_at) VALUES
    ('40000000-0000-0000-0000-000000000001', '30000000-0000-0000-0000-000000000010', 'inactivity', 'inactivity_days', 'gte', '7', 'integer', 0, 0, TRUE, NOW(), NOW())
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────
-- RELEASES & INCIDENTS
-- ─────────────────────────────────────────────────────────────────────────

-- 25_fct_releases: Platform release notes / changelog
CREATE TABLE IF NOT EXISTS "03_notifications"."25_fct_releases" (
    id              UUID         NOT NULL,
    tenant_key      VARCHAR(100) NOT NULL,
    version         VARCHAR(50)  NOT NULL,
    title           VARCHAR(300) NOT NULL,
    summary         VARCHAR(500) NOT NULL,
    body_markdown   TEXT         NULL,
    body_html       TEXT         NULL,
    changelog_url   VARCHAR(500) NULL,
    status          VARCHAR(30)  NOT NULL DEFAULT 'draft',
    release_date    TIMESTAMP    NULL,
    published_at    TIMESTAMP    NULL,
    broadcast_id    UUID         NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP    NOT NULL,
    updated_at      TIMESTAMP    NOT NULL,
    created_by      UUID         NOT NULL,
    CONSTRAINT pk_25_fct_releases PRIMARY KEY (id),
    CONSTRAINT ck_25_fct_releases_status
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT uq_25_fct_releases_version UNIQUE (tenant_key, version)
);

CREATE INDEX IF NOT EXISTS ix_25_fct_releases_tenant_status
    ON "03_notifications"."25_fct_releases" (tenant_key, status, created_at DESC)
    WHERE is_deleted = FALSE;

-- 26_fct_incidents: Platform incident tracking
CREATE TABLE IF NOT EXISTS "03_notifications"."26_fct_incidents" (
    id                   UUID         NOT NULL,
    tenant_key           VARCHAR(100) NOT NULL,
    title                VARCHAR(300) NOT NULL,
    description          TEXT         NOT NULL,
    severity             VARCHAR(30)  NOT NULL,
    status               VARCHAR(30)  NOT NULL DEFAULT 'investigating',
    affected_components  VARCHAR(500) NULL,
    started_at           TIMESTAMP    NOT NULL,
    resolved_at          TIMESTAMP    NULL,
    broadcast_id         UUID         NULL,
    is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMP    NOT NULL,
    updated_at           TIMESTAMP    NOT NULL,
    created_by           UUID         NOT NULL,
    CONSTRAINT pk_26_fct_incidents PRIMARY KEY (id),
    CONSTRAINT ck_26_fct_incidents_severity
        CHECK (severity IN ('critical', 'major', 'minor', 'informational')),
    CONSTRAINT ck_26_fct_incidents_status
        CHECK (status IN ('investigating', 'identified', 'monitoring', 'resolved'))
);

CREATE INDEX IF NOT EXISTS ix_26_fct_incidents_tenant_status
    ON "03_notifications"."26_fct_incidents" (tenant_key, status, created_at DESC)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS ix_26_fct_incidents_active
    ON "03_notifications"."26_fct_incidents" (tenant_key, created_at DESC)
    WHERE is_deleted = FALSE AND status != 'resolved';

-- 27_dtl_incident_updates: Status updates for incidents
CREATE TABLE IF NOT EXISTS "03_notifications"."27_dtl_incident_updates" (
    id              UUID         NOT NULL,
    incident_id     UUID         NOT NULL,
    status          VARCHAR(30)  NOT NULL,
    message         TEXT         NOT NULL,
    is_public       BOOLEAN      NOT NULL DEFAULT TRUE,
    broadcast_id    UUID         NULL,
    created_at      TIMESTAMP    NOT NULL,
    created_by      UUID         NOT NULL,
    CONSTRAINT pk_27_dtl_incident_updates PRIMARY KEY (id),
    CONSTRAINT fk_27_dtl_incident_updates_incident
        FOREIGN KEY (incident_id)
        REFERENCES "03_notifications"."26_fct_incidents" (id)
        ON DELETE CASCADE,
    CONSTRAINT ck_27_dtl_incident_updates_status
        CHECK (status IN ('investigating', 'identified', 'monitoring', 'resolved'))
);

CREATE INDEX IF NOT EXISTS ix_27_dtl_incident_updates_incident
    ON "03_notifications"."27_dtl_incident_updates" (incident_id, created_at ASC);

-- ─────────────────────────────────────────────────────────────────────────
-- COMMENTS
-- ─────────────────────────────────────────────────────────────────────────

COMMENT ON SCHEMA "03_notifications" IS 'Enterprise notification system: templates, queue, delivery tracking, user preferences.';

COMMENT ON TABLE "03_notifications"."02_dim_notification_channels" IS 'Available notification delivery channels (email, web_push, etc.).';
COMMENT ON TABLE "03_notifications"."03_dim_notification_categories" IS 'Notification categories for preference hierarchy grouping.';
COMMENT ON TABLE "03_notifications"."04_dim_notification_types" IS 'Specific notification triggers with category, mandatory flag, and cooldown.';
COMMENT ON TABLE "03_notifications"."05_dim_notification_statuses" IS 'Lifecycle statuses for queued notifications.';
COMMENT ON TABLE "03_notifications"."06_dim_notification_priorities" IS 'Priority levels controlling queue ordering and retry behavior.';
COMMENT ON TABLE "03_notifications"."07_dim_notification_channel_types" IS 'Matrix defining which channels each notification type supports.';
COMMENT ON TABLE "03_notifications"."08_dim_template_variable_keys" IS 'Valid placeholder variable keys for template rendering.';
COMMENT ON TABLE "03_notifications"."09_dim_tracking_event_types" IS 'Types of delivery and engagement tracking events.';
COMMENT ON TABLE "03_notifications"."10_fct_templates" IS 'Notification template registry with versioning and layout inheritance.';
COMMENT ON TABLE "03_notifications"."11_fct_notification_rules" IS 'Rules mapping audit events to notification dispatch with recipient strategies.';
COMMENT ON TABLE "03_notifications"."12_fct_broadcasts" IS 'Admin-initiated broadcast notifications with scope targeting.';
COMMENT ON TABLE "03_notifications"."13_fct_web_push_subscriptions" IS 'Web Push API subscription storage per user and device.';
COMMENT ON TABLE "03_notifications"."14_dtl_template_versions" IS 'Versioned template content with HTML, text, and short bodies.';
COMMENT ON TABLE "03_notifications"."15_dtl_template_placeholders" IS 'Required and optional placeholder declarations per template.';
COMMENT ON TABLE "03_notifications"."16_dtl_notification_properties" IS 'EAV properties for notification queue items.';
COMMENT ON TABLE "03_notifications"."17_lnk_user_notification_preferences" IS 'Hierarchical user notification preferences with scope overrides.';
COMMENT ON TABLE "03_notifications"."18_lnk_notification_rule_channels" IS 'Channel dispatch configuration per notification rule.';
COMMENT ON TABLE "03_notifications"."20_trx_notification_queue" IS 'Outbound notification queue with priority, retry, and idempotency.';
COMMENT ON TABLE "03_notifications"."21_trx_delivery_log" IS 'Immutable delivery attempt log with provider responses.';
COMMENT ON TABLE "03_notifications"."22_trx_tracking_events" IS 'Email open, click, and push interaction tracking events.';
COMMENT ON TABLE "03_notifications"."23_trx_inactivity_snapshots" IS 'User activity tracking for inactivity-based notification triggers.';
COMMENT ON TABLE "03_notifications"."19_dtl_rule_conditions" IS 'Configurable conditions for notification rules (campaigns): inactivity, engagement, schedule.';
COMMENT ON TABLE "03_notifications"."24_trx_campaign_runs" IS 'Tracks periodic campaign evaluation runs with match/dispatch statistics.';
COMMENT ON TABLE "03_notifications"."25_fct_releases" IS 'Platform release notes and changelog entries with publish workflow.';
COMMENT ON TABLE "03_notifications"."26_fct_incidents" IS 'Platform incident tracking with severity, status, and auto-broadcast.';
COMMENT ON TABLE "03_notifications"."27_dtl_incident_updates" IS 'Status updates and communications for incidents.';
