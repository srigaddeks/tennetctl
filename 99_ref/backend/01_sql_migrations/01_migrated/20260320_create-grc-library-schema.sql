-- ─────────────────────────────────────────────────────────────────────────────
-- 05_GRC_LIBRARY SCHEMA
-- Framework Registry, Controls, Tests, Requirements, Versions, Evidence Templates
--
-- Scoping: Platform-level library (tenant_key + optional scope_org_id)
--   - Official frameworks: tenant_key = '__platform__'
--   - Org-specific frameworks: scope_org_id set
--   - Operational usage (deployments, risks, tasks) happens in workspaces
--
-- Pattern: lean fact + EAV (no property_keys dimension — unconstrained keys)
--   - 02-08 dim_* tables: dimension/lookup (types, categories, criticalities)
--   - 10-15 fct_* tables: ONLY structural columns (UUID, code, FKs, flags)
--   - 20-26 dtl_* tables: ALL descriptive data (name, description, notes, URLs)
--   - 27    trx_* tables: immutable transaction data (version changelogs)
--   - 30-32 lnk_* tables: many-to-many relationships
--   - 40-42 vw_*  views:  reassemble fact + EAV for API consumption
--
-- Audit: ALL lifecycle events go to 03_auth_manage.40_aud_events (no local audit)
-- Domain trx tables: version changelog items (structured, immutable)
-- ─────────────────────────────────────────────────────────────────────────────

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES (02-08)
-- ─────────────────────────────────────────────────────────────────────────────

-- Framework types: structural classification that determines behaviour
-- (versioning rules, marketplace eligibility, publisher attribution)
-- Different from categories which are for filtering/grouping in the UI
CREATE TABLE IF NOT EXISTS "05_grc_library"."02_dim_framework_types" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_02_dim_framework_types      PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_framework_types_code UNIQUE (code)
);

-- Framework categories: filtering/grouping in the UI
CREATE TABLE IF NOT EXISTS "05_grc_library"."03_dim_framework_categories" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_03_dim_framework_categories      PRIMARY KEY (id),
    CONSTRAINT uq_03_dim_framework_categories_code UNIQUE (code)
);

-- Control categories: domain grouping (access_control, change_management, etc.)
CREATE TABLE IF NOT EXISTS "05_grc_library"."04_dim_control_categories" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_04_dim_control_categories      PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_control_categories_code UNIQUE (code)
);

-- Control criticalities: severity levels
CREATE TABLE IF NOT EXISTS "05_grc_library"."05_dim_control_criticalities" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_05_dim_control_criticalities      PRIMARY KEY (id),
    CONSTRAINT uq_05_dim_control_criticalities_code UNIQUE (code)
);

-- Test types: automated, manual, semi-automated
CREATE TABLE IF NOT EXISTS "05_grc_library"."07_dim_test_types" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_07_dim_test_types      PRIMARY KEY (id),
    CONSTRAINT uq_07_dim_test_types_code UNIQUE (code)
);

-- Test result statuses: pass, fail, partial, unknown, error
CREATE TABLE IF NOT EXISTS "05_grc_library"."08_dim_test_result_statuses" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_08_dim_test_result_statuses      PRIMARY KEY (id),
    CONSTRAINT uq_08_dim_test_result_statuses_code UNIQUE (code)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- FACT TABLES (10-15) — LEAN: only structural columns
-- ─────────────────────────────────────────────────────────────────────────────

-- 10_fct_frameworks
-- Lean: tenant_key, code, type FK, category FK, scope FKs, flags only.
-- name, description, publisher info, logo_url → 20_dtl_framework_properties
CREATE TABLE IF NOT EXISTS "05_grc_library"."10_fct_frameworks" (
    id                      UUID         NOT NULL,
    tenant_key              VARCHAR(100) NOT NULL,
    framework_code          VARCHAR(100) NOT NULL,
    framework_type_code     VARCHAR(50)  NOT NULL,
    framework_category_code VARCHAR(50)  NOT NULL,
    scope_org_id            UUID         NULL,
    scope_workspace_id      UUID         NULL,
    approval_status         VARCHAR(50)  NOT NULL DEFAULT 'draft',
    is_marketplace_visible  BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active               BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted              BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test                 BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system               BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked               BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMP    NOT NULL,
    updated_at              TIMESTAMP    NOT NULL,
    created_by              UUID         NULL,
    updated_by              UUID         NULL,
    deleted_at              TIMESTAMP    NULL,
    deleted_by              UUID         NULL,
    CONSTRAINT pk_10_fct_frameworks              PRIMARY KEY (id),
    CONSTRAINT uq_10_fct_frameworks_code         UNIQUE (tenant_key, framework_code),
    CONSTRAINT ck_10_fct_frameworks_approval     CHECK (approval_status IN ('draft','pending_review','approved','rejected','suspended')),
    CONSTRAINT fk_10_fct_frameworks_type         FOREIGN KEY (framework_type_code)
        REFERENCES "05_grc_library"."02_dim_framework_types" (code),
    CONSTRAINT fk_10_fct_frameworks_category     FOREIGN KEY (framework_category_code)
        REFERENCES "05_grc_library"."03_dim_framework_categories" (code),
    CONSTRAINT fk_10_fct_frameworks_org          FOREIGN KEY (scope_org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_10_fct_frameworks_workspace    FOREIGN KEY (scope_workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
);

-- 11_fct_framework_versions — immutable snapshots
-- version_label, release_notes → 21_dtl_version_properties
CREATE TABLE IF NOT EXISTS "05_grc_library"."11_fct_framework_versions" (
    id                  UUID         NOT NULL,
    framework_id        UUID         NOT NULL,
    version_code        VARCHAR(50)  NOT NULL,
    change_severity     VARCHAR(30)  NOT NULL DEFAULT 'minor',
    lifecycle_state     VARCHAR(30)  NOT NULL DEFAULT 'draft',
    control_count       INTEGER      NOT NULL DEFAULT 0,
    previous_version_id UUID         NULL,
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled         BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted          BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMP    NOT NULL,
    updated_at          TIMESTAMP    NOT NULL,
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    deleted_at          TIMESTAMP    NULL,
    deleted_by          UUID         NULL,
    CONSTRAINT pk_11_fct_framework_versions              PRIMARY KEY (id),
    CONSTRAINT uq_11_fct_framework_versions_code         UNIQUE (framework_id, version_code),
    CONSTRAINT ck_11_fct_framework_versions_severity     CHECK (change_severity IN ('breaking','major','minor','patch')),
    CONSTRAINT ck_11_fct_framework_versions_lifecycle    CHECK (lifecycle_state IN ('draft','published','deprecated','archived')),
    CONSTRAINT fk_11_fct_framework_versions_framework    FOREIGN KEY (framework_id)
        REFERENCES "05_grc_library"."10_fct_frameworks" (id),
    CONSTRAINT fk_11_fct_framework_versions_prev         FOREIGN KEY (previous_version_id)
        REFERENCES "05_grc_library"."11_fct_framework_versions" (id)
);

-- 12_fct_requirements — groupings within a framework ("CC6.1 — Logical Access")
-- name, description → 22_dtl_requirement_properties
CREATE TABLE IF NOT EXISTS "05_grc_library"."12_fct_requirements" (
    id                    UUID         NOT NULL,
    framework_id          UUID         NOT NULL,
    requirement_code      VARCHAR(100) NOT NULL,
    sort_order            INTEGER      NOT NULL DEFAULT 0,
    parent_requirement_id UUID         NULL,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted            BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test               BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system             BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked             BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at            TIMESTAMP    NOT NULL,
    updated_at            TIMESTAMP    NOT NULL,
    created_by            UUID         NULL,
    updated_by            UUID         NULL,
    deleted_at            TIMESTAMP    NULL,
    deleted_by            UUID         NULL,
    CONSTRAINT pk_12_fct_requirements           PRIMARY KEY (id),
    CONSTRAINT uq_12_fct_requirements_code      UNIQUE (framework_id, requirement_code),
    CONSTRAINT fk_12_fct_requirements_framework FOREIGN KEY (framework_id)
        REFERENCES "05_grc_library"."10_fct_frameworks" (id),
    CONSTRAINT fk_12_fct_requirements_parent    FOREIGN KEY (parent_requirement_id)
        REFERENCES "05_grc_library"."12_fct_requirements" (id)
);

-- 13_fct_controls — controls belong to ONE framework
-- name, description, guidance → 23_dtl_control_properties
CREATE TABLE IF NOT EXISTS "05_grc_library"."13_fct_controls" (
    id                     UUID         NOT NULL,
    framework_id           UUID         NOT NULL,
    requirement_id         UUID         NULL,
    tenant_key             VARCHAR(100) NOT NULL,
    control_code           VARCHAR(100) NOT NULL,
    control_category_code  VARCHAR(50)  NOT NULL,
    criticality_code       VARCHAR(50)  NOT NULL DEFAULT 'medium',
    control_type           VARCHAR(50)  NOT NULL DEFAULT 'preventive',
    automation_potential   VARCHAR(30)  NOT NULL DEFAULT 'manual',
    sort_order             INTEGER      NOT NULL DEFAULT 0,
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
    CONSTRAINT pk_13_fct_controls                  PRIMARY KEY (id),
    CONSTRAINT uq_13_fct_controls_code             UNIQUE (framework_id, control_code),
    CONSTRAINT ck_13_fct_controls_type             CHECK (control_type IN ('preventive','detective','corrective','compensating')),
    CONSTRAINT ck_13_fct_controls_automation       CHECK (automation_potential IN ('full','partial','manual')),
    CONSTRAINT fk_13_fct_controls_framework        FOREIGN KEY (framework_id)
        REFERENCES "05_grc_library"."10_fct_frameworks" (id),
    CONSTRAINT fk_13_fct_controls_requirement      FOREIGN KEY (requirement_id)
        REFERENCES "05_grc_library"."12_fct_requirements" (id),
    CONSTRAINT fk_13_fct_controls_category         FOREIGN KEY (control_category_code)
        REFERENCES "05_grc_library"."04_dim_control_categories" (code),
    CONSTRAINT fk_13_fct_controls_criticality      FOREIGN KEY (criticality_code)
        REFERENCES "05_grc_library"."05_dim_control_criticalities" (code)
);

-- 14_fct_control_tests — reusable tests/checks (many-to-many with controls)
-- name, description, evaluation_rule → 24_dtl_test_properties
CREATE TABLE IF NOT EXISTS "05_grc_library"."14_fct_control_tests" (
    id                   UUID         NOT NULL,
    tenant_key           VARCHAR(100) NOT NULL,
    test_code            VARCHAR(100) NOT NULL,
    test_type_code       VARCHAR(50)  NOT NULL,
    integration_type     VARCHAR(50)  NULL,
    monitoring_frequency VARCHAR(30)  NOT NULL DEFAULT 'manual',
    is_platform_managed  BOOLEAN      NOT NULL DEFAULT FALSE,
    is_active            BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled          BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted           BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test              BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system            BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked            BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMP    NOT NULL,
    updated_at           TIMESTAMP    NOT NULL,
    created_by           UUID         NULL,
    updated_by           UUID         NULL,
    deleted_at           TIMESTAMP    NULL,
    deleted_by           UUID         NULL,
    CONSTRAINT pk_14_fct_control_tests           PRIMARY KEY (id),
    CONSTRAINT uq_14_fct_control_tests_code      UNIQUE (tenant_key, test_code),
    CONSTRAINT ck_14_fct_control_tests_frequency CHECK (monitoring_frequency IN ('realtime','hourly','daily','weekly','manual')),
    CONSTRAINT fk_14_fct_control_tests_type      FOREIGN KEY (test_type_code)
        REFERENCES "05_grc_library"."07_dim_test_types" (code)
);


-- ─────────────────────────────────────────────────────────────────────────────
-- DETAIL / EAV TABLES (20-26)
-- ALL descriptive data lives here. Fact tables stay clean.
-- No FK to property_keys dimension — unconstrained keys.
-- ─────────────────────────────────────────────────────────────────────────────

-- Framework properties: name, description, publisher_name, publisher_type,
--   logo_url, documentation_url, short_description
CREATE TABLE IF NOT EXISTS "05_grc_library"."20_dtl_framework_properties" (
    id             UUID         NOT NULL,
    framework_id   UUID         NOT NULL,
    property_key   VARCHAR(80)  NOT NULL,
    property_value TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_20_dtl_fw_props          PRIMARY KEY (id),
    CONSTRAINT uq_20_dtl_fw_props_key      UNIQUE (framework_id, property_key),
    CONSTRAINT fk_20_dtl_fw_props_fw       FOREIGN KEY (framework_id)
        REFERENCES "05_grc_library"."10_fct_frameworks" (id) ON DELETE CASCADE
);

-- Version properties: version_label, release_notes, change_summary
CREATE TABLE IF NOT EXISTS "05_grc_library"."21_dtl_version_properties" (
    id                  UUID         NOT NULL,
    framework_version_id UUID        NOT NULL,
    property_key        VARCHAR(80)  NOT NULL,
    property_value      TEXT         NOT NULL,
    created_at          TIMESTAMP    NOT NULL,
    updated_at          TIMESTAMP    NOT NULL,
    created_by          UUID         NULL,
    updated_by          UUID         NULL,
    CONSTRAINT pk_21_dtl_ver_props       PRIMARY KEY (id),
    CONSTRAINT uq_21_dtl_ver_props_key   UNIQUE (framework_version_id, property_key),
    CONSTRAINT fk_21_dtl_ver_props_ver   FOREIGN KEY (framework_version_id)
        REFERENCES "05_grc_library"."11_fct_framework_versions" (id) ON DELETE CASCADE
);

-- Requirement properties: name, description
CREATE TABLE IF NOT EXISTS "05_grc_library"."22_dtl_requirement_properties" (
    id             UUID         NOT NULL,
    requirement_id UUID         NOT NULL,
    property_key   VARCHAR(80)  NOT NULL,
    property_value TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_22_dtl_req_props        PRIMARY KEY (id),
    CONSTRAINT uq_22_dtl_req_props_key    UNIQUE (requirement_id, property_key),
    CONSTRAINT fk_22_dtl_req_props_req    FOREIGN KEY (requirement_id)
        REFERENCES "05_grc_library"."12_fct_requirements" (id) ON DELETE CASCADE
);

-- Control properties: name, description, guidance, implementation_notes
CREATE TABLE IF NOT EXISTS "05_grc_library"."23_dtl_control_properties" (
    id             UUID         NOT NULL,
    control_id     UUID         NOT NULL,
    property_key   VARCHAR(80)  NOT NULL,
    property_value TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_23_dtl_ctrl_props        PRIMARY KEY (id),
    CONSTRAINT uq_23_dtl_ctrl_props_key    UNIQUE (control_id, property_key),
    CONSTRAINT fk_23_dtl_ctrl_props_ctrl   FOREIGN KEY (control_id)
        REFERENCES "05_grc_library"."13_fct_controls" (id) ON DELETE CASCADE
);

-- Test properties: name, description, evaluation_rule (JSON), signal_type, integration_guide
CREATE TABLE IF NOT EXISTS "05_grc_library"."24_dtl_test_properties" (
    id             UUID         NOT NULL,
    test_id        UUID         NOT NULL,
    property_key   VARCHAR(80)  NOT NULL,
    property_value TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_24_dtl_test_props        PRIMARY KEY (id),
    CONSTRAINT uq_24_dtl_test_props_key    UNIQUE (test_id, property_key),
    CONSTRAINT fk_24_dtl_test_props_test   FOREIGN KEY (test_id)
        REFERENCES "05_grc_library"."14_fct_control_tests" (id) ON DELETE CASCADE
);

-- Framework settings: configurable framework behaviour (EAV)
-- Expected keys: auto_publish, notification_on_update, default_review_period_days,
--   require_approval_for_publish, max_controls_per_version, enable_cross_framework_mappings
CREATE TABLE IF NOT EXISTS "05_grc_library"."25_dtl_framework_settings" (
    id             UUID         NOT NULL,
    framework_id   UUID         NOT NULL,
    setting_key    VARCHAR(100) NOT NULL,
    setting_value  TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_25_dtl_framework_settings      PRIMARY KEY (id),
    CONSTRAINT uq_25_dtl_framework_settings_key  UNIQUE (framework_id, setting_key),
    CONSTRAINT fk_25_dtl_framework_settings_fw   FOREIGN KEY (framework_id)
        REFERENCES "05_grc_library"."10_fct_frameworks" (id) ON DELETE CASCADE
);


-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLES (27) — Immutable
-- ─────────────────────────────────────────────────────────────────────────────

-- Version changelog: auto-generated diff when a version is published
-- Records what changed between versions (controls/requirements added/removed/modified)
CREATE TABLE IF NOT EXISTS "05_grc_library"."27_trx_version_changelog_items" (
    id                    UUID         NOT NULL,
    framework_version_id  UUID         NOT NULL,
    change_type           VARCHAR(30)  NOT NULL,
    entity_type           VARCHAR(30)  NOT NULL,
    entity_id             UUID         NOT NULL,
    entity_code           VARCHAR(100) NOT NULL,
    field_name            VARCHAR(80)  NULL,         -- NULL for add/remove
    old_value             TEXT         NULL,          -- NULL for add
    new_value             TEXT         NULL,          -- NULL for remove
    created_at            TIMESTAMP    NOT NULL,
    CONSTRAINT pk_27_trx_version_changelog           PRIMARY KEY (id),
    CONSTRAINT ck_27_trx_changelog_change            CHECK (change_type IN ('added','removed','modified')),
    CONSTRAINT ck_27_trx_changelog_entity            CHECK (entity_type IN ('control','requirement')),
    CONSTRAINT fk_27_trx_changelog_version           FOREIGN KEY (framework_version_id)
        REFERENCES "05_grc_library"."11_fct_framework_versions" (id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- LINK TABLES (30-32)
-- ─────────────────────────────────────────────────────────────────────────────

-- Tests ↔ Controls: many-to-many
-- One "Okta MFA Check" test maps to SOC 2 CC6.1, ISO A.9.4, PCI MFA control
CREATE TABLE IF NOT EXISTS "05_grc_library"."30_lnk_test_control_mappings" (
    id              UUID      NOT NULL,
    control_test_id UUID      NOT NULL,
    control_id      UUID      NOT NULL,
    is_primary      BOOLEAN   NOT NULL DEFAULT FALSE,
    sort_order      INTEGER   NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL,
    created_by      UUID      NULL,
    CONSTRAINT pk_30_lnk_test_control_mappings           PRIMARY KEY (id),
    CONSTRAINT uq_30_lnk_test_control_mappings           UNIQUE (control_test_id, control_id),
    CONSTRAINT fk_30_lnk_test_control_mappings_test      FOREIGN KEY (control_test_id)
        REFERENCES "05_grc_library"."14_fct_control_tests" (id) ON DELETE CASCADE,
    CONSTRAINT fk_30_lnk_test_control_mappings_control   FOREIGN KEY (control_id)
        REFERENCES "05_grc_library"."13_fct_controls" (id) ON DELETE CASCADE
);

-- Controls included in a specific published version
CREATE TABLE IF NOT EXISTS "05_grc_library"."31_lnk_framework_version_controls" (
    id                  UUID      NOT NULL,
    framework_version_id UUID     NOT NULL,
    control_id          UUID      NOT NULL,
    sort_order          INTEGER   NOT NULL DEFAULT 0,
    created_at          TIMESTAMP NOT NULL,
    created_by          UUID      NULL,
    CONSTRAINT pk_31_lnk_fw_version_controls             PRIMARY KEY (id),
    CONSTRAINT uq_31_lnk_fw_version_controls             UNIQUE (framework_version_id, control_id),
    CONSTRAINT fk_31_lnk_fw_version_controls_version     FOREIGN KEY (framework_version_id)
        REFERENCES "05_grc_library"."11_fct_framework_versions" (id) ON DELETE CASCADE,
    CONSTRAINT fk_31_lnk_fw_version_controls_control     FOREIGN KEY (control_id)
        REFERENCES "05_grc_library"."13_fct_controls" (id) ON DELETE CASCADE
);


-- ─────────────────────────────────────────────────────────────────────────────
-- VIEWS (40-42) — Reassemble fact + EAV for API consumption
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "05_grc_library"."40_vw_framework_catalog" AS
SELECT
    f.id,
    f.tenant_key,
    f.framework_code,
    f.framework_type_code,
    ft.name                         AS type_name,
    f.framework_category_code,
    fc.name                         AS category_name,
    f.scope_org_id,
    f.scope_workspace_id,
    f.approval_status,
    f.is_marketplace_visible,
    f.is_active,
    f.is_deleted,
    f.created_at,
    f.updated_at,
    f.created_by,
    -- EAV properties flattened
    p_name.property_value           AS name,
    p_desc.property_value           AS description,
    p_short.property_value          AS short_description,
    p_pub_type.property_value       AS publisher_type,
    p_pub_name.property_value       AS publisher_name,
    p_logo.property_value           AS logo_url,
    p_docs.property_value           AS documentation_url,
    -- Latest published version (subquery)
    (SELECT v.version_code
     FROM "05_grc_library"."11_fct_framework_versions" v
     WHERE v.framework_id = f.id
       AND v.lifecycle_state = 'published'
       AND v.is_deleted = FALSE
     ORDER BY v.created_at DESC
     LIMIT 1)                       AS latest_version_code,
    (SELECT COUNT(*)
     FROM "05_grc_library"."13_fct_controls" c
     WHERE c.framework_id = f.id
       AND c.is_deleted = FALSE)    AS control_count
FROM "05_grc_library"."10_fct_frameworks" f
LEFT JOIN "05_grc_library"."02_dim_framework_types" ft
    ON ft.code = f.framework_type_code
LEFT JOIN "05_grc_library"."03_dim_framework_categories" fc
    ON fc.code = f.framework_category_code
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
    ON p_name.framework_id = f.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_desc
    ON p_desc.framework_id = f.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_short
    ON p_short.framework_id = f.id AND p_short.property_key = 'short_description'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub_type
    ON p_pub_type.framework_id = f.id AND p_pub_type.property_key = 'publisher_type'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub_name
    ON p_pub_name.framework_id = f.id AND p_pub_name.property_key = 'publisher_name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_logo
    ON p_logo.framework_id = f.id AND p_logo.property_key = 'logo_url'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_docs
    ON p_docs.framework_id = f.id AND p_docs.property_key = 'documentation_url'
WHERE f.is_deleted = FALSE;

CREATE OR REPLACE VIEW "05_grc_library"."41_vw_control_detail" AS
SELECT
    c.id,
    c.framework_id,
    c.requirement_id,
    c.tenant_key,
    c.control_code,
    c.control_category_code,
    cat.name                    AS category_name,
    c.criticality_code,
    crit.name                   AS criticality_name,
    c.control_type,
    c.automation_potential,
    c.sort_order,
    c.is_active,
    c.is_deleted,
    c.created_at,
    c.updated_at,
    -- EAV properties flattened
    p_name.property_value       AS name,
    p_desc.property_value       AS description,
    p_guid.property_value       AS guidance,
    p_impl.property_value       AS implementation_notes,
    -- Framework info
    f.framework_code,
    fw_name.property_value      AS framework_name,
    -- Requirement info
    r.requirement_code,
    rq_name.property_value      AS requirement_name,
    -- Test count
    (SELECT COUNT(*)
     FROM "05_grc_library"."30_lnk_test_control_mappings" m
     WHERE m.control_id = c.id) AS test_count
FROM "05_grc_library"."13_fct_controls" c
LEFT JOIN "05_grc_library"."04_dim_control_categories" cat
    ON cat.code = c.control_category_code
LEFT JOIN "05_grc_library"."05_dim_control_criticalities" crit
    ON crit.code = c.criticality_code
LEFT JOIN "05_grc_library"."10_fct_frameworks" f
    ON f.id = c.framework_id
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fw_name
    ON fw_name.framework_id = f.id AND fw_name.property_key = 'name'
LEFT JOIN "05_grc_library"."12_fct_requirements" r
    ON r.id = c.requirement_id
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" rq_name
    ON rq_name.requirement_id = r.id AND rq_name.property_key = 'name'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
    ON p_name.control_id = c.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
    ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guid
    ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_impl
    ON p_impl.control_id = c.id AND p_impl.property_key = 'implementation_notes'
WHERE c.is_deleted = FALSE;

CREATE OR REPLACE VIEW "05_grc_library"."42_vw_test_detail" AS
SELECT
    t.id,
    t.tenant_key,
    t.test_code,
    t.test_type_code,
    tt.name                         AS test_type_name,
    t.integration_type,
    t.monitoring_frequency,
    t.is_platform_managed,
    t.is_active,
    t.is_deleted,
    t.created_at,
    t.updated_at,
    -- EAV properties flattened
    p_name.property_value           AS name,
    p_desc.property_value           AS description,
    p_rule.property_value           AS evaluation_rule,
    p_sig.property_value            AS signal_type,
    p_guide.property_value          AS integration_guide,
    -- Mapped control count
    (SELECT COUNT(*)
     FROM "05_grc_library"."30_lnk_test_control_mappings" m
     WHERE m.control_test_id = t.id) AS mapped_control_count
FROM "05_grc_library"."14_fct_control_tests" t
LEFT JOIN "05_grc_library"."07_dim_test_types" tt
    ON tt.code = t.test_type_code
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_name
    ON p_name.test_id = t.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_desc
    ON p_desc.test_id = t.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_rule
    ON p_rule.test_id = t.id AND p_rule.property_key = 'evaluation_rule'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_sig
    ON p_sig.test_id = t.id AND p_sig.property_key = 'signal_type'
LEFT JOIN "05_grc_library"."24_dtl_test_properties" p_guide
    ON p_guide.test_id = t.id AND p_guide.property_key = 'integration_guide'
WHERE t.is_deleted = FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

-- Fact: frameworks
CREATE INDEX IF NOT EXISTS idx_10_fct_frameworks_tenant
    ON "05_grc_library"."10_fct_frameworks" (tenant_key) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_frameworks_type
    ON "05_grc_library"."10_fct_frameworks" (framework_type_code) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_frameworks_category
    ON "05_grc_library"."10_fct_frameworks" (framework_category_code) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_frameworks_org
    ON "05_grc_library"."10_fct_frameworks" (scope_org_id) WHERE is_deleted = FALSE;

-- Fact: versions
CREATE INDEX IF NOT EXISTS idx_11_fct_versions_framework
    ON "05_grc_library"."11_fct_framework_versions" (framework_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_11_fct_versions_lifecycle
    ON "05_grc_library"."11_fct_framework_versions" (lifecycle_state) WHERE is_deleted = FALSE;

-- Fact: requirements
CREATE INDEX IF NOT EXISTS idx_12_fct_requirements_framework
    ON "05_grc_library"."12_fct_requirements" (framework_id) WHERE is_deleted = FALSE;

-- Fact: controls
CREATE INDEX IF NOT EXISTS idx_13_fct_controls_framework
    ON "05_grc_library"."13_fct_controls" (framework_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_13_fct_controls_requirement
    ON "05_grc_library"."13_fct_controls" (requirement_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_13_fct_controls_category
    ON "05_grc_library"."13_fct_controls" (control_category_code) WHERE is_deleted = FALSE;

-- Fact: control tests
CREATE INDEX IF NOT EXISTS idx_14_fct_control_tests_tenant
    ON "05_grc_library"."14_fct_control_tests" (tenant_key) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_14_fct_control_tests_type
    ON "05_grc_library"."14_fct_control_tests" (test_type_code) WHERE is_deleted = FALSE;


-- Detail: EAV composite lookups
CREATE INDEX IF NOT EXISTS idx_20_dtl_fw_props_key
    ON "05_grc_library"."20_dtl_framework_properties" (framework_id, property_key);
CREATE INDEX IF NOT EXISTS idx_23_dtl_ctrl_props_key
    ON "05_grc_library"."23_dtl_control_properties" (control_id, property_key);
CREATE INDEX IF NOT EXISTS idx_24_dtl_test_props_key
    ON "05_grc_library"."24_dtl_test_properties" (test_id, property_key);

-- Link: test↔control mappings
CREATE INDEX IF NOT EXISTS idx_30_lnk_test_control_mappings_test
    ON "05_grc_library"."30_lnk_test_control_mappings" (control_test_id);
CREATE INDEX IF NOT EXISTS idx_30_lnk_test_control_mappings_control
    ON "05_grc_library"."30_lnk_test_control_mappings" (control_id);

-- Link: version↔controls
CREATE INDEX IF NOT EXISTS idx_31_lnk_fw_version_controls_version
    ON "05_grc_library"."31_lnk_framework_version_controls" (framework_version_id);


-- Transaction: version changelog
CREATE INDEX IF NOT EXISTS idx_27_trx_changelog_version
    ON "05_grc_library"."27_trx_version_changelog_items" (framework_version_id, created_at);
CREATE INDEX IF NOT EXISTS idx_27_trx_changelog_entity
    ON "05_grc_library"."27_trx_version_changelog_items" (entity_type, entity_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SEED DATA — Dimension tables
-- Deterministic UUIDs for idempotent seeding
-- ─────────────────────────────────────────────────────────────────────────────

-- Framework types
INSERT INTO "05_grc_library"."02_dim_framework_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('a0010001-0000-0000-0000-000000000000', 'compliance_standard', 'Compliance Standard', 'Regulatory compliance frameworks (SOC 2, PCI DSS, HIPAA)',  1, TRUE, NOW(), NOW()),
    ('a0010002-0000-0000-0000-000000000000', 'security_framework',  'Security Framework',  'Information security frameworks (ISO 27001, NIST CSF)',     2, TRUE, NOW(), NOW()),
    ('a0010003-0000-0000-0000-000000000000', 'privacy_regulation',  'Privacy Regulation',  'Data privacy regulations (GDPR, CCPA, LGPD)',               3, TRUE, NOW(), NOW()),
    ('a0010004-0000-0000-0000-000000000000', 'industry_standard',   'Industry Standard',   'Industry-specific standards (HITRUST, FedRAMP)',             4, TRUE, NOW(), NOW()),
    ('a0010005-0000-0000-0000-000000000000', 'internal_policy',     'Internal Policy',     'Organisation-defined internal policies',                     5, TRUE, NOW(), NOW()),
    ('a0010006-0000-0000-0000-000000000000', 'custom',              'Custom',              'Custom framework definitions',                               6, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Framework categories
INSERT INTO "05_grc_library"."03_dim_framework_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('a0000001-0000-0000-0000-000000000000', 'compliance',    'Compliance',    'Regulatory and compliance frameworks',             1, TRUE, NOW(), NOW()),
    ('a0000002-0000-0000-0000-000000000000', 'security',      'Security',      'Information security and cybersecurity frameworks', 2, TRUE, NOW(), NOW()),
    ('a0000003-0000-0000-0000-000000000000', 'privacy',       'Privacy',       'Data privacy and protection frameworks',            3, TRUE, NOW(), NOW()),
    ('a0000004-0000-0000-0000-000000000000', 'industry',      'Industry',      'Industry-specific regulatory frameworks',           4, TRUE, NOW(), NOW()),
    ('a0000005-0000-0000-0000-000000000000', 'operational',   'Operational',   'Operational risk and resilience frameworks',         5, TRUE, NOW(), NOW()),
    ('a0000006-0000-0000-0000-000000000000', 'custom',        'Custom',        'Organisation-defined custom frameworks',            6, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Control categories
INSERT INTO "05_grc_library"."04_dim_control_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000000', 'access_control',      'Access Control',      'User authentication, authorisation, MFA',      1, TRUE, NOW(), NOW()),
    ('b0000002-0000-0000-0000-000000000000', 'change_management',   'Change Management',   'Change control, SDLC, release processes',      2, TRUE, NOW(), NOW()),
    ('b0000003-0000-0000-0000-000000000000', 'incident_response',   'Incident Response',   'Detection, response, and recovery',            3, TRUE, NOW(), NOW()),
    ('b0000004-0000-0000-0000-000000000000', 'data_protection',     'Data Protection',     'Encryption, DLP, data classification',         4, TRUE, NOW(), NOW()),
    ('b0000005-0000-0000-0000-000000000000', 'network_security',    'Network Security',    'Firewalls, segmentation, monitoring',          5, TRUE, NOW(), NOW()),
    ('b0000006-0000-0000-0000-000000000000', 'physical_security',   'Physical Security',   'Facility access, physical controls',           6, TRUE, NOW(), NOW()),
    ('b0000007-0000-0000-0000-000000000000', 'risk_management',     'Risk Management',     'Risk assessment, treatment, tracking',         7, TRUE, NOW(), NOW()),
    ('b0000008-0000-0000-0000-000000000000', 'vendor_management',   'Vendor Management',   'Third-party risk and due diligence',           8, TRUE, NOW(), NOW()),
    ('b0000009-0000-0000-0000-000000000000', 'hr_security',         'HR Security',         'Hiring, offboarding, security training',       9, TRUE, NOW(), NOW()),
    ('b0000010-0000-0000-0000-000000000000', 'business_continuity', 'Business Continuity', 'BCP, DR, availability',                       10, TRUE, NOW(), NOW()),
    ('b0000011-0000-0000-0000-000000000000', 'cryptography',        'Cryptography',        'Key management, cert rotation',               11, TRUE, NOW(), NOW()),
    ('b0000012-0000-0000-0000-000000000000', 'logging_monitoring',  'Logging & Monitoring','Audit logs, SIEM, alerting',                  12, TRUE, NOW(), NOW()),
    ('b0000013-0000-0000-0000-000000000000', 'asset_management',    'Asset Management',    'Asset inventory, lifecycle, classification',   13, TRUE, NOW(), NOW()),
    ('b0000014-0000-0000-0000-000000000000', 'compliance',          'Compliance',          'Regulatory compliance checks',                14, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Control criticalities
INSERT INTO "05_grc_library"."05_dim_control_criticalities" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('c0000001-0000-0000-0000-000000000000', 'critical', 'Critical', 'Must be implemented — breach = immediate exposure', 1, TRUE, NOW(), NOW()),
    ('c0000002-0000-0000-0000-000000000000', 'high',     'High',     'Should be implemented promptly',                    2, TRUE, NOW(), NOW()),
    ('c0000003-0000-0000-0000-000000000000', 'medium',   'Medium',   'Implement within current compliance cycle',         3, TRUE, NOW(), NOW()),
    ('c0000004-0000-0000-0000-000000000000', 'low',      'Low',      'Implement at next opportunity',                     4, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Test types
INSERT INTO "05_grc_library"."07_dim_test_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('e0000001-0000-0000-0000-000000000000', 'automated',      'Automated',      'Fully automated test via connector/API',              1, TRUE, NOW(), NOW()),
    ('e0000002-0000-0000-0000-000000000000', 'manual',         'Manual',         'Requires human review and attestation',               2, TRUE, NOW(), NOW()),
    ('e0000003-0000-0000-0000-000000000000', 'semi_automated', 'Semi-Automated', 'Automated signal collection + manual interpretation', 3, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Test result statuses
INSERT INTO "05_grc_library"."08_dim_test_result_statuses" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('f0000001-0000-0000-0000-000000000000', 'pass',    'Pass',    'Control is operating effectively',          1, TRUE, NOW(), NOW()),
    ('f0000002-0000-0000-0000-000000000000', 'fail',    'Fail',    'Control failure detected',                  2, TRUE, NOW(), NOW()),
    ('f0000003-0000-0000-0000-000000000000', 'partial', 'Partial', 'Control partially effective',               3, TRUE, NOW(), NOW()),
    ('f0000004-0000-0000-0000-000000000000', 'unknown', 'Unknown', 'Insufficient evidence to determine result', 4, TRUE, NOW(), NOW()),
    ('f0000005-0000-0000-0000-000000000000', 'error',   'Error',   'Test execution error',                      5, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
