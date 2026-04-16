-- ─────────────────────────────────────────────────────────────────────────────
-- 14_RISK_REGISTRY SCHEMA
-- Global Risk Registry, Assessments, Treatment Plans
--
-- Scoping: Workspace-level (org_id + workspace_id both required)
--   - All risks live inside a workspace
--   - Users access risks through workspace membership
--
-- Pattern: lean fact + EAV (no property_keys dimension — unconstrained keys)
--   - 02-04 dim_*: risk categories, treatment types, risk levels (5×5 matrix)
--   - 10-11 fct_*: LEAN structural only
--   - 20-21 dtl_*: ALL descriptive data (title, description, owner, etc.)
--   - 30-31 lnk_*: cross-schema risk ↔ controls and risk ↔ vendors
--   - 32-33 trx_*: immutable assessment scores and review events
--   - 40    vw_*:  reassembled risk with EAV for API
--
-- Cross-schema FKs:
--   - lnk_risk_control_mappings → 05_grc_library.13_fct_controls
--   - lnk_risk_vendor_mappings  → vendor schema (FK deferred)
--   - fct_risks → 03_auth_manage.29_fct_orgs + 03_auth_manage.34_fct_workspaces
--
-- Audit: ALL lifecycle events go to 03_auth_manage.40_aud_events
-- Domain trx tables: risk assessments (5×5 scoring) + review events (lifecycle)
-- ─────────────────────────────────────────────────────────────────────────────

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES (02-04)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "14_risk_registry"."02_dim_risk_categories" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_02_dim_risk_categories      PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_risk_categories_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "14_risk_registry"."03_dim_risk_treatment_types" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_03_dim_risk_treatment_types      PRIMARY KEY (id),
    CONSTRAINT uq_03_dim_risk_treatment_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "14_risk_registry"."04_dim_risk_levels" (
    id            UUID         NOT NULL,
    code          VARCHAR(50)  NOT NULL,
    name          VARCHAR(100) NOT NULL,
    description   TEXT         NOT NULL,
    score_min     INTEGER      NOT NULL,
    score_max     INTEGER      NOT NULL,
    color_hex     VARCHAR(7)   NOT NULL DEFAULT '#94a3b8',
    sort_order    INTEGER      NOT NULL DEFAULT 0,
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP    NOT NULL,
    updated_at    TIMESTAMP    NOT NULL,
    CONSTRAINT pk_04_dim_risk_levels      PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_risk_levels_code UNIQUE (code)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- FACT TABLES (10-11) — LEAN: only structural columns
-- ─────────────────────────────────────────────────────────────────────────────

-- 10_fct_risks — workspace-scoped risk register
-- title, description, notes, owner_user_id → 20_dtl_risk_properties
CREATE TABLE IF NOT EXISTS "14_risk_registry"."10_fct_risks" (
    id                   UUID         NOT NULL,
    tenant_key           VARCHAR(100) NOT NULL,
    risk_code            VARCHAR(100) NOT NULL,
    org_id               UUID         NOT NULL,
    workspace_id         UUID         NOT NULL,
    risk_category_code   VARCHAR(50)  NOT NULL,
    risk_level_code      VARCHAR(50)  NOT NULL DEFAULT 'medium',
    treatment_type_code  VARCHAR(50)  NOT NULL DEFAULT 'mitigate',
    source_type          VARCHAR(50)  NOT NULL DEFAULT 'manual',
    risk_status          VARCHAR(50)  NOT NULL DEFAULT 'identified',
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
    CONSTRAINT pk_10_fct_risks              PRIMARY KEY (id),
    CONSTRAINT uq_10_fct_risks_code         UNIQUE (tenant_key, risk_code),
    CONSTRAINT ck_10_fct_risks_status       CHECK (risk_status IN ('identified','assessed','treating','accepted','closed')),
    CONSTRAINT ck_10_fct_risks_source       CHECK (source_type IN ('manual','auto_control_failure','vendor_risk','incident')),
    CONSTRAINT fk_10_fct_risks_category     FOREIGN KEY (risk_category_code)
        REFERENCES "14_risk_registry"."02_dim_risk_categories" (code),
    CONSTRAINT fk_10_fct_risks_level        FOREIGN KEY (risk_level_code)
        REFERENCES "14_risk_registry"."04_dim_risk_levels" (code),
    CONSTRAINT fk_10_fct_risks_treatment    FOREIGN KEY (treatment_type_code)
        REFERENCES "14_risk_registry"."03_dim_risk_treatment_types" (code),
    CONSTRAINT fk_10_fct_risks_org          FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_10_fct_risks_workspace    FOREIGN KEY (workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
);

-- 11_fct_risk_treatment_plans — one plan per risk
-- plan_description, action_items → 21_dtl_treatment_plan_properties
CREATE TABLE IF NOT EXISTS "14_risk_registry"."11_fct_risk_treatment_plans" (
    id             UUID         NOT NULL,
    risk_id        UUID         NOT NULL,
    tenant_key     VARCHAR(100) NOT NULL,
    plan_status    VARCHAR(50)  NOT NULL DEFAULT 'draft',
    target_date    TIMESTAMP    NULL,
    completed_at   TIMESTAMP    NULL,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled    BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted     BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system      BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked      BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    deleted_at     TIMESTAMP    NULL,
    deleted_by     UUID         NULL,
    CONSTRAINT pk_11_fct_risk_treatment_plans          PRIMARY KEY (id),
    CONSTRAINT uq_11_fct_risk_treatment_plans_risk     UNIQUE (risk_id),
    CONSTRAINT ck_11_fct_risk_treatment_plans_status   CHECK (plan_status IN ('draft','active','completed','cancelled')),
    CONSTRAINT fk_11_fct_risk_treatment_plans_risk     FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- DETAIL / EAV TABLES (20-21) — No property_keys dimension
-- ─────────────────────────────────────────────────────────────────────────────

-- Risk properties: title, description, notes, owner_user_id, source_reference,
--   remediation_notes, business_impact, likelihood_rationale, impact_rationale
CREATE TABLE IF NOT EXISTS "14_risk_registry"."20_dtl_risk_properties" (
    id             UUID         NOT NULL,
    risk_id        UUID         NOT NULL,
    property_key   VARCHAR(80)  NOT NULL,
    property_value TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_20_dtl_risk_props        PRIMARY KEY (id),
    CONSTRAINT uq_20_dtl_risk_props_key    UNIQUE (risk_id, property_key),
    CONSTRAINT fk_20_dtl_risk_props_risk   FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id) ON DELETE CASCADE
);

-- Treatment plan properties: plan_description, action_items,
--   compensating_control_description, approver_user_id, approval_notes, review_frequency
CREATE TABLE IF NOT EXISTS "14_risk_registry"."21_dtl_treatment_plan_properties" (
    id                UUID         NOT NULL,
    treatment_plan_id UUID         NOT NULL,
    property_key      VARCHAR(80)  NOT NULL,
    property_value    TEXT         NOT NULL,
    created_at        TIMESTAMP    NOT NULL,
    updated_at        TIMESTAMP    NOT NULL,
    created_by        UUID         NULL,
    updated_by        UUID         NULL,
    CONSTRAINT pk_21_dtl_treatment_props         PRIMARY KEY (id),
    CONSTRAINT uq_21_dtl_treatment_props_key     UNIQUE (treatment_plan_id, property_key),
    CONSTRAINT fk_21_dtl_treatment_props_plan    FOREIGN KEY (treatment_plan_id)
        REFERENCES "14_risk_registry"."11_fct_risk_treatment_plans" (id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- LINK TABLES (30-31) — Cross-schema
-- ─────────────────────────────────────────────────────────────────────────────

-- Risk ↔ Controls (many-to-many, cross-schema to 05_grc_library)
CREATE TABLE IF NOT EXISTS "14_risk_registry"."30_lnk_risk_control_mappings" (
    id          UUID         NOT NULL,
    risk_id     UUID         NOT NULL,
    control_id  UUID         NOT NULL,
    link_type   VARCHAR(50)  NOT NULL DEFAULT 'mitigating',
    notes       TEXT         NULL,
    created_at  TIMESTAMP    NOT NULL,
    created_by  UUID         NULL,
    CONSTRAINT pk_30_lnk_risk_control_mappings          PRIMARY KEY (id),
    CONSTRAINT uq_30_lnk_risk_control_mappings          UNIQUE (risk_id, control_id),
    CONSTRAINT ck_30_lnk_risk_control_mappings_type     CHECK (link_type IN ('mitigating','compensating','related')),
    CONSTRAINT fk_30_lnk_risk_control_mappings_risk     FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id) ON DELETE CASCADE,
    CONSTRAINT fk_30_lnk_risk_control_mappings_control  FOREIGN KEY (control_id)
        REFERENCES "05_grc_library"."13_fct_controls" (id) ON DELETE CASCADE
);

-- Risk ↔ Vendors (many-to-many, cross-schema — FK deferred)
CREATE TABLE IF NOT EXISTS "14_risk_registry"."31_lnk_risk_vendor_mappings" (
    id         UUID         NOT NULL,
    risk_id    UUID         NOT NULL,
    vendor_id  UUID         NOT NULL,
    link_notes TEXT         NULL,
    created_at TIMESTAMP    NOT NULL,
    created_by UUID         NULL,
    CONSTRAINT pk_31_lnk_risk_vendor_mappings       PRIMARY KEY (id),
    CONSTRAINT uq_31_lnk_risk_vendor_mappings       UNIQUE (risk_id, vendor_id),
    CONSTRAINT fk_31_lnk_risk_vendor_mappings_risk  FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id) ON DELETE CASCADE
    -- fk to vendor table added when vendor schema exists
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLES (32-33) — Immutable events
-- ─────────────────────────────────────────────────────────────────────────────

-- 32_trx_risk_assessments — 5×5 scoring snapshots (inherent + residual over time)
CREATE TABLE IF NOT EXISTS "14_risk_registry"."32_trx_risk_assessments" (
    id               UUID         NOT NULL,
    risk_id          UUID         NOT NULL,
    assessment_type  VARCHAR(30)  NOT NULL DEFAULT 'inherent',
    likelihood_score INTEGER      NOT NULL,
    impact_score     INTEGER      NOT NULL,
    risk_score       INTEGER      GENERATED ALWAYS AS (likelihood_score * impact_score) STORED,
    assessed_by      UUID         NOT NULL,
    assessment_notes TEXT         NULL,
    assessed_at      TIMESTAMP    NOT NULL,
    CONSTRAINT pk_32_trx_risk_assessments            PRIMARY KEY (id),
    CONSTRAINT ck_32_trx_risk_assessments_type       CHECK (assessment_type IN ('inherent','residual')),
    CONSTRAINT ck_32_trx_risk_assessments_likelihood CHECK (likelihood_score BETWEEN 1 AND 5),
    CONSTRAINT ck_32_trx_risk_assessments_impact     CHECK (impact_score BETWEEN 1 AND 5),
    CONSTRAINT fk_32_trx_risk_assessments_risk       FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id)
);

-- 33_trx_risk_review_events — review lifecycle (status changes, comments)
CREATE TABLE IF NOT EXISTS "14_risk_registry"."33_trx_risk_review_events" (
    id          UUID         NOT NULL,
    risk_id     UUID         NOT NULL,
    event_type  VARCHAR(50)  NOT NULL,
    old_status  VARCHAR(50)  NULL,
    new_status  VARCHAR(50)  NULL,
    actor_id    UUID         NOT NULL,
    comment     TEXT         NULL,
    occurred_at TIMESTAMP    NOT NULL,
    CONSTRAINT pk_33_trx_risk_review_events       PRIMARY KEY (id),
    CONSTRAINT ck_33_trx_risk_review_events_type  CHECK (event_type IN ('status_changed','assessed','treatment_updated','control_linked','control_unlinked','comment_added','reviewed')),
    CONSTRAINT fk_33_trx_risk_review_events_risk  FOREIGN KEY (risk_id)
        REFERENCES "14_risk_registry"."10_fct_risks" (id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- VIEWS (40) — Reassemble risk + EAV for API consumption
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "14_risk_registry"."40_vw_risk_detail" AS
SELECT
    r.id,
    r.tenant_key,
    r.risk_code,
    r.org_id,
    r.workspace_id,
    r.risk_category_code,
    rc.name                         AS category_name,
    r.risk_level_code,
    rl.name                         AS risk_level_name,
    rl.color_hex                    AS risk_level_color,
    r.treatment_type_code,
    rt.name                         AS treatment_type_name,
    r.source_type,
    r.risk_status,
    r.is_active,
    r.is_deleted,
    r.created_at,
    r.updated_at,
    r.created_by,
    -- EAV properties flattened
    p_title.property_value          AS title,
    p_desc.property_value           AS description,
    p_notes.property_value          AS notes,
    p_owner.property_value          AS owner_user_id,
    p_impact.property_value         AS business_impact,
    -- Latest inherent score
    (SELECT ra.risk_score
     FROM "14_risk_registry"."32_trx_risk_assessments" ra
     WHERE ra.risk_id = r.id AND ra.assessment_type = 'inherent'
     ORDER BY ra.assessed_at DESC LIMIT 1)  AS inherent_risk_score,
    -- Latest residual score
    (SELECT ra.risk_score
     FROM "14_risk_registry"."32_trx_risk_assessments" ra
     WHERE ra.risk_id = r.id AND ra.assessment_type = 'residual'
     ORDER BY ra.assessed_at DESC LIMIT 1)  AS residual_risk_score,
    -- Linked control count
    (SELECT COUNT(*)
     FROM "14_risk_registry"."30_lnk_risk_control_mappings" m
     WHERE m.risk_id = r.id)        AS linked_control_count,
    -- Treatment plan status
    (SELECT tp.plan_status
     FROM "14_risk_registry"."11_fct_risk_treatment_plans" tp
     WHERE tp.risk_id = r.id AND tp.is_deleted = FALSE
     LIMIT 1)                       AS treatment_plan_status,
    -- Treatment plan target date
    (SELECT tp.target_date::text
     FROM "14_risk_registry"."11_fct_risk_treatment_plans" tp
     WHERE tp.risk_id = r.id AND tp.is_deleted = FALSE
     LIMIT 1)                       AS treatment_plan_target_date
FROM "14_risk_registry"."10_fct_risks" r
LEFT JOIN "14_risk_registry"."02_dim_risk_categories" rc
    ON rc.code = r.risk_category_code
LEFT JOIN "14_risk_registry"."04_dim_risk_levels" rl
    ON rl.code = r.risk_level_code
LEFT JOIN "14_risk_registry"."03_dim_risk_treatment_types" rt
    ON rt.code = r.treatment_type_code
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_title
    ON p_title.risk_id = r.id AND p_title.property_key = 'title'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_desc
    ON p_desc.risk_id = r.id AND p_desc.property_key = 'description'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_notes
    ON p_notes.risk_id = r.id AND p_notes.property_key = 'notes'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_owner
    ON p_owner.risk_id = r.id AND p_owner.property_key = 'owner_user_id'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_impact
    ON p_impact.risk_id = r.id AND p_impact.property_key = 'business_impact'
WHERE r.is_deleted = FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_10_fct_risks_tenant
    ON "14_risk_registry"."10_fct_risks" (tenant_key) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_risks_org
    ON "14_risk_registry"."10_fct_risks" (org_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_risks_workspace
    ON "14_risk_registry"."10_fct_risks" (workspace_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_risks_category
    ON "14_risk_registry"."10_fct_risks" (risk_category_code) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_risks_status
    ON "14_risk_registry"."10_fct_risks" (risk_status) WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_11_fct_treatment_plans_risk
    ON "14_risk_registry"."11_fct_risk_treatment_plans" (risk_id) WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_20_dtl_risk_props_key
    ON "14_risk_registry"."20_dtl_risk_properties" (risk_id, property_key);
CREATE INDEX IF NOT EXISTS idx_21_dtl_treatment_props_plan
    ON "14_risk_registry"."21_dtl_treatment_plan_properties" (treatment_plan_id, property_key);

CREATE INDEX IF NOT EXISTS idx_32_trx_risk_assessments_risk
    ON "14_risk_registry"."32_trx_risk_assessments" (risk_id, assessed_at DESC);
CREATE INDEX IF NOT EXISTS idx_33_trx_risk_review_events_risk
    ON "14_risk_registry"."33_trx_risk_review_events" (risk_id, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_30_lnk_risk_control_mappings_risk
    ON "14_risk_registry"."30_lnk_risk_control_mappings" (risk_id);
CREATE INDEX IF NOT EXISTS idx_30_lnk_risk_control_mappings_control
    ON "14_risk_registry"."30_lnk_risk_control_mappings" (control_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SEED DATA
-- ─────────────────────────────────────────────────────────────────────────────

-- Risk categories
INSERT INTO "14_risk_registry"."02_dim_risk_categories" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('a1b00001-0000-0000-0000-000000000000', 'operational',   'Operational',   'Risks from internal processes, people, systems', 1, TRUE, NOW(), NOW()),
    ('a1b00002-0000-0000-0000-000000000000', 'strategic',     'Strategic',     'Risks affecting strategic objectives',            2, TRUE, NOW(), NOW()),
    ('a1b00003-0000-0000-0000-000000000000', 'compliance',    'Compliance',    'Regulatory and legal compliance risks',           3, TRUE, NOW(), NOW()),
    ('a1b00004-0000-0000-0000-000000000000', 'financial',     'Financial',     'Financial loss or fraud risks',                   4, TRUE, NOW(), NOW()),
    ('a1b00005-0000-0000-0000-000000000000', 'reputational',  'Reputational',  'Brand and reputation damage risks',               5, TRUE, NOW(), NOW()),
    ('a1b00006-0000-0000-0000-000000000000', 'technology',    'Technology',    'IT infrastructure and cybersecurity risks',       6, TRUE, NOW(), NOW()),
    ('a1b00007-0000-0000-0000-000000000000', 'legal',         'Legal',         'Legal liability and contract risks',              7, TRUE, NOW(), NOW()),
    ('a1b00008-0000-0000-0000-000000000000', 'vendor',        'Vendor',        'Third-party and supply chain risks',              8, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Risk treatment types
INSERT INTO "14_risk_registry"."03_dim_risk_treatment_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('a2b00001-0000-0000-0000-000000000000', 'mitigate', 'Mitigate', 'Implement controls to reduce likelihood or impact', 1, TRUE, NOW(), NOW()),
    ('a2b00002-0000-0000-0000-000000000000', 'accept',   'Accept',   'Accept the risk within tolerance levels',          2, TRUE, NOW(), NOW()),
    ('a2b00003-0000-0000-0000-000000000000', 'transfer', 'Transfer', 'Transfer risk via insurance or contracts',          3, TRUE, NOW(), NOW()),
    ('a2b00004-0000-0000-0000-000000000000', 'avoid',    'Avoid',    'Eliminate the activity that creates the risk',      4, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Risk levels (5×5 matrix bands)
INSERT INTO "14_risk_registry"."04_dim_risk_levels" (id, code, name, description, score_min, score_max, color_hex, sort_order, is_active, created_at, updated_at)
VALUES
    ('a3b00001-0000-0000-0000-000000000000', 'critical', 'Critical', 'Score 16-25: immediate action required',    16, 25, '#ef4444', 1, TRUE, NOW(), NOW()),
    ('a3b00002-0000-0000-0000-000000000000', 'high',     'High',     'Score 11-15: urgent action within 30 days', 11, 15, '#f97316', 2, TRUE, NOW(), NOW()),
    ('a3b00003-0000-0000-0000-000000000000', 'medium',   'Medium',   'Score 6-10: action within 90 days',          6, 10, '#f59e0b', 3, TRUE, NOW(), NOW()),
    ('a3b00004-0000-0000-0000-000000000000', 'low',      'Low',      'Score 1-5: monitor and review quarterly',    1,  5, '#10b981', 4, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
