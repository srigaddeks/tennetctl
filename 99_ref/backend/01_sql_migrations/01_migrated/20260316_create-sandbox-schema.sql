-- ===========================================================================
-- Migration: Create sandbox schema
-- Date: 2026-03-16
-- Description: K-Control Sandbox — live compliance system for building,
--              testing, and promoting runtime control tests.
--
--   Chain: Connectors → Datasets → Signals → Threat Types → Policies → Actions
--
--   Signals are granular Python functions stored in DB, executed in a
--   RestrictedPython + subprocess sandbox.  Threat types compose signals
--   via AND/OR/NOT expression trees.  Policies attach to threat types
--   and determine automated responses (notifications, evidence reports,
--   RCA agents, escalation).
--
--   SSF/CAEP/RISC compliant — every signal can emit a standards-compliant
--   Security Event Token (SET) for Zero Trust / Continuous Adaptive Trust.
--
-- Row-Level Security (RLS) notes:
--   All fact tables carry tenant_key.  If RLS is enabled in a future phase,
--   policies should filter by tenant_key using a current_setting session var.
--   Live session data goes to ClickHouse, not PostgreSQL.
-- ===========================================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- SHARED TRIGGER FUNCTION — auto-update updated_at
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION "15_sandbox".fn_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ═══════════════════════════════════════════════════════════════════════════════
-- DIMENSION TABLES (02-10)
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 02_dim_connector_categories — top-level grouping for connector types
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."02_dim_connector_categories" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_02_dim_connector_categories       PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_connector_categories_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."02_dim_connector_categories" (code, name, description, sort_order) VALUES
    ('cloud_infrastructure',     'Cloud Infrastructure',     'AWS, Azure, GCP cloud platforms',             1),
    ('identity_provider',        'Identity Provider',        'Okta, Azure AD, Google Workspace',            2),
    ('source_control',           'Source Control',           'GitHub, GitLab, Bitbucket',                   3),
    ('project_management',       'Project Management',       'Jira, ServiceNow, Linear',                   4),
    ('database',                 'Database',                 'PostgreSQL, MySQL, MongoDB',                  5),
    ('container_orchestration',  'Container Orchestration',  'Kubernetes, Docker, ECS',                     6),
    ('logging_monitoring',       'Logging & Monitoring',     'Datadog, Splunk, Elastic, CloudWatch',        7),
    ('itsm',                     'IT Service Management',    'ServiceNow, PagerDuty',                       8),
    ('communication',            'Communication',            'Slack, Microsoft Teams',                       9),
    ('custom',                   'Custom',                   'Custom API or webhook integrations',          10)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 03_dim_connector_types — specific integration types (FK → category)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."03_dim_connector_types" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    code            VARCHAR(50)  NOT NULL,
    name            VARCHAR(100) NOT NULL,
    category_code   VARCHAR(50)  NOT NULL,
    auth_method     VARCHAR(50)  NOT NULL DEFAULT 'api_key',  -- oauth2, api_key, iam_role, basic, connection_string
    description     TEXT,
    sort_order      INTEGER      NOT NULL DEFAULT 0,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_03_dim_connector_types       PRIMARY KEY (id),
    CONSTRAINT uq_03_dim_connector_types_code  UNIQUE (code),
    CONSTRAINT ck_03_dim_connector_types_auth  CHECK (auth_method IN ('oauth2','api_key','iam_role','basic','connection_string','certificate','saml')),
    CONSTRAINT fk_03_dim_connector_types_cat   FOREIGN KEY (category_code)
        REFERENCES "15_sandbox"."02_dim_connector_categories" (code)
);

INSERT INTO "15_sandbox"."03_dim_connector_types" (code, name, category_code, auth_method, sort_order) VALUES
    -- Cloud Infrastructure
    ('aws_iam',          'AWS IAM',              'cloud_infrastructure', 'iam_role',  1),
    ('aws_cloudtrail',   'AWS CloudTrail',       'cloud_infrastructure', 'iam_role',  2),
    ('aws_config',       'AWS Config',           'cloud_infrastructure', 'iam_role',  3),
    ('aws_s3',           'AWS S3',               'cloud_infrastructure', 'iam_role',  4),
    ('azure_ad',         'Azure Active Directory','cloud_infrastructure','oauth2',    5),
    ('azure_policy',     'Azure Policy',         'cloud_infrastructure', 'oauth2',    6),
    ('azure_monitor',    'Azure Monitor',        'cloud_infrastructure', 'oauth2',    7),
    ('gcp_iam',          'GCP IAM',              'cloud_infrastructure', 'oauth2',    8),
    ('gcp_audit',        'GCP Audit Log',        'cloud_infrastructure', 'oauth2',    9),
    -- Identity Provider
    ('okta',             'Okta',                 'identity_provider',    'api_key',  10),
    ('google_workspace', 'Google Workspace',     'identity_provider',    'oauth2',   11),
    -- Source Control
    ('github',           'GitHub',               'source_control',       'api_key',  12),
    ('gitlab',           'GitLab',               'source_control',       'api_key',  13),
    ('bitbucket',        'Bitbucket',            'source_control',       'api_key',  14),
    -- Project Management
    ('jira',             'Jira',                 'project_management',   'api_key',  15),
    ('servicenow',       'ServiceNow',           'itsm',                 'basic',    16),
    -- Database
    ('postgresql',       'PostgreSQL',           'database',             'connection_string', 17),
    ('mysql',            'MySQL',                'database',             'connection_string', 18),
    ('mongodb',          'MongoDB',              'database',             'connection_string', 19),
    -- Container Orchestration
    ('kubernetes',       'Kubernetes',           'container_orchestration','certificate', 20),
    -- Logging & Monitoring
    ('datadog',          'Datadog',              'logging_monitoring',   'api_key',  21),
    ('splunk',           'Splunk',               'logging_monitoring',   'api_key',  22),
    ('elastic',          'Elastic',              'logging_monitoring',   'api_key',  23),
    -- Communication
    ('slack',            'Slack',                'communication',        'oauth2',   24),
    -- Custom
    ('custom_api',       'Custom API',           'custom',               'api_key',  25),
    ('custom_webhook',   'Custom Webhook',       'custom',               'api_key',  26)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 04_dim_signal_statuses — signal lifecycle states
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."04_dim_signal_statuses" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_04_dim_signal_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_signal_statuses_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."04_dim_signal_statuses" (code, name, is_terminal, sort_order) VALUES
    ('draft',     'Draft',     FALSE, 1),
    ('testing',   'Testing',   FALSE, 2),
    ('validated', 'Validated', FALSE, 3),
    ('promoted',  'Promoted',  TRUE,  4),
    ('archived',  'Archived',  TRUE,  5)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 05_dim_dataset_sources — how a dataset was created
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."05_dim_dataset_sources" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_05_dim_dataset_sources       PRIMARY KEY (id),
    CONSTRAINT uq_05_dim_dataset_sources_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."05_dim_dataset_sources" (code, name, description, sort_order) VALUES
    ('manual_json',     'Manual JSON',      'Hand-typed JSON in editor',                  1),
    ('manual_upload',   'File Upload',      'Uploaded .json file',                        2),
    ('live_capture',    'Live Capture',     'Data captured during a live session',         3),
    ('connector_pull',  'Connector Pull',   'Scheduled or on-demand collection',          4),
    ('template',        'Template',         'Started from a predefined template',         5),
    ('composite',       'Composite',        'Mixed sources with field-level overrides',   6)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 06_dim_execution_statuses — sandbox run states
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."06_dim_execution_statuses" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_06_dim_execution_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_06_dim_execution_statuses_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."06_dim_execution_statuses" (code, name, is_terminal, sort_order) VALUES
    ('queued',     'Queued',     FALSE, 1),
    ('running',    'Running',    FALSE, 2),
    ('completed',  'Completed',  TRUE,  3),
    ('failed',     'Failed',     TRUE,  4),
    ('timeout',    'Timeout',    TRUE,  5),
    ('cancelled',  'Cancelled',  TRUE,  6)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 07_dim_dataset_templates — predefined dataset shapes per connector type
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."07_dim_dataset_templates" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    code                VARCHAR(100) NOT NULL,
    connector_type_code VARCHAR(50)  NOT NULL,
    name                VARCHAR(200) NOT NULL,
    description         TEXT,
    json_schema         JSONB        NOT NULL DEFAULT '{}',  -- expected JSON structure (keys + types)
    sample_payload      JSONB        NOT NULL DEFAULT '{}',  -- realistic example data
    sort_order          INTEGER      NOT NULL DEFAULT 0,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_07_dim_dataset_templates       PRIMARY KEY (id),
    CONSTRAINT uq_07_dim_dataset_templates_code  UNIQUE (code),
    CONSTRAINT fk_07_dim_dataset_templates_type  FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);


-- ---------------------------------------------------------------------------
-- 08_dim_threat_severities — threat severity levels
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."08_dim_threat_severities" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(30)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_08_dim_threat_severities       PRIMARY KEY (id),
    CONSTRAINT uq_08_dim_threat_severities_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."08_dim_threat_severities" (code, name, sort_order) VALUES
    ('info',     'Informational', 1),
    ('low',      'Low',           2),
    ('medium',   'Medium',        3),
    ('high',     'High',          4),
    ('critical', 'Critical',      5)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 09_dim_policy_action_types — what policies can trigger
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."09_dim_policy_action_types" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_09_dim_policy_action_types       PRIMARY KEY (id),
    CONSTRAINT uq_09_dim_policy_action_types_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."09_dim_policy_action_types" (code, name, description, sort_order) VALUES
    ('notification',     'Notification',      'Send alert via configured channel',            1),
    ('evidence_report',  'Evidence Report',   'Generate compliance evidence document',        2),
    ('rca_agent',        'RCA Agent',         'Run root cause analysis agent',                3),
    ('escalate',         'Escalate',          'Escalate to specified role/user',               4),
    ('create_task',      'Create Task',       'Create remediation task in task manager',       5),
    ('webhook',          'Webhook',           'Send HTTP POST to external URL',                6),
    ('disable_access',   'Disable Access',    'Revoke user/session access',                    7),
    ('quarantine',       'Quarantine',        'Isolate resource for investigation',             8)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 10_dim_library_types — library classification
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."10_dim_library_types" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_10_dim_library_types       PRIMARY KEY (id),
    CONSTRAINT uq_10_dim_library_types_code  UNIQUE (code)
);

INSERT INTO "15_sandbox"."10_dim_library_types" (code, name, sort_order) VALUES
    ('asset_security', 'Asset Security',  1),
    ('compliance',     'Compliance',      2),
    ('operational',    'Operational',     3),
    ('custom',         'Custom',          4)
ON CONFLICT (code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 11_dim_asset_versions — version variants per connector type
-- e.g., kubernetes 1.29, 1.31; postgresql 14, 16; aws_iam v2023, v2024
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."11_dim_asset_versions" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    connector_type_code VARCHAR(50)  NOT NULL,
    version_code        VARCHAR(50)  NOT NULL,  -- e.g., "1.29", "16", "v2024"
    version_label       VARCHAR(100) NOT NULL,  -- e.g., "Kubernetes 1.29", "PostgreSQL 16"
    is_latest           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    sort_order          INTEGER      NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_11_dim_asset_versions         PRIMARY KEY (id),
    CONSTRAINT uq_11_dim_asset_versions_code    UNIQUE (connector_type_code, version_code),
    CONSTRAINT fk_11_dim_asset_versions_type    FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);

INSERT INTO "15_sandbox"."11_dim_asset_versions" (connector_type_code, version_code, version_label, is_latest, sort_order) VALUES
    ('kubernetes',  '1.28', 'Kubernetes 1.28',  FALSE, 1),
    ('kubernetes',  '1.29', 'Kubernetes 1.29',  FALSE, 2),
    ('kubernetes',  '1.30', 'Kubernetes 1.30',  FALSE, 3),
    ('kubernetes',  '1.31', 'Kubernetes 1.31',  TRUE,  4),
    ('postgresql',  '14',   'PostgreSQL 14',    FALSE, 1),
    ('postgresql',  '15',   'PostgreSQL 15',    FALSE, 2),
    ('postgresql',  '16',   'PostgreSQL 16',    TRUE,  3),
    ('mysql',       '8.0',  'MySQL 8.0',        FALSE, 1),
    ('mysql',       '8.4',  'MySQL 8.4',        TRUE,  2),
    ('aws_iam',     'v2024','AWS IAM 2024',     FALSE, 1),
    ('aws_iam',     'v2025','AWS IAM 2025',     TRUE,  2)
ON CONFLICT (connector_type_code, version_code) DO NOTHING;


-- ---------------------------------------------------------------------------
-- 12_lnk_template_asset_versions — dataset templates are version-aware
-- A template can apply to multiple versions or be version-specific
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."12_lnk_template_asset_versions" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    template_code       VARCHAR(100) NOT NULL,
    asset_version_id    UUID         NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_12_lnk_tpl_ver             PRIMARY KEY (id),
    CONSTRAINT uq_12_lnk_tpl_ver             UNIQUE (template_code, asset_version_id),
    CONSTRAINT fk_12_lnk_tpl_ver_tpl         FOREIGN KEY (template_code)
        REFERENCES "15_sandbox"."07_dim_dataset_templates" (code),
    CONSTRAINT fk_12_lnk_tpl_ver_ver         FOREIGN KEY (asset_version_id)
        REFERENCES "15_sandbox"."11_dim_asset_versions" (id)
);


-- NOTE: 13_lnk_library_connector_types defined after 29_fct_libraries (FK dependency)


-- ═══════════════════════════════════════════════════════════════════════════════
-- FACT TABLES (20-30) — LEAN: only structural columns
-- Descriptive data (name, description, tags, etc.) lives in detail tables.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 20_fct_connector_instances — org-scoped integration configs
-- Multiple instances per type allowed (e.g., 3 AWS accounts).
-- name, description, base_url, region → 40_dtl_connector_instance_properties
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."20_fct_connector_instances" (
    id                   UUID         NOT NULL,
    tenant_key           VARCHAR(100) NOT NULL,
    org_id               UUID         NOT NULL,
    workspace_id         UUID         NULL,
    instance_code        VARCHAR(100) NOT NULL,
    connector_type_code  VARCHAR(50)  NOT NULL,
    asset_version_id     UUID         NULL,     -- e.g., K8s 1.31, PG 16 (NULL = version-agnostic)
    collection_schedule  VARCHAR(30)  NOT NULL DEFAULT 'manual',
    last_collected_at    TIMESTAMPTZ  NULL,
    health_status        VARCHAR(30)  NOT NULL DEFAULT 'unchecked',
    is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by           UUID         NULL,
    updated_by           UUID         NULL,
    deleted_at           TIMESTAMPTZ  NULL,
    deleted_by           UUID         NULL,

    CONSTRAINT pk_20_fct_connector_instances            PRIMARY KEY (id),
    CONSTRAINT uq_20_fct_connector_instances_code       UNIQUE (org_id, instance_code),
    CONSTRAINT ck_20_fct_connector_instances_schedule    CHECK (collection_schedule IN ('realtime','hourly','daily','weekly','manual')),
    CONSTRAINT ck_20_fct_connector_instances_health      CHECK (health_status IN ('healthy','degraded','error','unchecked')),
    CONSTRAINT ck_20_fct_connector_instances_deleted      CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
        OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    ),
    CONSTRAINT fk_20_fct_connector_instances_type       FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code),
    CONSTRAINT fk_20_fct_connector_instances_org        FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_20_fct_connector_instances_version  FOREIGN KEY (asset_version_id)
        REFERENCES "15_sandbox"."11_dim_asset_versions" (id)
);

CREATE INDEX IF NOT EXISTS idx_20_fct_connector_instances_org
    ON "15_sandbox"."20_fct_connector_instances" (org_id)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_20_fct_connector_instances_type
    ON "15_sandbox"."20_fct_connector_instances" (connector_type_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_20_fct_connector_instances_tenant
    ON "15_sandbox"."20_fct_connector_instances" (tenant_key)
    WHERE is_deleted = FALSE;

CREATE TRIGGER trg_20_fct_connector_instances_updated_at
    BEFORE UPDATE ON "15_sandbox"."20_fct_connector_instances"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 21_fct_datasets — simulation/reference datasets (lean fact)
-- name, description, json_schema, tags → 42_dtl_dataset_properties
-- Live logs go to ClickHouse, NOT here.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."21_fct_datasets" (
    id                      UUID         NOT NULL,
    tenant_key              VARCHAR(100) NOT NULL,
    org_id                  UUID         NOT NULL,
    workspace_id            UUID         NULL,
    connector_instance_id   UUID         NULL,
    dataset_code            VARCHAR(100) NOT NULL,
    dataset_source_code     VARCHAR(50)  NOT NULL,
    version_number          INTEGER      NOT NULL DEFAULT 1,
    schema_fingerprint      VARCHAR(64)  NULL,
    row_count               INTEGER      NULL,
    byte_size               BIGINT       NULL,
    collected_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    is_locked               BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted              BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID         NULL,
    updated_by              UUID         NULL,
    deleted_at              TIMESTAMPTZ  NULL,
    deleted_by              UUID         NULL,

    CONSTRAINT pk_21_fct_datasets              PRIMARY KEY (id),
    CONSTRAINT uq_21_fct_datasets_version      UNIQUE (org_id, dataset_code, version_number),
    CONSTRAINT ck_21_fct_datasets_deleted       CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
        OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    ),
    CONSTRAINT fk_21_fct_datasets_source       FOREIGN KEY (dataset_source_code)
        REFERENCES "15_sandbox"."05_dim_dataset_sources" (code),
    CONSTRAINT fk_21_fct_datasets_connector    FOREIGN KEY (connector_instance_id)
        REFERENCES "15_sandbox"."20_fct_connector_instances" (id),
    CONSTRAINT fk_21_fct_datasets_org          FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_21_fct_datasets_org
    ON "15_sandbox"."21_fct_datasets" (org_id)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_21_fct_datasets_connector
    ON "15_sandbox"."21_fct_datasets" (connector_instance_id)
    WHERE is_deleted = FALSE AND connector_instance_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_21_fct_datasets_workspace
    ON "15_sandbox"."21_fct_datasets" (workspace_id)
    WHERE is_deleted = FALSE AND workspace_id IS NOT NULL;

CREATE TRIGGER trg_21_fct_datasets_updated_at
    BEFORE UPDATE ON "15_sandbox"."21_fct_datasets"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 22_fct_signals — lean fact. Python source stored in 45_dtl_signal_properties.
-- name, description, python_source, source_prompt, tags, caep/risc types → EAV
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."22_fct_signals" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    workspace_id        UUID         NULL,
    signal_code         VARCHAR(100) NOT NULL,
    version_number      INTEGER      NOT NULL DEFAULT 1,
    signal_status_code  VARCHAR(50)  NOT NULL DEFAULT 'draft',
    python_hash         VARCHAR(64)  NULL,
    timeout_ms          INTEGER      NOT NULL DEFAULT 5000,
    max_memory_mb       INTEGER      NOT NULL DEFAULT 128,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    deleted_at          TIMESTAMPTZ  NULL,
    deleted_by          UUID         NULL,

    CONSTRAINT pk_22_fct_signals              PRIMARY KEY (id),
    CONSTRAINT uq_22_fct_signals_version      UNIQUE (org_id, signal_code, version_number),
    CONSTRAINT ck_22_fct_signals_deleted       CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
        OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    ),
    CONSTRAINT fk_22_fct_signals_status       FOREIGN KEY (signal_status_code)
        REFERENCES "15_sandbox"."04_dim_signal_statuses" (code),
    CONSTRAINT fk_22_fct_signals_org          FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_22_fct_signals_org
    ON "15_sandbox"."22_fct_signals" (org_id, signal_status_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_22_fct_signals_workspace
    ON "15_sandbox"."22_fct_signals" (workspace_id)
    WHERE is_deleted = FALSE AND workspace_id IS NOT NULL;

CREATE TRIGGER trg_22_fct_signals_updated_at
    BEFORE UPDATE ON "15_sandbox"."22_fct_signals"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 23_fct_threat_types — lean fact. Expression tree is structural (JSONB).
-- name, description, mitigation_guidance, compliance_references → EAV
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."23_fct_threat_types" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    workspace_id        UUID         NULL,
    threat_code         VARCHAR(100) NOT NULL,
    version_number      INTEGER      NOT NULL DEFAULT 1,
    severity_code       VARCHAR(30)  NOT NULL DEFAULT 'medium',
    expression_tree     JSONB        NOT NULL DEFAULT '{}',
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    deleted_at          TIMESTAMPTZ  NULL,
    deleted_by          UUID         NULL,

    CONSTRAINT pk_23_fct_threat_types           PRIMARY KEY (id),
    CONSTRAINT uq_23_fct_threat_types_version   UNIQUE (org_id, threat_code, version_number),
    CONSTRAINT ck_23_fct_threat_types_deleted    CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
        OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    ),
    CONSTRAINT fk_23_fct_threat_types_severity  FOREIGN KEY (severity_code)
        REFERENCES "15_sandbox"."08_dim_threat_severities" (code),
    CONSTRAINT fk_23_fct_threat_types_org       FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_23_fct_threat_types_org
    ON "15_sandbox"."23_fct_threat_types" (org_id)
    WHERE is_deleted = FALSE;

CREATE TRIGGER trg_23_fct_threat_types_updated_at
    BEFORE UPDATE ON "15_sandbox"."23_fct_threat_types"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 24_fct_policies — lean fact. Actions config is structural (JSONB).
-- name, description, owner, escalation_path → EAV
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."24_fct_policies" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    workspace_id        UUID         NULL,
    policy_code         VARCHAR(100) NOT NULL,
    version_number      INTEGER      NOT NULL DEFAULT 1,
    threat_type_id      UUID         NOT NULL,
    actions             JSONB        NOT NULL DEFAULT '[]',
    is_enabled          BOOLEAN      NOT NULL DEFAULT TRUE,
    cooldown_minutes    INTEGER      NOT NULL DEFAULT 0,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    deleted_at          TIMESTAMPTZ  NULL,
    deleted_by          UUID         NULL,

    CONSTRAINT pk_24_fct_policies              PRIMARY KEY (id),
    CONSTRAINT uq_24_fct_policies_version      UNIQUE (org_id, policy_code, version_number),
    CONSTRAINT ck_24_fct_policies_deleted       CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
        OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    ),
    CONSTRAINT fk_24_fct_policies_threat       FOREIGN KEY (threat_type_id)
        REFERENCES "15_sandbox"."23_fct_threat_types" (id),
    CONSTRAINT fk_24_fct_policies_org          FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_24_fct_policies_org
    ON "15_sandbox"."24_fct_policies" (org_id)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_24_fct_policies_threat
    ON "15_sandbox"."24_fct_policies" (threat_type_id)
    WHERE is_deleted = FALSE;

CREATE TRIGGER trg_24_fct_policies_updated_at
    BEFORE UPDATE ON "15_sandbox"."24_fct_policies"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 25_trx_sandbox_runs — immutable signal execution records (FAIL/WARNING only in PG)
-- Pass results go to ClickHouse.  Immutable — no UPDATE trigger.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."25_trx_sandbox_runs" (
    id                       UUID         NOT NULL,
    tenant_key               VARCHAR(100) NOT NULL,
    org_id                   UUID         NOT NULL,
    workspace_id             UUID         NULL,
    signal_id                UUID         NOT NULL,
    dataset_id               UUID         NULL,
    live_session_id          UUID         NULL,
    execution_status_code    VARCHAR(50)  NOT NULL,
    result_code              VARCHAR(30)  NULL,
    result_summary           TEXT         NULL,
    result_details           JSONB        NULL,
    execution_time_ms        INTEGER      NULL,
    error_message            TEXT         NULL,
    stdout_capture           TEXT         NULL,
    python_source_snapshot   TEXT         NOT NULL,
    dataset_snapshot_hash    VARCHAR(64)  NULL,
    started_at               TIMESTAMPTZ  NULL,
    completed_at             TIMESTAMPTZ  NULL,
    created_at               TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by               UUID         NULL,

    CONSTRAINT pk_25_trx_sandbox_runs             PRIMARY KEY (id),
    CONSTRAINT ck_25_trx_sandbox_runs_result      CHECK (result_code IS NULL OR result_code IN ('fail','warning','error')),
    CONSTRAINT fk_25_trx_sandbox_runs_status      FOREIGN KEY (execution_status_code)
        REFERENCES "15_sandbox"."06_dim_execution_statuses" (code),
    CONSTRAINT fk_25_trx_sandbox_runs_signal      FOREIGN KEY (signal_id)
        REFERENCES "15_sandbox"."22_fct_signals" (id),
    CONSTRAINT fk_25_trx_sandbox_runs_dataset     FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."21_fct_datasets" (id)
    -- FK to 28_fct_live_sessions added via ALTER TABLE after that table is created below
);

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_signal
    ON "15_sandbox"."25_trx_sandbox_runs" (signal_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_org
    ON "15_sandbox"."25_trx_sandbox_runs" (org_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_session
    ON "15_sandbox"."25_trx_sandbox_runs" (live_session_id, created_at DESC)
    WHERE live_session_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_created_brin
    ON "15_sandbox"."25_trx_sandbox_runs" USING BRIN (created_at);


-- ---------------------------------------------------------------------------
-- 26_trx_threat_evaluations — immutable threat evaluation records (TRIGGERED only in PG)
-- No UPDATE trigger — append-only.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."26_trx_threat_evaluations" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    threat_type_id      UUID         NOT NULL,
    is_triggered        BOOLEAN      NOT NULL,
    signal_results      JSONB        NOT NULL DEFAULT '{}',
    expression_snapshot JSONB        NOT NULL DEFAULT '{}',
    live_session_id     UUID         NULL,
    evaluated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,

    CONSTRAINT pk_26_trx_threat_evaluations         PRIMARY KEY (id),
    CONSTRAINT fk_26_trx_threat_evaluations_threat  FOREIGN KEY (threat_type_id)
        REFERENCES "15_sandbox"."23_fct_threat_types" (id)
);

CREATE INDEX IF NOT EXISTS idx_26_trx_threat_evaluations_threat
    ON "15_sandbox"."26_trx_threat_evaluations" (threat_type_id, evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_26_trx_threat_evaluations_org
    ON "15_sandbox"."26_trx_threat_evaluations" (org_id, evaluated_at DESC);

CREATE INDEX IF NOT EXISTS idx_26_trx_threat_evaluations_brin
    ON "15_sandbox"."26_trx_threat_evaluations" USING BRIN (evaluated_at);


-- ---------------------------------------------------------------------------
-- 27_trx_policy_executions — immutable audit trail of policy actions triggered
-- No UPDATE trigger — append-only.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."27_trx_policy_executions" (
    id                      UUID         NOT NULL,
    tenant_key              VARCHAR(100) NOT NULL,
    org_id                  UUID         NOT NULL,
    policy_id               UUID         NOT NULL,
    threat_evaluation_id    UUID         NOT NULL,
    actions_executed        JSONB        NOT NULL DEFAULT '[]',
    actions_failed          JSONB        NULL,
    executed_at             TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID         NULL,

    CONSTRAINT pk_27_trx_policy_executions           PRIMARY KEY (id),
    CONSTRAINT fk_27_trx_policy_executions_policy    FOREIGN KEY (policy_id)
        REFERENCES "15_sandbox"."24_fct_policies" (id),
    CONSTRAINT fk_27_trx_policy_executions_eval      FOREIGN KEY (threat_evaluation_id)
        REFERENCES "15_sandbox"."26_trx_threat_evaluations" (id)
);

CREATE INDEX IF NOT EXISTS idx_27_trx_policy_executions_policy
    ON "15_sandbox"."27_trx_policy_executions" (policy_id, executed_at DESC);

CREATE INDEX IF NOT EXISTS idx_27_trx_policy_executions_brin
    ON "15_sandbox"."27_trx_policy_executions" USING BRIN (executed_at);


-- ---------------------------------------------------------------------------
-- 28_fct_live_sessions — temporary live mode sessions (30 min default)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."28_fct_live_sessions" (
    id                      UUID         NOT NULL,
    tenant_key              VARCHAR(100) NOT NULL,
    org_id                  UUID         NOT NULL,
    workspace_id            UUID         NOT NULL,
    connector_instance_id   UUID         NOT NULL,
    session_status          VARCHAR(30)  NOT NULL DEFAULT 'starting',
    duration_minutes        INTEGER      NOT NULL DEFAULT 30,
    started_at              TIMESTAMPTZ  NULL,
    expires_at              TIMESTAMPTZ  NULL,
    paused_at               TIMESTAMPTZ  NULL,
    completed_at            TIMESTAMPTZ  NULL,
    data_points_received    INTEGER      NOT NULL DEFAULT 0,
    bytes_received          BIGINT       NOT NULL DEFAULT 0,
    signals_executed        INTEGER      NOT NULL DEFAULT 0,
    threats_evaluated       INTEGER      NOT NULL DEFAULT 0,
    is_deleted              BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID         NULL,

    CONSTRAINT pk_28_fct_live_sessions              PRIMARY KEY (id),
    CONSTRAINT ck_28_fct_live_sessions_status        CHECK (session_status IN ('starting','active','paused','completed','expired','error')),
    CONSTRAINT fk_28_fct_live_sessions_connector    FOREIGN KEY (connector_instance_id)
        REFERENCES "15_sandbox"."20_fct_connector_instances" (id),
    CONSTRAINT fk_28_fct_live_sessions_org          FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_28_fct_live_sessions_org
    ON "15_sandbox"."28_fct_live_sessions" (org_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_28_fct_live_sessions_workspace
    ON "15_sandbox"."28_fct_live_sessions" (workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_28_fct_live_sessions_status
    ON "15_sandbox"."28_fct_live_sessions" (session_status)
    WHERE session_status IN ('starting', 'active', 'paused');

-- Deferred FK: 25_trx_sandbox_runs.live_session_id → 28_fct_live_sessions
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    ADD CONSTRAINT fk_25_trx_sandbox_runs_session
    FOREIGN KEY (live_session_id) REFERENCES "15_sandbox"."28_fct_live_sessions" (id);


-- ═══════════════════════════════════════════════════════════════════════════════
-- TRANSACTION TABLES (31-32) — Immutable lifecycle events
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 31_trx_entity_lifecycle_events — immutable audit trail of status changes
-- Tracks: signal draft→testing→validated, threat type edits, policy enable/disable,
--         connector health changes, library publish, etc.
-- Same pattern as 33_trx_risk_review_events in risk_registry.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."31_trx_entity_lifecycle_events" (
    id              UUID         NOT NULL,
    tenant_key      VARCHAR(100) NOT NULL,
    org_id          UUID         NOT NULL,
    entity_type     VARCHAR(50)  NOT NULL,  -- connector, dataset, signal, threat_type, policy, library, live_session
    entity_id       UUID         NOT NULL,
    event_type      VARCHAR(50)  NOT NULL,  -- created, status_changed, updated, deleted, promoted, published, enabled, disabled, collected, validated, archived
    old_value       TEXT         NULL,       -- e.g., old status
    new_value       TEXT         NULL,       -- e.g., new status
    actor_id        UUID         NOT NULL,
    comment         TEXT         NULL,
    occurred_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_31_trx_lifecycle            PRIMARY KEY (id),
    CONSTRAINT ck_31_trx_lifecycle_entity     CHECK (entity_type IN ('connector','dataset','signal','threat_type','policy','library','live_session','promotion')),
    CONSTRAINT ck_31_trx_lifecycle_event      CHECK (event_type IN (
        'created','updated','deleted','status_changed',
        'promoted','published','unpublished',
        'enabled','disabled',
        'validated','archived',
        'collected','locked','cloned',
        'version_created','credential_updated','health_changed'
    ))
);

CREATE INDEX IF NOT EXISTS idx_31_trx_lifecycle_entity
    ON "15_sandbox"."31_trx_entity_lifecycle_events" (entity_type, entity_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_31_trx_lifecycle_org
    ON "15_sandbox"."31_trx_entity_lifecycle_events" (org_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_31_trx_lifecycle_actor
    ON "15_sandbox"."31_trx_entity_lifecycle_events" (actor_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_31_trx_lifecycle_brin
    ON "15_sandbox"."31_trx_entity_lifecycle_events" USING BRIN (occurred_at);


-- ---------------------------------------------------------------------------
-- 32_dtl_lifecycle_event_properties — EAV for lifecycle event metadata
-- e.g., "field_changed": "expression_tree", "old_hash": "abc", "new_hash": "def"
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."32_dtl_lifecycle_event_properties" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    event_id        UUID         NOT NULL,
    meta_key        VARCHAR(80)  NOT NULL,
    meta_value      TEXT         NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_32_dtl_lifecycle_props         PRIMARY KEY (id),
    CONSTRAINT fk_32_dtl_lifecycle_props_event   FOREIGN KEY (event_id)
        REFERENCES "15_sandbox"."31_trx_entity_lifecycle_events" (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_32_dtl_lifecycle_props_event
    ON "15_sandbox"."32_dtl_lifecycle_event_properties" (event_id);


-- ---------------------------------------------------------------------------
-- 29_fct_libraries — lean fact. Bundles policies into reusable collections.
-- name, description, target_asset_type, tags → 48_dtl_library_properties
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."29_fct_libraries" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    library_code        VARCHAR(100) NOT NULL,
    library_type_code   VARCHAR(50)  NOT NULL,
    version_number      INTEGER      NOT NULL DEFAULT 1,
    is_published        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    deleted_at          TIMESTAMPTZ  NULL,
    deleted_by          UUID         NULL,

    CONSTRAINT pk_29_fct_libraries              PRIMARY KEY (id),
    CONSTRAINT uq_29_fct_libraries_version      UNIQUE (org_id, library_code, version_number),
    CONSTRAINT ck_29_fct_libraries_deleted       CHECK (
        (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL)
        OR (is_deleted = TRUE AND deleted_at IS NOT NULL)
    ),
    CONSTRAINT fk_29_fct_libraries_type        FOREIGN KEY (library_type_code)
        REFERENCES "15_sandbox"."10_dim_library_types" (code),
    CONSTRAINT fk_29_fct_libraries_org         FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_29_fct_libraries_org
    ON "15_sandbox"."29_fct_libraries" (org_id)
    WHERE is_deleted = FALSE;

CREATE TRIGGER trg_29_fct_libraries_updated_at
    BEFORE UPDATE ON "15_sandbox"."29_fct_libraries"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- ---------------------------------------------------------------------------
-- 13_lnk_library_connector_types — maps libraries to connector types + versions
-- Used for auto-suggestion: configure K8s 1.31 → suggest "k8s_security_baseline" library
-- Placed here (after 29_fct_libraries) to satisfy FK dependency.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."13_lnk_library_connector_types" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    library_id          UUID         NOT NULL,
    connector_type_code VARCHAR(50)  NOT NULL,
    asset_version_id    UUID         NULL,     -- NULL = applies to all versions of this type
    is_recommended      BOOLEAN      NOT NULL DEFAULT TRUE,
    sort_order          INTEGER      NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_13_lnk_lib_ct              PRIMARY KEY (id),
    CONSTRAINT uq_13_lnk_lib_ct              UNIQUE (library_id, connector_type_code, asset_version_id),
    CONSTRAINT fk_13_lnk_lib_ct_lib          FOREIGN KEY (library_id)
        REFERENCES "15_sandbox"."29_fct_libraries" (id) ON DELETE CASCADE,
    CONSTRAINT fk_13_lnk_lib_ct_type         FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code),
    CONSTRAINT fk_13_lnk_lib_ct_ver          FOREIGN KEY (asset_version_id)
        REFERENCES "15_sandbox"."11_dim_asset_versions" (id)
);

CREATE INDEX IF NOT EXISTS idx_13_lnk_lib_ct_type
    ON "15_sandbox"."13_lnk_library_connector_types" (connector_type_code);


-- ---------------------------------------------------------------------------
-- 30_trx_promotions — immutable promotion records from sandbox → GRC library
-- No UPDATE trigger — append-only.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."30_trx_promotions" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    signal_id           UUID         NULL,
    policy_id           UUID         NULL,
    library_id          UUID         NULL,
    target_test_id      UUID         NULL,
    promotion_status    VARCHAR(30)  NOT NULL DEFAULT 'pending_review',
    promoted_at         TIMESTAMPTZ  NULL,
    promoted_by         UUID         NULL,
    review_notes        TEXT         NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,

    CONSTRAINT pk_30_trx_promotions              PRIMARY KEY (id),
    CONSTRAINT ck_30_trx_promotions_status       CHECK (promotion_status IN ('pending_review','approved','rejected','promoted')),
    CONSTRAINT ck_30_trx_promotions_has_source   CHECK (
        signal_id IS NOT NULL OR policy_id IS NOT NULL OR library_id IS NOT NULL
    )
);

CREATE INDEX IF NOT EXISTS idx_30_trx_promotions_signal
    ON "15_sandbox"."30_trx_promotions" (signal_id)
    WHERE signal_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_30_trx_promotions_policy
    ON "15_sandbox"."30_trx_promotions" (policy_id)
    WHERE policy_id IS NOT NULL;


-- ═══════════════════════════════════════════════════════════════════════════════
-- DETAIL / EAV TABLES (40-48)
-- ALL descriptive data lives here. Fact tables stay clean.
-- Standard pattern: (id, entity_id, property_key, property_value, timestamps)
-- ═══════════════════════════════════════════════════════════════════════════════

-- 40_dtl_connector_instance_properties
-- Keys: name, description, base_url, region, project_id, org_name, repo_list
CREATE TABLE IF NOT EXISTS "15_sandbox"."40_dtl_connector_instance_properties" (
    id                      UUID         NOT NULL,
    connector_instance_id   UUID         NOT NULL,
    property_key            VARCHAR(80)  NOT NULL,
    property_value          TEXT         NOT NULL,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID         NULL,
    updated_by              UUID         NULL,

    CONSTRAINT pk_40_dtl_ci_props          PRIMARY KEY (id),
    CONSTRAINT uq_40_dtl_ci_props_key      UNIQUE (connector_instance_id, property_key),
    CONSTRAINT fk_40_dtl_ci_props_ci       FOREIGN KEY (connector_instance_id)
        REFERENCES "15_sandbox"."20_fct_connector_instances" (id) ON DELETE CASCADE
);


-- 41_dtl_connector_credentials — encrypted credential storage (NOT standard EAV)
CREATE TABLE IF NOT EXISTS "15_sandbox"."41_dtl_connector_credentials" (
    id                      UUID         NOT NULL,
    connector_instance_id   UUID         NOT NULL,
    credential_key          VARCHAR(100) NOT NULL,
    encrypted_value         TEXT         NOT NULL,
    encryption_key_id       VARCHAR(50)  NOT NULL DEFAULT 'v1',
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by              UUID         NULL,
    updated_by              UUID         NULL,

    CONSTRAINT pk_41_dtl_creds             PRIMARY KEY (id),
    CONSTRAINT uq_41_dtl_creds_key         UNIQUE (connector_instance_id, credential_key),
    CONSTRAINT fk_41_dtl_creds_ci          FOREIGN KEY (connector_instance_id)
        REFERENCES "15_sandbox"."20_fct_connector_instances" (id) ON DELETE CASCADE
);


-- 42_dtl_dataset_properties
-- Keys: name, description, json_schema, source_endpoint, notes, tags
CREATE TABLE IF NOT EXISTS "15_sandbox"."42_dtl_dataset_properties" (
    id              UUID         NOT NULL,
    dataset_id      UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,
    updated_by      UUID         NULL,

    CONSTRAINT pk_42_dtl_ds_props          PRIMARY KEY (id),
    CONSTRAINT uq_42_dtl_ds_props_key      UNIQUE (dataset_id, property_key),
    CONSTRAINT fk_42_dtl_ds_props_ds       FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."21_fct_datasets" (id) ON DELETE CASCADE
);


-- 43_dtl_dataset_payloads — separated from fact table for query performance
CREATE TABLE IF NOT EXISTS "15_sandbox"."43_dtl_dataset_payloads" (
    id                  UUID         NOT NULL,
    dataset_id          UUID         NOT NULL,
    payload             JSONB        NOT NULL DEFAULT '{}',
    compressed_payload  BYTEA        NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_43_dtl_ds_payloads       PRIMARY KEY (id),
    CONSTRAINT uq_43_dtl_ds_payloads_ds    UNIQUE (dataset_id),
    CONSTRAINT fk_43_dtl_ds_payloads_ds    FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."21_fct_datasets" (id) ON DELETE CASCADE
);


-- 44_dtl_dataset_field_overrides — per-field provenance for composite datasets
CREATE TABLE IF NOT EXISTS "15_sandbox"."44_dtl_dataset_field_overrides" (
    id                  UUID         NOT NULL,
    dataset_id          UUID         NOT NULL,
    field_path          TEXT         NOT NULL,  -- JSONPath e.g. $.users[0].mfa_enabled
    override_source     VARCHAR(30)  NOT NULL,  -- manual, live, connector
    override_value      TEXT         NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,

    CONSTRAINT pk_44_dtl_ds_overrides       PRIMARY KEY (id),
    CONSTRAINT uq_44_dtl_ds_overrides_path  UNIQUE (dataset_id, field_path),
    CONSTRAINT fk_44_dtl_ds_overrides_ds    FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."21_fct_datasets" (id) ON DELETE CASCADE
);


-- 45_dtl_signal_properties
-- Keys: name, description, python_source, source_prompt, tags, usage_notes,
--        parameter_schema, caep_event_type, risc_event_type, compatible_connector_types
CREATE TABLE IF NOT EXISTS "15_sandbox"."45_dtl_signal_properties" (
    id              UUID         NOT NULL,
    signal_id       UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,
    updated_by      UUID         NULL,

    CONSTRAINT pk_45_dtl_sig_props         PRIMARY KEY (id),
    CONSTRAINT uq_45_dtl_sig_props_key     UNIQUE (signal_id, property_key),
    CONSTRAINT fk_45_dtl_sig_props_sig     FOREIGN KEY (signal_id)
        REFERENCES "15_sandbox"."22_fct_signals" (id) ON DELETE CASCADE
);


-- 46_dtl_threat_type_properties
-- Keys: name, description, mitigation_guidance, compliance_references, tags,
--        caep_event_type, risc_event_type
CREATE TABLE IF NOT EXISTS "15_sandbox"."46_dtl_threat_type_properties" (
    id              UUID         NOT NULL,
    threat_type_id  UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,
    updated_by      UUID         NULL,

    CONSTRAINT pk_46_dtl_tt_props          PRIMARY KEY (id),
    CONSTRAINT uq_46_dtl_tt_props_key      UNIQUE (threat_type_id, property_key),
    CONSTRAINT fk_46_dtl_tt_props_tt       FOREIGN KEY (threat_type_id)
        REFERENCES "15_sandbox"."23_fct_threat_types" (id) ON DELETE CASCADE
);


-- 47_dtl_policy_properties
-- Keys: name, description, owner, escalation_path, sla_notes, tags
CREATE TABLE IF NOT EXISTS "15_sandbox"."47_dtl_policy_properties" (
    id              UUID         NOT NULL,
    policy_id       UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,
    updated_by      UUID         NULL,

    CONSTRAINT pk_47_dtl_pol_props         PRIMARY KEY (id),
    CONSTRAINT uq_47_dtl_pol_props_key     UNIQUE (policy_id, property_key),
    CONSTRAINT fk_47_dtl_pol_props_pol     FOREIGN KEY (policy_id)
        REFERENCES "15_sandbox"."24_fct_policies" (id) ON DELETE CASCADE
);


-- 48_dtl_library_properties
-- Keys: name, description, target_asset_type, compliance_frameworks, tags, owner, release_notes
CREATE TABLE IF NOT EXISTS "15_sandbox"."48_dtl_library_properties" (
    id              UUID         NOT NULL,
    library_id      UUID         NOT NULL,
    property_key    VARCHAR(80)  NOT NULL,
    property_value  TEXT         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,
    updated_by      UUID         NULL,

    CONSTRAINT pk_48_dtl_lib_props         PRIMARY KEY (id),
    CONSTRAINT uq_48_dtl_lib_props_key     UNIQUE (library_id, property_key),
    CONSTRAINT fk_48_dtl_lib_props_lib     FOREIGN KEY (library_id)
        REFERENCES "15_sandbox"."29_fct_libraries" (id) ON DELETE CASCADE
);


-- 49_dtl_signal_test_expectations — golden tests for signal validation
CREATE TABLE IF NOT EXISTS "15_sandbox"."49_dtl_signal_test_expectations" (
    id                          UUID         NOT NULL,
    signal_id                   UUID         NOT NULL,
    dataset_id                  UUID         NOT NULL,
    expected_result_code        VARCHAR(30)  NOT NULL,
    expected_summary_pattern    TEXT         NULL,  -- regex to match against result_summary
    created_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by                  UUID         NULL,

    CONSTRAINT pk_49_dtl_expectations       PRIMARY KEY (id),
    CONSTRAINT ck_49_dtl_expectations_code  CHECK (expected_result_code IN ('pass','fail','warning')),
    CONSTRAINT fk_49_dtl_expectations_sig   FOREIGN KEY (signal_id)
        REFERENCES "15_sandbox"."22_fct_signals" (id) ON DELETE CASCADE,
    CONSTRAINT fk_49_dtl_expectations_ds    FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."21_fct_datasets" (id)
);


-- ═══════════════════════════════════════════════════════════════════════════════
-- LINK TABLES (50-53)
-- ═══════════════════════════════════════════════════════════════════════════════

-- 50_lnk_signal_connector_types — which connector types a signal evaluates
CREATE TABLE IF NOT EXISTS "15_sandbox"."50_lnk_signal_connector_types" (
    id                  UUID         NOT NULL DEFAULT gen_random_uuid(),
    signal_id           UUID         NOT NULL,
    connector_type_code VARCHAR(50)  NOT NULL,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,

    CONSTRAINT pk_50_lnk_sig_ct            PRIMARY KEY (id),
    CONSTRAINT uq_50_lnk_sig_ct            UNIQUE (signal_id, connector_type_code),
    CONSTRAINT fk_50_lnk_sig_ct_sig        FOREIGN KEY (signal_id)
        REFERENCES "15_sandbox"."22_fct_signals" (id) ON DELETE CASCADE,
    CONSTRAINT fk_50_lnk_sig_ct_type       FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);


-- 51_lnk_library_policies — which policies belong to a library
CREATE TABLE IF NOT EXISTS "15_sandbox"."51_lnk_library_policies" (
    id          UUID         NOT NULL DEFAULT gen_random_uuid(),
    library_id  UUID         NOT NULL,
    policy_id   UUID         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by  UUID         NULL,

    CONSTRAINT pk_51_lnk_lib_pol           PRIMARY KEY (id),
    CONSTRAINT uq_51_lnk_lib_pol           UNIQUE (library_id, policy_id),
    CONSTRAINT fk_51_lnk_lib_pol_lib       FOREIGN KEY (library_id)
        REFERENCES "15_sandbox"."29_fct_libraries" (id) ON DELETE CASCADE,
    CONSTRAINT fk_51_lnk_lib_pol_pol       FOREIGN KEY (policy_id)
        REFERENCES "15_sandbox"."24_fct_policies" (id)
);


-- 52_lnk_live_session_signals — which signals auto-execute during a live session
CREATE TABLE IF NOT EXISTS "15_sandbox"."52_lnk_live_session_signals" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    live_session_id UUID         NOT NULL,
    signal_id       UUID         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,

    CONSTRAINT pk_52_lnk_ls_sig            PRIMARY KEY (id),
    CONSTRAINT uq_52_lnk_ls_sig            UNIQUE (live_session_id, signal_id),
    CONSTRAINT fk_52_lnk_ls_sig_ls         FOREIGN KEY (live_session_id)
        REFERENCES "15_sandbox"."28_fct_live_sessions" (id) ON DELETE CASCADE,
    CONSTRAINT fk_52_lnk_ls_sig_sig        FOREIGN KEY (signal_id)
        REFERENCES "15_sandbox"."22_fct_signals" (id)
);


-- 53_lnk_live_session_threat_types — which threats to evaluate during live session
CREATE TABLE IF NOT EXISTS "15_sandbox"."53_lnk_live_session_threat_types" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    live_session_id UUID         NOT NULL,
    threat_type_id  UUID         NOT NULL,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,

    CONSTRAINT pk_53_lnk_ls_tt             PRIMARY KEY (id),
    CONSTRAINT uq_53_lnk_ls_tt             UNIQUE (live_session_id, threat_type_id),
    CONSTRAINT fk_53_lnk_ls_tt_ls          FOREIGN KEY (live_session_id)
        REFERENCES "15_sandbox"."28_fct_live_sessions" (id) ON DELETE CASCADE,
    CONSTRAINT fk_53_lnk_ls_tt_tt          FOREIGN KEY (threat_type_id)
        REFERENCES "15_sandbox"."23_fct_threat_types" (id)
);


-- ═══════════════════════════════════════════════════════════════════════════════
-- SSF TRANSMITTER TABLES (70-73)
-- Shared Signals Framework infrastructure for SET delivery
-- ═══════════════════════════════════════════════════════════════════════════════

-- 70_fct_ssf_streams — event streams for SSF receivers
CREATE TABLE IF NOT EXISTS "15_sandbox"."70_fct_ssf_streams" (
    id                  UUID         NOT NULL,
    tenant_key          VARCHAR(100) NOT NULL,
    org_id              UUID         NOT NULL,
    stream_description  TEXT         NULL,
    receiver_url        TEXT         NULL,        -- for push delivery
    delivery_method     VARCHAR(30)  NOT NULL DEFAULT 'push',
    events_requested    TEXT[]       NOT NULL DEFAULT '{}',
    events_delivered    TEXT[]       NOT NULL DEFAULT '{}',
    stream_status       VARCHAR(30)  NOT NULL DEFAULT 'enabled',
    authorization_header TEXT        NULL,        -- for push endpoint auth (encrypted at app layer via crypto.py, same as connector credentials)
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by          UUID         NULL,

    CONSTRAINT pk_70_fct_ssf_streams         PRIMARY KEY (id),
    CONSTRAINT ck_70_fct_ssf_streams_method  CHECK (delivery_method IN ('push','poll')),
    CONSTRAINT ck_70_fct_ssf_streams_status  CHECK (stream_status IN ('enabled','paused','disabled')),
    CONSTRAINT fk_70_fct_ssf_streams_org     FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id)
);

CREATE INDEX IF NOT EXISTS idx_70_fct_ssf_streams_org
    ON "15_sandbox"."70_fct_ssf_streams" (org_id)
    WHERE is_active = TRUE;

CREATE TRIGGER trg_70_fct_ssf_streams_updated_at
    BEFORE UPDATE ON "15_sandbox"."70_fct_ssf_streams"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_update_timestamp();


-- 71_dtl_ssf_stream_subjects — subjects enrolled per stream
CREATE TABLE IF NOT EXISTS "15_sandbox"."71_dtl_ssf_stream_subjects" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    stream_id       UUID         NOT NULL,
    subject_type    VARCHAR(50)  NOT NULL,  -- user, device, session, application, tenant
    subject_format  VARCHAR(50)  NOT NULL,  -- email, opaque, iss_sub, complex
    subject_id_data JSONB        NOT NULL,  -- the Subject Identifier object
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by      UUID         NULL,

    CONSTRAINT pk_71_dtl_ssf_subjects        PRIMARY KEY (id),
    CONSTRAINT fk_71_dtl_ssf_subjects_stream FOREIGN KEY (stream_id)
        REFERENCES "15_sandbox"."70_fct_ssf_streams" (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_71_dtl_ssf_subjects_stream
    ON "15_sandbox"."71_dtl_ssf_stream_subjects" (stream_id);


-- 72_trx_ssf_outbox — outgoing SET queue for poll delivery
CREATE TABLE IF NOT EXISTS "15_sandbox"."72_trx_ssf_outbox" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    stream_id       UUID         NOT NULL,
    set_jwt         TEXT         NOT NULL,  -- the signed SET JWT
    jti             VARCHAR(100) NOT NULL,  -- unique token identifier
    acknowledged    BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    acknowledged_at TIMESTAMPTZ  NULL,

    CONSTRAINT pk_72_trx_ssf_outbox          PRIMARY KEY (id),
    CONSTRAINT uq_72_trx_ssf_outbox_jti      UNIQUE (stream_id, jti),
    CONSTRAINT fk_72_trx_ssf_outbox_stream   FOREIGN KEY (stream_id)
        REFERENCES "15_sandbox"."70_fct_ssf_streams" (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_72_trx_ssf_outbox_pending
    ON "15_sandbox"."72_trx_ssf_outbox" (stream_id, created_at)
    WHERE acknowledged = FALSE;


-- 73_trx_ssf_delivery_log — delivery receipts
CREATE TABLE IF NOT EXISTS "15_sandbox"."73_trx_ssf_delivery_log" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    stream_id       UUID         NOT NULL,
    jti             VARCHAR(100) NOT NULL,
    delivery_method VARCHAR(30)  NOT NULL,
    http_status     INTEGER      NULL,
    error_message   TEXT         NULL,
    delivered_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_73_trx_ssf_delivery        PRIMARY KEY (id),
    CONSTRAINT fk_73_trx_ssf_delivery_stream FOREIGN KEY (stream_id)
        REFERENCES "15_sandbox"."70_fct_ssf_streams" (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_73_trx_ssf_delivery_stream
    ON "15_sandbox"."73_trx_ssf_delivery_log" (stream_id, delivered_at DESC);

CREATE INDEX IF NOT EXISTS idx_73_trx_ssf_delivery_brin
    ON "15_sandbox"."73_trx_ssf_delivery_log" USING BRIN (delivered_at);


-- ═══════════════════════════════════════════════════════════════════════════════
-- VIEWS (60-65)
-- ═══════════════════════════════════════════════════════════════════════════════

-- 60_vw_connector_instance_detail
CREATE OR REPLACE VIEW "15_sandbox"."60_vw_connector_instance_detail" AS
SELECT
    ci.id,
    ci.tenant_key,
    ci.org_id,
    ci.instance_code,
    ci.connector_type_code,
    ct.name                 AS connector_type_name,
    ct.category_code        AS connector_category_code,
    cc.name                 AS connector_category_name,
    ci.asset_version_id,
    ci.collection_schedule,
    ci.last_collected_at,
    ci.health_status,
    ci.is_active,
    ci.created_at,
    ci.updated_at,
    (SELECT p.property_value FROM "15_sandbox"."40_dtl_connector_instance_properties" p
     WHERE p.connector_instance_id = ci.id AND p.property_key = 'name')        AS name,
    (SELECT p.property_value FROM "15_sandbox"."40_dtl_connector_instance_properties" p
     WHERE p.connector_instance_id = ci.id AND p.property_key = 'description') AS description
FROM "15_sandbox"."20_fct_connector_instances" ci
JOIN "15_sandbox"."03_dim_connector_types"     ct ON ct.code = ci.connector_type_code
JOIN "15_sandbox"."02_dim_connector_categories" cc ON cc.code = ct.category_code
WHERE ci.is_deleted = FALSE;


-- 61_vw_signal_detail
CREATE OR REPLACE VIEW "15_sandbox"."61_vw_signal_detail" AS
SELECT
    s.id,
    s.tenant_key,
    s.org_id,
    s.workspace_id,
    s.signal_code,
    s.version_number,
    s.signal_status_code,
    ss.name                 AS signal_status_name,
    s.python_hash,
    s.timeout_ms,
    s.max_memory_mb,
    s.is_active,
    s.created_at,
    s.updated_at,
    (SELECT p.property_value FROM "15_sandbox"."45_dtl_signal_properties" p
     WHERE p.signal_id = s.id AND p.property_key = 'name')          AS name,
    (SELECT p.property_value FROM "15_sandbox"."45_dtl_signal_properties" p
     WHERE p.signal_id = s.id AND p.property_key = 'description')   AS description,
    (SELECT p.property_value FROM "15_sandbox"."45_dtl_signal_properties" p
     WHERE p.signal_id = s.id AND p.property_key = 'caep_event_type') AS caep_event_type,
    (SELECT p.property_value FROM "15_sandbox"."45_dtl_signal_properties" p
     WHERE p.signal_id = s.id AND p.property_key = 'risc_event_type') AS risc_event_type
FROM "15_sandbox"."22_fct_signals" s
JOIN "15_sandbox"."04_dim_signal_statuses" ss ON ss.code = s.signal_status_code
WHERE s.is_deleted = FALSE;


-- 62_vw_threat_type_detail
CREATE OR REPLACE VIEW "15_sandbox"."62_vw_threat_type_detail" AS
SELECT
    t.id,
    t.tenant_key,
    t.org_id,
    t.workspace_id,
    t.threat_code,
    t.version_number,
    t.severity_code,
    ts.name                 AS severity_name,
    t.expression_tree,
    t.is_active,
    t.created_at,
    t.updated_at,
    (SELECT p.property_value FROM "15_sandbox"."46_dtl_threat_type_properties" p
     WHERE p.threat_type_id = t.id AND p.property_key = 'name')        AS name,
    (SELECT p.property_value FROM "15_sandbox"."46_dtl_threat_type_properties" p
     WHERE p.threat_type_id = t.id AND p.property_key = 'description') AS description
FROM "15_sandbox"."23_fct_threat_types" t
JOIN "15_sandbox"."08_dim_threat_severities" ts ON ts.code = t.severity_code
WHERE t.is_deleted = FALSE;


-- 63_vw_policy_detail
CREATE OR REPLACE VIEW "15_sandbox"."63_vw_policy_detail" AS
SELECT
    pol.id,
    pol.tenant_key,
    pol.org_id,
    pol.workspace_id,
    pol.policy_code,
    pol.version_number,
    pol.threat_type_id,
    tt.threat_code,
    pol.actions,
    pol.is_enabled,
    pol.cooldown_minutes,
    pol.is_active,
    pol.created_at,
    pol.updated_at,
    (SELECT p.property_value FROM "15_sandbox"."47_dtl_policy_properties" p
     WHERE p.policy_id = pol.id AND p.property_key = 'name')        AS name,
    (SELECT p.property_value FROM "15_sandbox"."47_dtl_policy_properties" p
     WHERE p.policy_id = pol.id AND p.property_key = 'description') AS description
FROM "15_sandbox"."24_fct_policies" pol
JOIN "15_sandbox"."23_fct_threat_types" tt ON tt.id = pol.threat_type_id
WHERE pol.is_deleted = FALSE;


-- 64_vw_library_detail
CREATE OR REPLACE VIEW "15_sandbox"."64_vw_library_detail" AS
SELECT
    lib.id,
    lib.tenant_key,
    lib.org_id,
    lib.library_code,
    lib.library_type_code,
    lt.name                 AS library_type_name,
    lib.version_number,
    lib.is_published,
    lib.is_active,
    lib.created_at,
    lib.updated_at,
    (SELECT p.property_value FROM "15_sandbox"."48_dtl_library_properties" p
     WHERE p.library_id = lib.id AND p.property_key = 'name')        AS name,
    (SELECT p.property_value FROM "15_sandbox"."48_dtl_library_properties" p
     WHERE p.library_id = lib.id AND p.property_key = 'description') AS description,
    (SELECT count(*) FROM "15_sandbox"."51_lnk_library_policies" lp
     WHERE lp.library_id = lib.id)                                    AS policy_count
FROM "15_sandbox"."29_fct_libraries" lib
JOIN "15_sandbox"."10_dim_library_types" lt ON lt.code = lib.library_type_code
WHERE lib.is_deleted = FALSE;


-- 65_vw_run_detail
CREATE OR REPLACE VIEW "15_sandbox"."65_vw_run_detail" AS
SELECT
    r.id,
    r.tenant_key,
    r.org_id,
    r.signal_id,
    s.signal_code,
    r.dataset_id,
    r.live_session_id,
    r.execution_status_code,
    es.name                 AS execution_status_name,
    r.result_code,
    r.result_summary,
    r.execution_time_ms,
    r.started_at,
    r.completed_at,
    r.created_at,
    (SELECT p.property_value FROM "15_sandbox"."45_dtl_signal_properties" p
     WHERE p.signal_id = s.id AND p.property_key = 'name')           AS signal_name
FROM "15_sandbox"."25_trx_sandbox_runs" r
JOIN "15_sandbox"."22_fct_signals"          s  ON s.id  = r.signal_id
JOIN "15_sandbox"."06_dim_execution_statuses" es ON es.code = r.execution_status_code;
