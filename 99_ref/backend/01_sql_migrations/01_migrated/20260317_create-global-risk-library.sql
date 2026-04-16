-- =============================================================================
-- Migration: Global Risk Registry in GRC Library Schema
-- Date: 2026-03-17
-- Schema: 05_grc_library (tables 50-69)
-- Description: Platform-level global risk registry with EAV properties,
--              control mappings, review event audit trail, and detail view.
-- =============================================================================

SET search_path = '05_grc_library';

-- ---------------------------------------------------------------------------
-- FACT: 50_fct_global_risks
-- Platform-level risk registry. Each row is a canonical global risk entry.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "50_fct_global_risks" (
    id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
    tenant_key              VARCHAR(100)    NOT NULL DEFAULT 'default',
    risk_code               VARCHAR(100)    NOT NULL,
    risk_category_code      VARCHAR(50)     NOT NULL,
    risk_level_code         VARCHAR(50),
    inherent_likelihood     INTEGER         CHECK (inherent_likelihood BETWEEN 1 AND 5),
    inherent_impact         INTEGER         CHECK (inherent_impact BETWEEN 1 AND 5),
    inherent_risk_score     SMALLINT        GENERATED ALWAYS AS (inherent_likelihood * inherent_impact) STORED,
    is_active               BOOLEAN         NOT NULL DEFAULT TRUE,
    is_deleted              BOOLEAN         NOT NULL DEFAULT FALSE,
    is_system               BOOLEAN         NOT NULL DEFAULT FALSE,
    created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    created_by              UUID,
    updated_by              UUID,
    deleted_at              TIMESTAMPTZ,
    deleted_by              UUID,

    CONSTRAINT pk_global_risks PRIMARY KEY (id),
    CONSTRAINT uq_global_risk_code UNIQUE (risk_code),

    CONSTRAINT fk_global_risk_category
        FOREIGN KEY (risk_category_code)
        REFERENCES "14_risk_registry"."02_dim_risk_categories" (code)
        DEFERRABLE INITIALLY DEFERRED,

    CONSTRAINT fk_global_risk_level
        FOREIGN KEY (risk_level_code)
        REFERENCES "14_risk_registry"."04_dim_risk_levels" (code)
        DEFERRABLE INITIALLY DEFERRED
);

-- ---------------------------------------------------------------------------
-- DETAIL (EAV): 56_dtl_global_risk_properties
-- Stores human-readable and guidance properties keyed by property_key.
-- Valid keys: title, description, short_description, mitigation_guidance,
--             detection_guidance, references
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "56_dtl_global_risk_properties" (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    global_risk_id  UUID        NOT NULL,
    property_key    VARCHAR(100) NOT NULL,
    property_value  TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,
    updated_by      UUID,

    CONSTRAINT pk_global_risk_properties PRIMARY KEY (id),
    CONSTRAINT uq_global_risk_property UNIQUE (global_risk_id, property_key),

    CONSTRAINT fk_global_risk_property_risk
        FOREIGN KEY (global_risk_id)
        REFERENCES "50_fct_global_risks" (id)
        ON DELETE CASCADE,

    CONSTRAINT chk_global_risk_property_key CHECK (
        property_key IN (
            'title',
            'description',
            'short_description',
            'mitigation_guidance',
            'detection_guidance',
            'references'
        )
    )
);

-- ---------------------------------------------------------------------------
-- LINK: 61_lnk_global_risk_control_mappings
-- Maps global risks to GRC library controls. Typed by mapping_type.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "61_lnk_global_risk_control_mappings" (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    global_risk_id  UUID        NOT NULL,
    control_id      UUID        NOT NULL,
    mapping_type    VARCHAR(30) NOT NULL DEFAULT 'mitigating'
                                CHECK (mapping_type IN ('mitigating', 'compensating', 'related', 'detecting')),
    sort_order      INTEGER     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by      UUID,

    CONSTRAINT pk_global_risk_control_mappings PRIMARY KEY (id),
    CONSTRAINT uq_global_risk_control UNIQUE (global_risk_id, control_id),

    CONSTRAINT fk_global_risk_control_risk
        FOREIGN KEY (global_risk_id)
        REFERENCES "50_fct_global_risks" (id)
        ON DELETE CASCADE,

    CONSTRAINT fk_global_risk_control_control
        FOREIGN KEY (control_id)
        REFERENCES "13_fct_controls" (id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- TRANSACTION: 66_trx_global_risk_review_events
-- Immutable audit trail for all status changes and control links.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS "66_trx_global_risk_review_events" (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    global_risk_id  UUID        NOT NULL,
    event_type      VARCHAR(50) NOT NULL,
    from_status     VARCHAR(30),
    to_status       VARCHAR(30),
    actor_id        UUID,
    notes           TEXT,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_global_risk_review_events PRIMARY KEY (id),

    CONSTRAINT fk_global_risk_review_event_risk
        FOREIGN KEY (global_risk_id)
        REFERENCES "50_fct_global_risks" (id)
        ON DELETE CASCADE
);

-- ---------------------------------------------------------------------------
-- INDEXES
-- ---------------------------------------------------------------------------

-- risk_code lookup (already covered by the unique constraint but explicit idx
-- aids the query planner when doing range or prefix queries)
CREATE INDEX IF NOT EXISTS idx_global_risks_risk_code
    ON "50_fct_global_risks" (risk_code);

-- active filter, excludes soft-deleted rows
CREATE INDEX IF NOT EXISTS idx_global_risks_is_active
    ON "50_fct_global_risks" (is_active)
    WHERE NOT is_deleted;

-- control mapping traversal from risk side
CREATE INDEX IF NOT EXISTS idx_global_risk_control_mappings_risk_id
    ON "61_lnk_global_risk_control_mappings" (global_risk_id);

-- control mapping traversal from control side (reverse lookup)
CREATE INDEX IF NOT EXISTS idx_global_risk_control_mappings_control_id
    ON "61_lnk_global_risk_control_mappings" (control_id);

-- ---------------------------------------------------------------------------
-- VIEW: 69_vw_global_risk_detail
-- Denormalised view joining fact, EAV properties, control count, and
-- dimension labels from the 14_risk_registry schema.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW "69_vw_global_risk_detail" AS
SELECT
    gr.id,
    gr.tenant_key,
    gr.risk_code,
    gr.risk_category_code,
    gr.risk_level_code,
    gr.inherent_likelihood,
    gr.inherent_impact,
    gr.inherent_risk_score,
    gr.is_active,
    gr.is_deleted,
    gr.created_at,
    gr.updated_at,
    gr.created_by,

    -- EAV property pivots
    MAX(CASE WHEN p.property_key = 'title'               THEN p.property_value END) AS title,
    MAX(CASE WHEN p.property_key = 'description'         THEN p.property_value END) AS description,
    MAX(CASE WHEN p.property_key = 'short_description'   THEN p.property_value END) AS short_description,
    MAX(CASE WHEN p.property_key = 'mitigation_guidance' THEN p.property_value END) AS mitigation_guidance,
    MAX(CASE WHEN p.property_key = 'detection_guidance'  THEN p.property_value END) AS detection_guidance,

    -- Linked control count
    COUNT(DISTINCT cm.control_id) AS linked_control_count,

    -- Risk category dimension label
    rc.name AS risk_category_name,

    -- Risk level dimension labels
    rl.name      AS risk_level_name,
    rl.color_hex AS risk_level_color

FROM "50_fct_global_risks" gr

LEFT JOIN "56_dtl_global_risk_properties" p
    ON p.global_risk_id = gr.id

LEFT JOIN "61_lnk_global_risk_control_mappings" cm
    ON cm.global_risk_id = gr.id

LEFT JOIN "14_risk_registry"."02_dim_risk_categories" rc
    ON rc.code = gr.risk_category_code

LEFT JOIN "14_risk_registry"."04_dim_risk_levels" rl
    ON rl.code = gr.risk_level_code

GROUP BY
    gr.id,
    gr.tenant_key,
    gr.risk_code,
    gr.risk_category_code,
    gr.risk_level_code,
    gr.inherent_likelihood,
    gr.inherent_impact,
    gr.inherent_risk_score,
    gr.is_active,
    gr.is_deleted,
    gr.created_at,
    gr.updated_at,
    gr.created_by,
    rc.name,
    rl.name,
    rl.color_hex;
