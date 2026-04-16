-- =============================================================================
-- Migration: 20260316_create-asset-inventory.sql
-- Description: Asset inventory tables for 15_sandbox schema + new 17_steampipe schema
-- Date: 2026-03-16
-- =============================================================================


-- =============================================================================
-- SECTION 1: Extend 20_fct_connector_instances
-- =============================================================================

ALTER TABLE "15_sandbox"."20_fct_connector_instances"
    ADD COLUMN IF NOT EXISTS provider_definition_code VARCHAR(100) NULL,
    ADD COLUMN IF NOT EXISTS provider_version_code VARCHAR(50) NULL,
    ADD COLUMN IF NOT EXISTS connection_config JSONB NULL;


-- =============================================================================
-- SECTION 2: 15_sandbox — Dimension Tables
-- =============================================================================

-- 14_dim_asset_types
CREATE TABLE IF NOT EXISTS "15_sandbox"."14_dim_asset_types" (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    code             VARCHAR(100) NOT NULL UNIQUE,
    provider_code    VARCHAR(100) NOT NULL,  -- references 16_dim_provider_definitions.code
    name             VARCHAR(200) NOT NULL,
    description      TEXT,
    is_active        BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 15_dim_asset_statuses
CREATE TABLE IF NOT EXISTS "15_sandbox"."15_dim_asset_statuses" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE
);

-- 16_dim_provider_definitions
CREATE TABLE IF NOT EXISTS "15_sandbox"."16_dim_provider_definitions" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    code                  VARCHAR(100) NOT NULL UNIQUE,
    name                  VARCHAR(200) NOT NULL,
    driver_module         VARCHAR(500) NOT NULL,
    default_auth_method   VARCHAR(100) NOT NULL DEFAULT 'api_key',
    supports_log_collection  BOOLEAN   NOT NULL DEFAULT FALSE,
    supports_steampipe    BOOLEAN      NOT NULL DEFAULT FALSE,
    supports_custom_driver BOOLEAN     NOT NULL DEFAULT TRUE,
    steampipe_plugin      VARCHAR(200) NULL,
    rate_limit_rpm        INT          NOT NULL DEFAULT 60,
    config_schema         JSONB        NOT NULL DEFAULT '{"fields": []}',
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    is_coming_soon        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 17_dim_provider_versions
CREATE TABLE IF NOT EXISTS "15_sandbox"."17_dim_provider_versions" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_code         VARCHAR(100) NOT NULL,
    version_code          VARCHAR(50)  NOT NULL,
    name                  VARCHAR(200) NOT NULL,
    config_schema_override JSONB       NULL,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    is_default            BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (provider_code, version_code)
);

-- 18_dim_asset_access_roles
CREATE TABLE IF NOT EXISTS "15_sandbox"."18_dim_asset_access_roles" (
    code        VARCHAR(50)  PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order  INT          NOT NULL DEFAULT 0
);


-- =============================================================================
-- SECTION 3: 15_sandbox — Fact Tables
-- =============================================================================

-- 33_fct_assets
CREATE TABLE IF NOT EXISTS "15_sandbox"."33_fct_assets" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key            VARCHAR(100) NOT NULL,
    org_id                UUID         NOT NULL,
    workspace_id          UUID         NULL,
    connector_instance_id UUID         NOT NULL,
    provider_code         VARCHAR(100) NOT NULL,
    asset_type_code       VARCHAR(100) NOT NULL,
    asset_external_id     VARCHAR(500) NOT NULL,
    parent_asset_id       UUID         NULL REFERENCES "15_sandbox"."33_fct_assets"(id),
    status_code           VARCHAR(50)  NOT NULL DEFAULT 'discovered',
    current_snapshot_id   UUID         NULL,
    last_collected_at     TIMESTAMPTZ  NULL,
    consecutive_misses    INT          NOT NULL DEFAULT 0,
    created_by            UUID         NOT NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    deleted_at            TIMESTAMPTZ  NULL,
    deleted_by            UUID         NULL,
    is_deleted            BOOLEAN      NOT NULL DEFAULT FALSE,
    UNIQUE (connector_instance_id, asset_type_code, asset_external_id)
);

-- 34_fct_asset_snapshots
CREATE TABLE IF NOT EXISTS "15_sandbox"."34_fct_asset_snapshots" (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id          UUID         NOT NULL REFERENCES "15_sandbox"."33_fct_assets"(id),
    collection_run_id UUID         NULL,
    snapshot_number   INT          NOT NULL,
    schema_fingerprint VARCHAR(64) NOT NULL,
    property_count    INT          NOT NULL DEFAULT 0,
    collected_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (asset_id, snapshot_number)
);

-- 35_fct_collection_runs
CREATE TABLE IF NOT EXISTS "15_sandbox"."35_fct_collection_runs" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key            VARCHAR(100) NOT NULL,
    org_id                UUID         NOT NULL,
    connector_instance_id UUID         NOT NULL,
    status                VARCHAR(50)  NOT NULL DEFAULT 'queued',
    trigger_type          VARCHAR(50)  NOT NULL DEFAULT 'manual',
    started_at            TIMESTAMPTZ  NULL,
    completed_at          TIMESTAMPTZ  NULL,
    assets_discovered     INT          NOT NULL DEFAULT 0,
    assets_updated        INT          NOT NULL DEFAULT 0,
    assets_deleted        INT          NOT NULL DEFAULT 0,
    logs_ingested         INT          NOT NULL DEFAULT 0,
    error_message         TEXT         NULL,
    triggered_by          UUID         NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 36_fct_log_sources
CREATE TABLE IF NOT EXISTS "15_sandbox"."36_fct_log_sources" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key            VARCHAR(100) NOT NULL,
    org_id                UUID         NOT NULL,
    connector_instance_id UUID         NOT NULL,
    log_type              VARCHAR(100) NOT NULL,
    poll_interval_seconds INT          NOT NULL DEFAULT 3600,
    last_polled_at        TIMESTAMPTZ  NULL,
    last_cursor           TEXT         NULL,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (connector_instance_id, log_type)
);


-- =============================================================================
-- SECTION 4: 15_sandbox — Detail / EAV Tables
-- =============================================================================

-- 54_dtl_asset_properties (current values, overwritten each run)
CREATE TABLE IF NOT EXISTS "15_sandbox"."54_dtl_asset_properties" (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id       UUID         NOT NULL REFERENCES "15_sandbox"."33_fct_assets"(id) ON DELETE CASCADE,
    property_key   VARCHAR(200) NOT NULL,
    property_value TEXT         NOT NULL,
    value_type     VARCHAR(50)  NOT NULL DEFAULT 'string',
    collected_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (asset_id, property_key)
);

-- 55_dtl_asset_snapshot_properties (immutable per snapshot)
CREATE TABLE IF NOT EXISTS "15_sandbox"."55_dtl_asset_snapshot_properties" (
    id             UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id    UUID         NOT NULL REFERENCES "15_sandbox"."34_fct_asset_snapshots"(id) ON DELETE CASCADE,
    property_key   VARCHAR(200) NOT NULL,
    property_value TEXT         NOT NULL,
    value_type     VARCHAR(50)  NOT NULL DEFAULT 'string',
    UNIQUE (snapshot_id, property_key)
);

-- 56_dtl_provider_definition_properties (metadata)
CREATE TABLE IF NOT EXISTS "15_sandbox"."56_dtl_provider_definition_properties" (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_code VARCHAR(100) NOT NULL,
    meta_key      VARCHAR(200) NOT NULL,
    meta_value    TEXT         NOT NULL,
    UNIQUE (provider_code, meta_key)
);


-- =============================================================================
-- SECTION 5: 15_sandbox — Link Tables
-- =============================================================================

-- 57_lnk_asset_access_grants
CREATE TABLE IF NOT EXISTS "15_sandbox"."57_lnk_asset_access_grants" (
    id            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id      UUID         NOT NULL REFERENCES "15_sandbox"."33_fct_assets"(id) ON DELETE CASCADE,
    user_group_id UUID         NOT NULL,
    role_code     VARCHAR(50)  NOT NULL,
    granted_by    UUID         NOT NULL,
    granted_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (asset_id, user_group_id, role_code)
);

-- 58_lnk_asset_datasets
CREATE TABLE IF NOT EXISTS "15_sandbox"."58_lnk_asset_datasets" (
    id         UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id   UUID        NOT NULL REFERENCES "15_sandbox"."33_fct_assets"(id) ON DELETE CASCADE,
    dataset_id UUID        NOT NULL,
    linked_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    linked_by  UUID        NOT NULL,
    UNIQUE (asset_id, dataset_id)
);


-- =============================================================================
-- SECTION 6: 15_sandbox — Indexes
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_33_fct_assets_org
    ON "15_sandbox"."33_fct_assets"(org_id, is_deleted);

CREATE INDEX IF NOT EXISTS idx_33_fct_assets_connector
    ON "15_sandbox"."33_fct_assets"(connector_instance_id, is_deleted);

CREATE INDEX IF NOT EXISTS idx_33_fct_assets_type
    ON "15_sandbox"."33_fct_assets"(asset_type_code, status_code);

CREATE INDEX IF NOT EXISTS idx_33_fct_assets_last_collected
    ON "15_sandbox"."33_fct_assets"(last_collected_at);

CREATE INDEX IF NOT EXISTS idx_34_fct_asset_snapshots_asset
    ON "15_sandbox"."34_fct_asset_snapshots"(asset_id, snapshot_number DESC);

CREATE INDEX IF NOT EXISTS idx_35_fct_collection_runs_org
    ON "15_sandbox"."35_fct_collection_runs"(org_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_35_fct_collection_runs_connector
    ON "15_sandbox"."35_fct_collection_runs"(connector_instance_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_35_fct_collection_runs_status
    ON "15_sandbox"."35_fct_collection_runs"(status);

CREATE INDEX IF NOT EXISTS idx_54_dtl_asset_properties_asset
    ON "15_sandbox"."54_dtl_asset_properties"(asset_id);

CREATE INDEX IF NOT EXISTS idx_55_dtl_snapshot_props_snapshot
    ON "15_sandbox"."55_dtl_asset_snapshot_properties"(snapshot_id);

CREATE INDEX IF NOT EXISTS idx_57_lnk_asset_access_asset
    ON "15_sandbox"."57_lnk_asset_access_grants"(asset_id);

CREATE INDEX IF NOT EXISTS idx_57_lnk_asset_access_group
    ON "15_sandbox"."57_lnk_asset_access_grants"(user_group_id);


-- =============================================================================
-- SECTION 7: 15_sandbox — Views
-- =============================================================================

-- 66_vw_asset_detail
CREATE OR REPLACE VIEW "15_sandbox"."66_vw_asset_detail" AS
SELECT
    a.id,
    a.tenant_key,
    a.org_id,
    a.workspace_id,
    a.connector_instance_id,
    a.provider_code,
    a.asset_type_code,
    a.asset_external_id,
    a.parent_asset_id,
    a.status_code,
    a.current_snapshot_id,
    a.last_collected_at,
    a.consecutive_misses,
    a.created_by,
    a.created_at,
    a.updated_at,
    a.is_deleted,
    pd.name                  AS provider_name,
    pd.supports_steampipe,
    pd.supports_log_collection,
    at.name                  AS asset_type_name,
    s.name                   AS status_name
FROM "15_sandbox"."33_fct_assets" a
LEFT JOIN "15_sandbox"."16_dim_provider_definitions" pd ON pd.code = a.provider_code
LEFT JOIN "15_sandbox"."14_dim_asset_types"          at ON at.code = a.asset_type_code
LEFT JOIN "15_sandbox"."15_dim_asset_statuses"        s ON s.code  = a.status_code
WHERE a.is_deleted = FALSE;

-- 67_vw_collection_run_detail
CREATE OR REPLACE VIEW "15_sandbox"."67_vw_collection_run_detail" AS
SELECT
    cr.id,
    cr.tenant_key,
    cr.org_id,
    cr.connector_instance_id,
    cr.status,
    cr.trigger_type,
    cr.started_at,
    cr.completed_at,
    cr.assets_discovered,
    cr.assets_updated,
    cr.assets_deleted,
    cr.logs_ingested,
    cr.error_message,
    cr.triggered_by,
    cr.created_at,
    cr.updated_at,
    EXTRACT(EPOCH FROM (cr.completed_at - cr.started_at))::INT AS duration_seconds
FROM "15_sandbox"."35_fct_collection_runs" cr;


-- =============================================================================
-- SECTION 8: 17_steampipe — Schema, Tables, and Indexes
-- =============================================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- 02_dim_plugin_types
CREATE TABLE IF NOT EXISTS "17_steampipe"."02_dim_plugin_types" (
    code          VARCHAR(100) PRIMARY KEY,
    name          VARCHAR(200) NOT NULL,
    plugin_image  VARCHAR(300) NOT NULL,
    provider_code VARCHAR(100) NOT NULL,
    version       VARCHAR(50)  NOT NULL DEFAULT 'latest',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 10_fct_plugin_configs
CREATE TABLE IF NOT EXISTS "17_steampipe"."10_fct_plugin_configs" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_instance_id UUID         NOT NULL,
    plugin_type_code      VARCHAR(100) NOT NULL,
    config_hash           VARCHAR(64)  NOT NULL,
    is_valid              BOOLEAN      NOT NULL DEFAULT TRUE,
    last_validated_at     TIMESTAMPTZ  NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (connector_instance_id, plugin_type_code)
);

-- 11_fct_query_results
CREATE TABLE IF NOT EXISTS "17_steampipe"."11_fct_query_results" (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_instance_id UUID        NOT NULL,
    query_hash            VARCHAR(64) NOT NULL,
    result_json           JSONB       NOT NULL,
    row_count             INT         NOT NULL DEFAULT 0,
    executed_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at            TIMESTAMPTZ NOT NULL,
    steampipe_run_id      UUID        NULL
);

-- 12_fct_steampipe_runs
CREATE TABLE IF NOT EXISTS "17_steampipe"."12_fct_steampipe_runs" (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    connector_instance_id UUID         NOT NULL,
    query_hash            VARCHAR(64)  NOT NULL,
    query_sql             TEXT         NOT NULL,
    status                VARCHAR(50)  NOT NULL DEFAULT 'running',
    row_count             INT          NULL,
    duration_ms           INT          NULL,
    error_message         TEXT         NULL,
    started_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at          TIMESTAMPTZ  NULL
);

CREATE INDEX IF NOT EXISTS idx_10_plugin_configs_connector
    ON "17_steampipe"."10_fct_plugin_configs"(connector_instance_id);

CREATE INDEX IF NOT EXISTS idx_11_query_results_connector
    ON "17_steampipe"."11_fct_query_results"(connector_instance_id, query_hash, expires_at);

CREATE INDEX IF NOT EXISTS idx_12_steampipe_runs_connector
    ON "17_steampipe"."12_fct_steampipe_runs"(connector_instance_id, started_at DESC);


-- =============================================================================
-- SECTION 9: Seed Data
-- =============================================================================

-- Asset statuses
INSERT INTO "15_sandbox"."15_dim_asset_statuses" (code, name, description, is_terminal)
VALUES
    ('discovered', 'Discovered', 'Asset first found by collector',                        FALSE),
    ('active',     'Active',     'Asset verified present in last collection',              FALSE),
    ('modified',   'Modified',   'Asset properties changed since last snapshot',           FALSE),
    ('stale',      'Stale',      'Asset not found in last collection run',                 FALSE),
    ('deleted',    'Deleted',    'Asset confirmed absent at provider',                     TRUE),
    ('error',      'Error',      'Asset collection encountered an error',                  FALSE)
ON CONFLICT (code) DO NOTHING;

-- Asset access roles
INSERT INTO "15_sandbox"."18_dim_asset_access_roles" (code, name, description, sort_order)
VALUES
    ('view', 'View', 'Can view asset properties and snapshots',                        1),
    ('use',  'Use',  'Can reference asset data in signals and policies',               2),
    ('edit', 'Edit', 'Can modify asset configuration and trigger collection',          3)
ON CONFLICT (code) DO NOTHING;

-- Provider definitions
INSERT INTO "15_sandbox"."16_dim_provider_definitions"
    (code, name, driver_module, default_auth_method, supports_log_collection, supports_steampipe,
     steampipe_plugin, rate_limit_rpm, config_schema, is_active, is_coming_soon)
VALUES
(
    'github',
    'GitHub',
    'backend.10_sandbox.18_drivers.github.GitHubDriver',
    'personal_access_token',
    TRUE,
    TRUE,
    'turbot/github',
    5000,
    '{"fields": [
        {"key": "org_name",              "label": "Organization Name",        "type": "text",     "required": true,  "credential": false, "placeholder": "my-github-org",                         "validation": "^[a-zA-Z0-9._-]+$", "hint": "The GitHub organization slug (from the URL)",                     "order": 1},
        {"key": "personal_access_token", "label": "Personal Access Token",   "type": "password", "required": true,  "credential": true,                                                                                             "hint": "Requires: read:org, repo, admin:org",                             "order": 2},
        {"key": "base_url",              "label": "GitHub Enterprise URL",    "type": "text",     "required": false, "credential": false, "placeholder": "https://github.example.com",                                             "hint": "Only for GitHub Enterprise Server installations",                 "order": 3}
    ]}',
    TRUE,
    FALSE
),
(
    'azure_storage',
    'Azure Storage',
    'backend.10_sandbox.18_drivers.azure_storage.AzureStorageDriver',
    'service_principal',
    TRUE,
    TRUE,
    'turbot/azure',
    1200,
    '{"fields": [
        {"key": "subscription_id", "label": "Subscription ID",             "type": "text",     "required": true,  "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "validation": "^[0-9a-f-]{36}$", "order": 1},
        {"key": "tenant_id",       "label": "Tenant ID",                   "type": "text",     "required": true,  "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "validation": "^[0-9a-f-]{36}$", "order": 2},
        {"key": "client_id",       "label": "Client ID",                   "type": "text",     "required": true,  "credential": false, "placeholder": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", "validation": "^[0-9a-f-]{36}$", "order": 3},
        {"key": "client_secret",   "label": "Client Secret",               "type": "password", "required": true,  "credential": true,                                                                                              "order": 4},
        {"key": "resource_group",  "label": "Resource Group (optional)",   "type": "text",     "required": false, "credential": false,                                                                                              "hint": "Leave empty to collect all storage accounts in the subscription", "order": 5}
    ]}',
    TRUE,
    FALSE
)
ON CONFLICT (code) DO NOTHING;

-- Asset types
INSERT INTO "15_sandbox"."14_dim_asset_types" (code, provider_code, name, description)
VALUES
    ('github_org',                  'github',        'GitHub Organization',       'A GitHub organization'),
    ('github_repo',                 'github',        'GitHub Repository',         'A repository within a GitHub org'),
    ('github_branch_protection',    'github',        'Branch Protection Rule',    'Branch protection rules for a GitHub repository'),
    ('github_team',                 'github',        'GitHub Team',               'A team within a GitHub organization'),
    ('github_org_member',           'github',        'Organization Member',       'A member of the GitHub organization'),
    ('azure_storage_account',       'azure_storage', 'Azure Storage Account',     'An Azure Storage Account'),
    ('azure_blob_container',        'azure_storage', 'Azure Blob Container',      'A Blob container within a Storage Account'),
    ('azure_storage_network_rule',  'azure_storage', 'Azure Storage Network Rule','Network rules for an Azure Storage Account')
ON CONFLICT (code) DO NOTHING;

-- Steampipe plugin types
INSERT INTO "17_steampipe"."02_dim_plugin_types" (code, name, plugin_image, provider_code, version)
VALUES
    ('turbot/github', 'Steampipe GitHub Plugin', 'ghcr.io/turbot/steampipe-plugin-github', 'github',        'latest'),
    ('turbot/azure',  'Steampipe Azure Plugin',  'ghcr.io/turbot/steampipe-plugin-azure',  'azure_storage', 'latest')
ON CONFLICT (code) DO NOTHING;
