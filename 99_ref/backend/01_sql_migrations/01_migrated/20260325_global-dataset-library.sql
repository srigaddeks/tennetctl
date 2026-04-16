-- ═══════════════════════════════════════════════════════════════════════════════
-- Global Dataset Library — Platform-scoped dataset templates
-- Published by super admins from sandbox, consumed by all orgs/workspaces.
-- ═══════════════════════════════════════════════════════════════════════════════

-- ---------------------------------------------------------------------------
-- 80_fct_global_datasets — Versioned global dataset catalog
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."80_fct_global_datasets" (
    id                   UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_code          VARCHAR(100)  NOT NULL,
    connector_type_code  VARCHAR(50)   NOT NULL,
    version_number       INTEGER       NOT NULL DEFAULT 1,
    source_dataset_id    UUID          NULL,
    source_org_id        UUID          NULL,

    json_schema          JSONB         NOT NULL DEFAULT '{}',
    sample_payload       JSONB         NOT NULL DEFAULT '[]',
    record_count         INTEGER       NOT NULL DEFAULT 0,

    publish_status       VARCHAR(20)   NOT NULL DEFAULT 'published',
    is_featured          BOOLEAN       NOT NULL DEFAULT FALSE,
    download_count       INTEGER       NOT NULL DEFAULT 0,

    published_by         UUID          NULL,
    published_at         TIMESTAMPTZ   NULL,
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    is_deleted           BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_80_fct_global_datasets          PRIMARY KEY (id),
    CONSTRAINT uq_80_fct_global_datasets_version  UNIQUE (global_code, version_number),
    CONSTRAINT fk_80_fct_global_datasets_type     FOREIGN KEY (connector_type_code)
        REFERENCES "15_sandbox"."03_dim_connector_types" (code)
);

CREATE INDEX IF NOT EXISTS idx_80_global_datasets_type
    ON "15_sandbox"."80_fct_global_datasets" (connector_type_code)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_80_global_datasets_status
    ON "15_sandbox"."80_fct_global_datasets" (publish_status)
    WHERE is_active AND NOT is_deleted;

CREATE INDEX IF NOT EXISTS idx_80_global_datasets_featured
    ON "15_sandbox"."80_fct_global_datasets" (is_featured)
    WHERE is_active AND NOT is_deleted AND is_featured;


-- ---------------------------------------------------------------------------
-- 81_dtl_global_dataset_properties — EAV for descriptive fields
-- Keys: name, description, tags, category, collection_query,
--        compatible_asset_types, changelog
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."81_dtl_global_dataset_properties" (
    id              UUID          NOT NULL DEFAULT gen_random_uuid(),
    dataset_id      UUID          NOT NULL,
    property_key    VARCHAR(100)  NOT NULL,
    property_value  TEXT          NOT NULL DEFAULT '',

    CONSTRAINT pk_81_dtl_global_dataset_properties      PRIMARY KEY (id),
    CONSTRAINT uq_81_dtl_global_dataset_properties      UNIQUE (dataset_id, property_key),
    CONSTRAINT fk_81_dtl_global_dataset_properties_ds   FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."80_fct_global_datasets" (id) ON DELETE CASCADE
);


-- ---------------------------------------------------------------------------
-- 82_trx_global_dataset_pulls — Track who pulled what
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "15_sandbox"."82_trx_global_dataset_pulls" (
    id                    UUID          NOT NULL DEFAULT gen_random_uuid(),
    global_dataset_id     UUID          NOT NULL,
    pulled_version        INTEGER       NOT NULL,
    target_org_id         UUID          NOT NULL,
    target_workspace_id   UUID          NULL,
    target_dataset_id     UUID          NULL,
    pulled_by             UUID          NOT NULL,
    pulled_at             TIMESTAMPTZ   NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_82_trx_global_dataset_pulls        PRIMARY KEY (id),
    CONSTRAINT fk_82_trx_global_dataset_pulls_gd     FOREIGN KEY (global_dataset_id)
        REFERENCES "15_sandbox"."80_fct_global_datasets" (id)
);

CREATE INDEX IF NOT EXISTS idx_82_pulls_org
    ON "15_sandbox"."82_trx_global_dataset_pulls" (target_org_id);

CREATE INDEX IF NOT EXISTS idx_82_pulls_global
    ON "15_sandbox"."82_trx_global_dataset_pulls" (global_dataset_id);


-- ---------------------------------------------------------------------------
-- 83_vw_global_dataset_detail — Flattened view for API queries
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "15_sandbox"."83_vw_global_dataset_detail" AS
SELECT
    gd.id,
    gd.global_code,
    gd.connector_type_code,
    ct.name                    AS connector_type_name,
    gd.version_number,
    gd.json_schema,
    gd.sample_payload,
    gd.record_count,
    gd.publish_status,
    gd.is_featured,
    gd.download_count,
    gd.source_dataset_id,
    gd.source_org_id,
    gd.published_by,
    gd.published_at,
    gd.is_active,
    gd.is_deleted,
    gd.created_at,
    gd.updated_at,
    -- Flattened EAV properties
    MAX(CASE WHEN p.property_key = 'name'                   THEN p.property_value END) AS name,
    MAX(CASE WHEN p.property_key = 'description'            THEN p.property_value END) AS description,
    MAX(CASE WHEN p.property_key = 'tags'                   THEN p.property_value END) AS tags,
    MAX(CASE WHEN p.property_key = 'category'               THEN p.property_value END) AS category,
    MAX(CASE WHEN p.property_key = 'collection_query'       THEN p.property_value END) AS collection_query,
    MAX(CASE WHEN p.property_key = 'compatible_asset_types' THEN p.property_value END) AS compatible_asset_types,
    MAX(CASE WHEN p.property_key = 'changelog'              THEN p.property_value END) AS changelog
FROM "15_sandbox"."80_fct_global_datasets" gd
LEFT JOIN "15_sandbox"."81_dtl_global_dataset_properties" p ON p.dataset_id = gd.id
LEFT JOIN "15_sandbox"."03_dim_connector_types" ct ON ct.code = gd.connector_type_code
WHERE NOT gd.is_deleted
GROUP BY gd.id, ct.name;


-- ---------------------------------------------------------------------------
-- Seed 'global_library' as a dataset source code
-- ---------------------------------------------------------------------------
INSERT INTO "15_sandbox"."05_dim_dataset_sources" (code, name, sort_order)
VALUES ('global_library', 'Global Library', 6)
ON CONFLICT (code) DO NOTHING;
