-- ============================================================
-- Control Tests V2 — Promoted Tests with Versioning + Assets
-- Phase 1: 35_fct_promoted_tests + properties + detail view
-- ============================================================

-- Promoted tests (sandbox-originated, versioned, asset-linked)
CREATE TABLE IF NOT EXISTS "15_sandbox"."35_fct_promoted_tests" (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key           TEXT NOT NULL,
    org_id               UUID NOT NULL,
    workspace_id         UUID NULL,
    promotion_id         UUID REFERENCES "15_sandbox"."30_trx_promotions"(id),
    source_signal_id     UUID,
    source_policy_id     UUID,
    source_library_id    UUID,
    source_pack_id       UUID,  -- set when deployed from global library (Phase 3)
    test_code            TEXT NOT NULL,
    test_type_code       TEXT NOT NULL DEFAULT 'automated',
    monitoring_frequency TEXT NOT NULL DEFAULT 'manual',
    linked_asset_id      UUID,  -- FK to 15_sandbox.20_fct_connector_instances
    version_number       INT NOT NULL DEFAULT 1,
    is_active            BOOLEAN NOT NULL DEFAULT TRUE,
    promoted_by          UUID NOT NULL,
    promoted_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_deleted           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_key, test_code, version_number)
);

CREATE TABLE IF NOT EXISTS "15_sandbox"."36_dtl_promoted_test_properties" (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id         UUID NOT NULL REFERENCES "15_sandbox"."35_fct_promoted_tests"(id),
    property_key    TEXT NOT NULL,
    property_value  TEXT,
    created_by      UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (test_id, property_key)
);

CREATE INDEX IF NOT EXISTS idx_promoted_tests_tenant
    ON "15_sandbox"."35_fct_promoted_tests" (tenant_key, org_id, is_active, is_deleted);

CREATE INDEX IF NOT EXISTS idx_promoted_tests_code
    ON "15_sandbox"."35_fct_promoted_tests" (tenant_key, test_code, version_number DESC);

CREATE INDEX IF NOT EXISTS idx_promoted_tests_asset
    ON "15_sandbox"."35_fct_promoted_tests" (linked_asset_id)
    WHERE linked_asset_id IS NOT NULL;

-- Detail view: flattened promoted test with connector info + properties + GRC control test ID
DROP VIEW IF EXISTS "15_sandbox"."66_vw_promoted_test_detail";
CREATE VIEW "15_sandbox"."66_vw_promoted_test_detail" AS
SELECT
    t.id::text,
    t.tenant_key,
    t.org_id::text,
    t.workspace_id::text,
    t.promotion_id::text,
    t.source_signal_id::text,
    t.source_policy_id::text,
    t.source_library_id::text,
    t.source_pack_id::text,
    t.test_code,
    t.test_type_code,
    t.monitoring_frequency,
    t.linked_asset_id::text,
    t.version_number,
    t.is_active,
    t.promoted_by::text,
    t.promoted_at::text,
    t.is_deleted,
    t.created_at::text,
    t.updated_at::text,
    ci.connector_type_code,
    cip.property_value AS connector_name,
    pr.target_test_id::text AS control_test_id,
    MAX(CASE WHEN p.property_key = 'name'              THEN p.property_value END) AS name,
    MAX(CASE WHEN p.property_key = 'description'       THEN p.property_value END) AS description,
    MAX(CASE WHEN p.property_key = 'evaluation_rule'   THEN p.property_value END) AS evaluation_rule,
    MAX(CASE WHEN p.property_key = 'signal_type'       THEN p.property_value END) AS signal_type,
    MAX(CASE WHEN p.property_key = 'integration_guide' THEN p.property_value END) AS integration_guide
FROM "15_sandbox"."35_fct_promoted_tests" t
LEFT JOIN "15_sandbox"."36_dtl_promoted_test_properties" p
    ON p.test_id = t.id
LEFT JOIN "15_sandbox"."20_fct_connector_instances" ci
    ON ci.id = t.linked_asset_id
LEFT JOIN "15_sandbox"."40_dtl_connector_instance_properties" cip
    ON cip.connector_instance_id = ci.id AND cip.property_key = 'name'
LEFT JOIN "15_sandbox"."30_trx_promotions" pr
    ON pr.id = t.promotion_id
WHERE t.is_deleted = FALSE
GROUP BY
    t.id, t.tenant_key, t.org_id, t.workspace_id, t.promotion_id,
    t.source_signal_id, t.source_policy_id, t.source_library_id, t.source_pack_id,
    t.test_code, t.test_type_code, t.monitoring_frequency,
    t.linked_asset_id, t.version_number, t.is_active,
    t.promoted_by, t.promoted_at, t.is_deleted,
    t.created_at, t.updated_at,
    ci.connector_type_code, cip.property_value, pr.target_test_id;
