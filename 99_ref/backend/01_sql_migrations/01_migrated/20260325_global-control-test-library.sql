-- ═══════════════════════════════════════════════════════════════════════════════
-- Global Control Test Library — Platform-scoped control test bundles
-- Each bundle contains: signal(s) + threat type + policy as a deployable unit.
-- Published by super admins, deployed to any org/workspace.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 84_fct_global_control_tests — Versioned control test bundles
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."84_fct_global_control_tests" (
    id                   UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_code          VARCHAR(100)  NOT NULL,
    connector_type_code  VARCHAR(50)   NOT NULL,
    version_number       INTEGER       NOT NULL DEFAULT 1,

    -- The full bundle: signals[], threat_type{}, policy{}
    bundle               JSONB         NOT NULL DEFAULT '{}',

    -- Source tracking
    source_signal_id     UUID          NULL,
    source_policy_id     UUID          NULL,
    source_library_id    UUID          NULL,
    source_org_id        UUID          NULL,
    linked_dataset_code  VARCHAR(100)  NULL,

    -- Metadata
    publish_status       VARCHAR(20)   NOT NULL DEFAULT 'published',
    is_featured          BOOLEAN       NOT NULL DEFAULT FALSE,
    download_count       INTEGER       NOT NULL DEFAULT 0,
    signal_count         INTEGER       NOT NULL DEFAULT 0,

    published_by         UUID          NULL,
    published_at         TIMESTAMPTZ   NULL,
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_84_fct_global_control_tests          PRIMARY KEY (id),
    CONSTRAINT uq_84_fct_global_control_tests_version  UNIQUE (global_code, version_number),
    CONSTRAINT fk_84_fct_global_control_tests_type     FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);

CREATE INDEX IF NOT EXISTS idx_84_global_tests_type
    ON "15_sandbox"."84_fct_global_control_tests" (connector_type_code)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_84_global_tests_status
    ON "15_sandbox"."84_fct_global_control_tests" (publish_status)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_84_global_tests_dataset
    ON "15_sandbox"."84_fct_global_control_tests" (linked_dataset_code)
    WHERE linked_dataset_code IS NOT NULL AND is_active AND NOT is_deleted;


-- ---------------------------------------------------------------------------
-- 85_dtl_global_control_test_properties — EAV
-- Keys: name, description, tags, category, changelog,
--        compatible_asset_types, compliance_references
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."85_dtl_global_control_test_properties" (
    id              UUID          NOT NULL DEFAULT gen_random_uuid(),
    test_id         UUID          NOT NULL,
    property_key    VARCHAR(100)  NOT NULL,
    property_value  TEXT          NOT NULL DEFAULT '',

    CONSTRAINT pk_85_dtl_global_test_props      PRIMARY KEY (id),
    CONSTRAINT uq_85_dtl_global_test_props      UNIQUE (test_id, property_key),
    CONSTRAINT fk_85_dtl_global_test_props_t    FOREIGN KEY (test_id)
        REFERENCES "15_sandbox"."84_fct_global_control_tests" (id) ON DELETE CASCADE
);


-- ---------------------------------------------------------------------------
-- 86_trx_global_control_test_pulls — Track deployments to workspaces
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."86_trx_global_control_test_pulls" (
    id                     UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_test_id         UUID          NOT NULL,
    pulled_version         INTEGER       NOT NULL,
    target_org_id          UUID          NOT NULL,
    target_workspace_id    UUID          NULL,
    deploy_type            VARCHAR(20)   NOT NULL DEFAULT 'workspace',
    created_signal_ids     UUID[]        NULL,
    created_threat_id      UUID          NULL,
    created_policy_id      UUID          NULL,
    pulled_by              UUID          NOT NULL,
    pulled_at              TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_86_trx_global_test_pulls        PRIMARY KEY (id),
    CONSTRAINT fk_86_trx_global_test_pulls_t      FOREIGN KEY (global_test_id)
        REFERENCES "15_sandbox"."84_fct_global_control_tests" (id)
);

CREATE INDEX IF NOT EXISTS idx_86_pulls_org
    ON "15_sandbox"."86_trx_global_control_test_pulls" (target_org_id);

CREATE INDEX IF NOT EXISTS idx_86_pulls_test
    ON "15_sandbox"."86_trx_global_control_test_pulls" (global_test_id);


-- ---------------------------------------------------------------------------
-- 87_vw_global_control_test_detail — Flattened view
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "15_sandbox"."87_vw_global_control_test_detail" AS
SELECT
    gt.id,
    gt.global_code,
    gt.connector_type_code,
    ct.name                    AS connector_type_name,
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
    -- Flattened EAV
    MAX(CASE WHEN p.property_key = 'name'                   THEN p.property_value END) AS name,
    MAX(CASE WHEN p.property_key = 'description'            THEN p.property_value END) AS description,
    MAX(CASE WHEN p.property_key = 'tags'                   THEN p.property_value END) AS tags,
    MAX(CASE WHEN p.property_key = 'category'               THEN p.property_value END) AS category,
    MAX(CASE WHEN p.property_key = 'changelog'              THEN p.property_value END) AS changelog,
    MAX(CASE WHEN p.property_key = 'compliance_references'  THEN p.property_value END) AS compliance_references
FROM "15_sandbox"."84_fct_global_control_tests" gt
LEFT JOIN "15_sandbox"."85_dtl_global_control_test_properties" p ON p.test_id = gt.id
LEFT JOIN "15_sandbox"."03_dim_connector_types" ct ON ct.code = gt.connector_type_code
WHERE NOT gt.is_deleted
GROUP BY gt.id, ct.name;
