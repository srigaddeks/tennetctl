-- UP ====================================================================

-- Quality Control vertical for somaerp (Plan 56-08).
-- Creates: dim_qc_check_types + dim_qc_stages + dim_qc_outcomes +
--          dim_qc_checkpoints (tenant-scoped per-tenant catalog;
--          `dim` by role, UUID PK, carries tenant_id — documented deviation) +
--          evt_qc_checks (append-only).
-- Plus views: v_qc_checkpoints, v_qc_checks.
--
-- Rules:
-- * dim_qc_check_types + dim_qc_stages + dim_qc_outcomes are universal seeds
--   (SMALLINT PK). Same DB-wide for every tenant.
-- * dim_qc_checkpoints is `dim` by role (reusable definitions) but is
--   tenant-scoped, UUID v7 PK, and mutable. This mirrors the pattern used
--   in 03_docs/01_data_model/04_quality.md — the naming is deliberate but
--   deviates from the strict `dim_*` = SMALLINT lookup convention; see
--   COMMENT ON TABLE for details.
-- * evt_qc_checks is append-only per evt_* convention (no updated_at, no
--   deleted_at). Corrections are new rows.
-- * batch_id is stored as VARCHAR(36) without an FK constraint — fct_production_batches
--   doesn't exist yet. TODO(56-10): add FK once production batches ship.

-- ── dim_qc_check_types ─────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_qc_check_types (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_qc_check_types PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_qc_check_types_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_qc_check_types IS 'Universal QC check-type lookup (visual / smell / weight / temperature / taste / firmness / lot_verification / document_check). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_qc_check_types.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_qc_check_types.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_qc_check_types.name IS 'Human-readable name.';
COMMENT ON COLUMN "11_somaerp".dim_qc_check_types.deprecated_at IS 'Non-null when retired.';

-- ── dim_qc_stages ──────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_qc_stages (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_qc_stages PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_qc_stages_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_qc_stages IS 'Universal QC stage lookup (pre_production / in_production / post_production / fssai / receiving). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_qc_stages.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_qc_stages.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_qc_stages.name IS 'Human-readable name.';
COMMENT ON COLUMN "11_somaerp".dim_qc_stages.deprecated_at IS 'Non-null when retired.';

-- ── dim_qc_outcomes ────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_qc_outcomes (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    name            TEXT NOT NULL,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_qc_outcomes PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_qc_outcomes_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_qc_outcomes IS 'Universal QC outcome lookup (pass / fail / partial_pass / skipped). Tenant-shared seed.';
COMMENT ON COLUMN "11_somaerp".dim_qc_outcomes.id IS 'Permanent manual ID.';
COMMENT ON COLUMN "11_somaerp".dim_qc_outcomes.code IS 'Stable lowercase code.';
COMMENT ON COLUMN "11_somaerp".dim_qc_outcomes.name IS 'Human-readable name.';
COMMENT ON COLUMN "11_somaerp".dim_qc_outcomes.deprecated_at IS 'Non-null when retired.';

-- ── dim_qc_checkpoints (tenant-scoped catalog, UUID PK) ────────────────

CREATE TABLE "11_somaerp".dim_qc_checkpoints (
    id               VARCHAR(36) NOT NULL,
    tenant_id        VARCHAR(36) NOT NULL,
    stage_id         SMALLINT NOT NULL,
    check_type_id    SMALLINT NOT NULL,
    scope_kind       TEXT NOT NULL,
    scope_ref_id     VARCHAR(36),
    name             TEXT NOT NULL,
    criteria_jsonb   JSONB NOT NULL DEFAULT '{}'::jsonb,
    required         BOOLEAN NOT NULL DEFAULT TRUE,
    status           TEXT NOT NULL DEFAULT 'active',
    properties       JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by       VARCHAR(36) NOT NULL,
    updated_by       VARCHAR(36) NOT NULL,
    deleted_at       TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_qc_checkpoints PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dim_qc_checkpoints_stage FOREIGN KEY (stage_id)
        REFERENCES "11_somaerp".dim_qc_stages(id),
    CONSTRAINT fk_somaerp_dim_qc_checkpoints_check_type FOREIGN KEY (check_type_id)
        REFERENCES "11_somaerp".dim_qc_check_types(id),
    CONSTRAINT chk_somaerp_dim_qc_checkpoints_scope_kind
        CHECK (scope_kind IN ('recipe_step','raw_material','kitchen','product','universal')),
    CONSTRAINT chk_somaerp_dim_qc_checkpoints_status
        CHECK (status IN ('active','paused','archived')),
    CONSTRAINT chk_somaerp_dim_qc_checkpoints_scope_ref_nullability
        CHECK (
            (scope_kind = 'universal' AND scope_ref_id IS NULL)
            OR (scope_kind <> 'universal' AND scope_ref_id IS NOT NULL)
        )
);
COMMENT ON TABLE  "11_somaerp".dim_qc_checkpoints IS 'Tenant-scoped QC checkpoint catalog. Named `dim_*` for its role as a lookup of checkpoint definitions, but carries tenant_id + UUID v7 PK (deliberate deviation from strict dim_* = SMALLINT lookup convention; see 01_data_model/04_quality.md). scope_ref_id is polymorphic — no FK constraint at DB; service layer validates per scope_kind.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.stage_id IS 'FK to dim_qc_stages.id.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.check_type_id IS 'FK to dim_qc_check_types.id.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.scope_kind IS 'recipe_step | raw_material | kitchen | product | universal.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.scope_ref_id IS 'Polymorphic UUID FK — resolved by service layer per scope_kind. Nullable only when scope_kind=universal.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.criteria_jsonb IS 'Free-form acceptance criteria (e.g. {"min_temp_c":2,"max_temp_c":8}).';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.required IS 'When true a failure blocks the batch.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.status IS 'active | paused | archived.';
COMMENT ON COLUMN "11_somaerp".dim_qc_checkpoints.properties IS 'JSONB side-channel.';

CREATE INDEX idx_somaerp_dim_qc_checkpoints_tenant_stage
    ON "11_somaerp".dim_qc_checkpoints(tenant_id, stage_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dim_qc_checkpoints_tenant_scope
    ON "11_somaerp".dim_qc_checkpoints(tenant_id, scope_kind, scope_ref_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dim_qc_checkpoints_tenant_status
    ON "11_somaerp".dim_qc_checkpoints(tenant_id, status)
    WHERE deleted_at IS NULL;

-- ── evt_qc_checks (append-only) ────────────────────────────────────────

CREATE TABLE "11_somaerp".evt_qc_checks (
    id                    VARCHAR(36) NOT NULL,
    tenant_id             VARCHAR(36) NOT NULL,
    checkpoint_id         VARCHAR(36) NOT NULL,
    batch_id              VARCHAR(36),
    raw_material_lot      TEXT,
    kitchen_id            VARCHAR(36),
    outcome_id            SMALLINT NOT NULL,
    measured_value        NUMERIC(14,4),
    measured_unit_id      SMALLINT,
    notes                 TEXT,
    photo_vault_key       TEXT,
    performed_by_user_id  VARCHAR(36) NOT NULL,
    ts                    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT pk_somaerp_evt_qc_checks PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_evt_qc_checks_checkpoint FOREIGN KEY (checkpoint_id)
        REFERENCES "11_somaerp".dim_qc_checkpoints(id),
    CONSTRAINT fk_somaerp_evt_qc_checks_outcome FOREIGN KEY (outcome_id)
        REFERENCES "11_somaerp".dim_qc_outcomes(id),
    CONSTRAINT fk_somaerp_evt_qc_checks_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT fk_somaerp_evt_qc_checks_measured_unit FOREIGN KEY (measured_unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id)
);
COMMENT ON TABLE  "11_somaerp".evt_qc_checks IS 'Append-only QC event rows. One row per check performed. Immutable per evt_* convention (no updated_at, no deleted_at). Corrections = new rows. batch_id has no FK — fct_production_batches ships in 56-10 (TODO: add FK then).';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.checkpoint_id IS 'FK to dim_qc_checkpoints.id.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.batch_id IS 'Optional UUID ref to fct_production_batches.id (TODO 56-10: add FK).';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.raw_material_lot IS 'Optional lot number (FSSAI traceability).';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.kitchen_id IS 'Optional kitchen scope.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.outcome_id IS 'FK to dim_qc_outcomes.id.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.measured_value IS 'Numeric measurement (e.g. temperature, weight).';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.measured_unit_id IS 'FK to dim_units_of_measure.id.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.notes IS 'Free-text notes.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.photo_vault_key IS 'tennetctl vault key for attached photo.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.performed_by_user_id IS 'tennetctl user_id who performed the check.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.ts IS 'App-managed UTC timestamp of check performance.';
COMMENT ON COLUMN "11_somaerp".evt_qc_checks.metadata IS 'JSONB side-channel.';

CREATE INDEX idx_somaerp_evt_qc_checks_tenant_checkpoint_ts
    ON "11_somaerp".evt_qc_checks(tenant_id, checkpoint_id, ts DESC);
CREATE INDEX idx_somaerp_evt_qc_checks_tenant_batch_ts
    ON "11_somaerp".evt_qc_checks(tenant_id, batch_id, ts DESC);
CREATE INDEX idx_somaerp_evt_qc_checks_tenant_lot
    ON "11_somaerp".evt_qc_checks(tenant_id, raw_material_lot);
CREATE INDEX idx_somaerp_evt_qc_checks_tenant_user_ts
    ON "11_somaerp".evt_qc_checks(tenant_id, performed_by_user_id, ts DESC);

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_qc_checkpoints AS
SELECT
    cp.id,
    cp.tenant_id,
    cp.stage_id,
    s.code              AS stage_code,
    s.name              AS stage_name,
    cp.check_type_id,
    t.code              AS check_type_code,
    t.name              AS check_type_name,
    cp.scope_kind,
    cp.scope_ref_id,
    cp.name,
    cp.criteria_jsonb,
    cp.required,
    cp.status,
    cp.properties,
    cp.created_at,
    cp.updated_at,
    cp.created_by,
    cp.updated_by,
    cp.deleted_at
FROM "11_somaerp".dim_qc_checkpoints cp
LEFT JOIN "11_somaerp".dim_qc_stages s ON s.id = cp.stage_id
LEFT JOIN "11_somaerp".dim_qc_check_types t ON t.id = cp.check_type_id;
COMMENT ON VIEW "11_somaerp".v_qc_checkpoints IS 'dim_qc_checkpoints joined with dim_qc_stages + dim_qc_check_types for code + name labels.';

CREATE VIEW "11_somaerp".v_qc_checks AS
SELECT
    qc.id,
    qc.tenant_id,
    qc.checkpoint_id,
    cp.name             AS checkpoint_name,
    cp.scope_kind       AS checkpoint_scope_kind,
    cp.scope_ref_id     AS checkpoint_scope_ref_id,
    cp.stage_id         AS stage_id,
    s.code              AS stage_code,
    s.name              AS stage_name,
    cp.check_type_id    AS check_type_id,
    t.code              AS check_type_code,
    t.name              AS check_type_name,
    qc.batch_id,
    qc.raw_material_lot,
    qc.kitchen_id,
    k.name              AS kitchen_name,
    qc.outcome_id,
    o.code              AS outcome_code,
    o.name              AS outcome_name,
    qc.measured_value,
    qc.measured_unit_id,
    u.code              AS measured_unit_code,
    qc.notes,
    qc.photo_vault_key,
    qc.performed_by_user_id,
    qc.ts,
    qc.metadata
FROM "11_somaerp".evt_qc_checks qc
LEFT JOIN "11_somaerp".dim_qc_checkpoints cp ON cp.id = qc.checkpoint_id
LEFT JOIN "11_somaerp".dim_qc_stages s ON s.id = cp.stage_id
LEFT JOIN "11_somaerp".dim_qc_check_types t ON t.id = cp.check_type_id
LEFT JOIN "11_somaerp".dim_qc_outcomes o ON o.id = qc.outcome_id
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = qc.kitchen_id
LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = qc.measured_unit_id;
COMMENT ON VIEW "11_somaerp".v_qc_checks IS 'evt_qc_checks joined with checkpoint + stage + check_type + outcome + kitchen + unit labels.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_qc_checks;
DROP VIEW IF EXISTS "11_somaerp".v_qc_checkpoints;

DROP TABLE IF EXISTS "11_somaerp".evt_qc_checks;
DROP TABLE IF EXISTS "11_somaerp".dim_qc_checkpoints;
DROP TABLE IF EXISTS "11_somaerp".dim_qc_outcomes;
DROP TABLE IF EXISTS "11_somaerp".dim_qc_stages;
DROP TABLE IF EXISTS "11_somaerp".dim_qc_check_types;
