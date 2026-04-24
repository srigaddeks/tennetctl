-- UP ====================================================================

-- Production Batches vertical for somaerp (Plan 56-10).
-- Creates: fct_production_batches,
--          dtl_batch_step_logs,
--          dtl_batch_ingredient_consumption (with GENERATED line_cost_actual),
--          dtl_batch_qc_results
-- Plus views: v_production_batches, v_batch_consumption, v_batch_qc_results,
--             v_batch_summary (yield%/COGS/margin/duration)
--
-- Rules:
-- * fct_production_batches = soft-delete; state machine
--   planned -> in_progress -> completed | cancelled. recipe_id pinned.
-- * dtl_batch_step_logs    = soft-delete (dtl_* convention).
-- * dtl_batch_ingredient_consumption = soft-delete; line_cost_actual is
--   STORED generated (actual_qty * unit_cost_snapshot).
-- * dtl_batch_qc_results   = soft-delete summary rollup row per
--   (batch, checkpoint).
--
-- Completion side-effect (service layer, not DB):
--   on planned->completed: insert evt_inventory_movements rows
--   (movement_type='consumed') for each consumption line actual_qty > 0.

-- ── fct_production_batches ────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_production_batches (
    id                   VARCHAR(36) NOT NULL,
    tenant_id            VARCHAR(36) NOT NULL,
    kitchen_id           VARCHAR(36) NOT NULL,
    product_id           VARCHAR(36) NOT NULL,
    recipe_id            VARCHAR(36) NOT NULL,
    run_date             DATE NOT NULL,
    planned_qty          NUMERIC(12,2) NOT NULL,
    actual_qty           NUMERIC(12,2),
    status               TEXT NOT NULL DEFAULT 'planned',
    shift_start          TIMESTAMP,
    shift_end            TIMESTAMP,
    cancel_reason        TEXT,
    currency_code        CHAR(3) NOT NULL,
    lead_user_id         VARCHAR(36),
    notes                TEXT,
    properties           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           VARCHAR(36) NOT NULL,
    updated_by           VARCHAR(36) NOT NULL,
    deleted_at           TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_production_batches PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_production_batches_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT fk_somaerp_fct_production_batches_product FOREIGN KEY (product_id)
        REFERENCES "11_somaerp".fct_products(id),
    CONSTRAINT fk_somaerp_fct_production_batches_recipe FOREIGN KEY (recipe_id)
        REFERENCES "11_somaerp".fct_recipes(id),
    CONSTRAINT chk_somaerp_fct_production_batches_status
        CHECK (status IN ('planned','in_progress','completed','cancelled')),
    CONSTRAINT chk_somaerp_fct_production_batches_planned_qty_pos
        CHECK (planned_qty > 0),
    CONSTRAINT chk_somaerp_fct_production_batches_actual_qty_nonneg
        CHECK (actual_qty IS NULL OR actual_qty >= 0)
);
COMMENT ON TABLE  "11_somaerp".fct_production_batches IS 'Production batch header — one row per batch; state machine planned/in_progress/completed/cancelled. recipe_id pinned at creation per ADR-007 and never changes.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.kitchen_id IS 'FK to fct_kitchens.id — producing kitchen.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.product_id IS 'FK to fct_products.id — target SKU.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.recipe_id IS 'FK to fct_recipes.id — pinned at batch creation (ADR-007 immutable).';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.run_date IS 'Business date of the run.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.planned_qty IS 'Planned yield in bottles (positive).';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.actual_qty IS 'Actual yield — required on transition to completed.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.status IS 'planned | in_progress | completed | cancelled.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.shift_start IS 'Set when status->in_progress.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.shift_end IS 'Set when status->completed or cancelled after start.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.cancel_reason IS 'Reason when status=cancelled.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.currency_code IS 'ISO 4217 — copied from product.currency_code at create.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.lead_user_id IS 'Lead operator iam user_id (nullable).';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.notes IS 'Free-text notes.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_production_batches.deleted_at IS 'Soft-delete sentinel.';

-- One active batch per (kitchen, product, run_date, shift_start) window.
CREATE UNIQUE INDEX idx_somaerp_fct_production_batches_uniq_shift
    ON "11_somaerp".fct_production_batches(
        tenant_id, kitchen_id, product_id, run_date, COALESCE(shift_start, '1970-01-01'::timestamp)
    )
    WHERE deleted_at IS NULL AND status != 'cancelled';

CREATE INDEX idx_somaerp_fct_production_batches_tenant_kitchen_date
    ON "11_somaerp".fct_production_batches(tenant_id, kitchen_id, run_date DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_production_batches_tenant_status_date
    ON "11_somaerp".fct_production_batches(tenant_id, status, run_date DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_production_batches_tenant_product_date
    ON "11_somaerp".fct_production_batches(tenant_id, product_id, run_date DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_production_batches_tenant_recipe_date
    ON "11_somaerp".fct_production_batches(tenant_id, recipe_id, run_date DESC)
    WHERE deleted_at IS NULL;

-- ── dtl_batch_step_logs ───────────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_batch_step_logs (
    id                    VARCHAR(36) NOT NULL,
    tenant_id             VARCHAR(36) NOT NULL,
    batch_id              VARCHAR(36) NOT NULL,
    recipe_step_id        VARCHAR(36),
    step_number           INTEGER NOT NULL,
    name                  TEXT NOT NULL,
    started_at            TIMESTAMP,
    completed_at          TIMESTAMP,
    performed_by_user_id  VARCHAR(36),
    notes                 TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by            VARCHAR(36) NOT NULL,
    updated_by            VARCHAR(36) NOT NULL,
    deleted_at            TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_batch_step_logs PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_batch_step_logs_batch FOREIGN KEY (batch_id)
        REFERENCES "11_somaerp".fct_production_batches(id),
    CONSTRAINT fk_somaerp_dtl_batch_step_logs_recipe_step FOREIGN KEY (recipe_step_id)
        REFERENCES "11_somaerp".dtl_recipe_steps(id),
    CONSTRAINT chk_somaerp_dtl_batch_step_logs_step_number_pos
        CHECK (step_number > 0)
);
COMMENT ON TABLE  "11_somaerp".dtl_batch_step_logs IS 'Per-step execution log for a production batch. Auto-created from recipe steps at batch creation.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.batch_id IS 'FK to fct_production_batches.id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.recipe_step_id IS 'FK to dtl_recipe_steps.id — nullable in case of ad-hoc step.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.step_number IS '1-based step ordering.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.name IS 'Denormalized step name at batch creation.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.started_at IS 'Wall-clock start time (nullable until operator starts).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.completed_at IS 'Wall-clock completion time (nullable until operator completes).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.performed_by_user_id IS 'iam user_id who did the step (nullable).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_step_logs.notes IS 'Free-text notes.';

CREATE INDEX idx_somaerp_dtl_batch_step_logs_batch_step
    ON "11_somaerp".dtl_batch_step_logs(batch_id, step_number)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_batch_step_logs_tenant_batch
    ON "11_somaerp".dtl_batch_step_logs(tenant_id, batch_id)
    WHERE deleted_at IS NULL;

-- ── dtl_batch_ingredient_consumption ──────────────────────────────────

CREATE TABLE "11_somaerp".dtl_batch_ingredient_consumption (
    id                    VARCHAR(36) NOT NULL,
    tenant_id             VARCHAR(36) NOT NULL,
    batch_id              VARCHAR(36) NOT NULL,
    raw_material_id       VARCHAR(36) NOT NULL,
    recipe_ingredient_id  VARCHAR(36),
    planned_qty           NUMERIC(14,4) NOT NULL,
    actual_qty            NUMERIC(14,4),
    unit_id               SMALLINT NOT NULL,
    unit_cost_snapshot    NUMERIC(14,4) NOT NULL DEFAULT 0,
    currency_code         CHAR(3) NOT NULL,
    lot_number            TEXT,
    line_cost_actual      NUMERIC(16,4)
        GENERATED ALWAYS AS (actual_qty * unit_cost_snapshot) STORED,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by            VARCHAR(36) NOT NULL,
    updated_by            VARCHAR(36) NOT NULL,
    deleted_at            TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_batch_ingredient_consumption PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_batch_ingredient_consumption_batch FOREIGN KEY (batch_id)
        REFERENCES "11_somaerp".fct_production_batches(id),
    CONSTRAINT fk_somaerp_dtl_batch_ingredient_consumption_raw_material FOREIGN KEY (raw_material_id)
        REFERENCES "11_somaerp".fct_raw_materials(id),
    CONSTRAINT fk_somaerp_dtl_batch_ingredient_consumption_recipe_ingredient FOREIGN KEY (recipe_ingredient_id)
        REFERENCES "11_somaerp".dtl_recipe_ingredients(id),
    CONSTRAINT fk_somaerp_dtl_batch_ingredient_consumption_unit FOREIGN KEY (unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT chk_somaerp_dtl_batch_ingredient_consumption_planned_qty_pos
        CHECK (planned_qty >= 0),
    CONSTRAINT chk_somaerp_dtl_batch_ingredient_consumption_actual_qty_nonneg
        CHECK (actual_qty IS NULL OR actual_qty >= 0)
);
COMMENT ON TABLE  "11_somaerp".dtl_batch_ingredient_consumption IS 'Per-ingredient planned vs actual consumption for a batch. Rows auto-created at batch creation from recipe ingredients. line_cost_actual STORED GENERATED.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.batch_id IS 'FK to fct_production_batches.id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.raw_material_id IS 'FK to fct_raw_materials.id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.recipe_ingredient_id IS 'FK to dtl_recipe_ingredients.id — source recipe line.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.planned_qty IS 'Quantity computed from recipe (ingredient.quantity * planned_qty * conversion).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.actual_qty IS 'Actual consumed (nullable until operator logs).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.unit_id IS 'FK to dim_units_of_measure.id — raw_material default unit.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.unit_cost_snapshot IS 'Per-unit cost frozen at batch creation (from raw_material.target_unit_cost).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.lot_number IS 'Optional FSSAI lot number from received inventory.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_ingredient_consumption.line_cost_actual IS 'Generated: actual_qty * unit_cost_snapshot.';

CREATE INDEX idx_somaerp_dtl_batch_ingredient_consumption_batch
    ON "11_somaerp".dtl_batch_ingredient_consumption(batch_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_batch_ingredient_consumption_tenant_material
    ON "11_somaerp".dtl_batch_ingredient_consumption(tenant_id, raw_material_id)
    WHERE deleted_at IS NULL;

-- ── dtl_batch_qc_results ──────────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_batch_qc_results (
    id                    VARCHAR(36) NOT NULL,
    tenant_id             VARCHAR(36) NOT NULL,
    batch_id              VARCHAR(36) NOT NULL,
    checkpoint_id         VARCHAR(36) NOT NULL,
    outcome_id            SMALLINT NOT NULL,
    measured_value        NUMERIC(14,4),
    measured_unit_id      SMALLINT,
    notes                 TEXT,
    photo_vault_key       TEXT,
    performed_by_user_id  VARCHAR(36),
    last_event_id         VARCHAR(36),
    events_count          INTEGER NOT NULL DEFAULT 1,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by            VARCHAR(36) NOT NULL,
    updated_by            VARCHAR(36) NOT NULL,
    deleted_at            TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_batch_qc_results PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_batch_qc_results_batch FOREIGN KEY (batch_id)
        REFERENCES "11_somaerp".fct_production_batches(id),
    CONSTRAINT fk_somaerp_dtl_batch_qc_results_checkpoint FOREIGN KEY (checkpoint_id)
        REFERENCES "11_somaerp".dim_qc_checkpoints(id),
    CONSTRAINT fk_somaerp_dtl_batch_qc_results_outcome FOREIGN KEY (outcome_id)
        REFERENCES "11_somaerp".dim_qc_outcomes(id),
    CONSTRAINT fk_somaerp_dtl_batch_qc_results_event FOREIGN KEY (last_event_id)
        REFERENCES "11_somaerp".evt_qc_checks(id)
);
COMMENT ON TABLE  "11_somaerp".dtl_batch_qc_results IS 'Per-(batch, checkpoint) rollup of the latest QC event. Updated on each evt_qc_checks insert matching this batch+checkpoint.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.batch_id IS 'FK to fct_production_batches.id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.checkpoint_id IS 'FK to dim_qc_checkpoints.id.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.outcome_id IS 'FK to dim_qc_outcomes.id — latest outcome.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.measured_value IS 'Latest measured value (nullable).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.measured_unit_id IS 'FK to dim_units_of_measure.id (nullable).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.notes IS 'Latest notes.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.photo_vault_key IS 'tennetctl vault key of the latest photo (nullable).';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.performed_by_user_id IS 'Operator who performed the latest check.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.last_event_id IS 'FK to evt_qc_checks.id — the latest event.';
COMMENT ON COLUMN "11_somaerp".dtl_batch_qc_results.events_count IS 'Number of events rolled up into this row.';

CREATE UNIQUE INDEX idx_somaerp_dtl_batch_qc_results_batch_checkpoint
    ON "11_somaerp".dtl_batch_qc_results(tenant_id, batch_id, checkpoint_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_batch_qc_results_batch
    ON "11_somaerp".dtl_batch_qc_results(batch_id)
    WHERE deleted_at IS NULL;

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_production_batches AS
SELECT
    b.id,
    b.tenant_id,
    b.kitchen_id,
    k.name                AS kitchen_name,
    b.product_id,
    p.name                AS product_name,
    p.slug                AS product_slug,
    p.default_selling_price,
    b.recipe_id,
    r.version             AS recipe_version,
    r.status              AS recipe_status,
    b.run_date,
    b.planned_qty,
    b.actual_qty,
    b.status,
    b.shift_start,
    b.shift_end,
    b.cancel_reason,
    b.currency_code,
    b.lead_user_id,
    b.notes,
    b.properties,
    b.created_at,
    b.updated_at,
    b.created_by,
    b.updated_by,
    b.deleted_at
FROM "11_somaerp".fct_production_batches b
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = b.kitchen_id
LEFT JOIN "11_somaerp".fct_products p ON p.id = b.product_id
LEFT JOIN "11_somaerp".fct_recipes  r ON r.id = b.recipe_id;
COMMENT ON VIEW "11_somaerp".v_production_batches IS 'fct_production_batches joined with kitchen, product (w/ default_selling_price for margin), and recipe (w/ version).';

CREATE VIEW "11_somaerp".v_batch_step_logs AS
SELECT
    sl.id,
    sl.tenant_id,
    sl.batch_id,
    sl.recipe_step_id,
    sl.step_number,
    sl.name,
    sl.started_at,
    sl.completed_at,
    sl.performed_by_user_id,
    sl.notes,
    sl.created_at,
    sl.updated_at,
    sl.created_by,
    sl.updated_by,
    sl.deleted_at,
    CASE
        WHEN sl.started_at IS NOT NULL AND sl.completed_at IS NOT NULL
        THEN EXTRACT(EPOCH FROM (sl.completed_at - sl.started_at)) / 60.0
        ELSE NULL
    END                   AS duration_min
FROM "11_somaerp".dtl_batch_step_logs sl;
COMMENT ON VIEW "11_somaerp".v_batch_step_logs IS 'dtl_batch_step_logs with computed duration_min.';

CREATE VIEW "11_somaerp".v_batch_consumption AS
SELECT
    c.id,
    c.tenant_id,
    c.batch_id,
    c.raw_material_id,
    rm.name                 AS raw_material_name,
    rm.slug                 AS raw_material_slug,
    c.recipe_ingredient_id,
    c.planned_qty,
    c.actual_qty,
    c.unit_id,
    u.code                  AS unit_code,
    u.dimension             AS unit_dimension,
    c.unit_cost_snapshot,
    c.currency_code,
    c.lot_number,
    c.line_cost_actual,
    c.created_at,
    c.updated_at,
    c.created_by,
    c.updated_by,
    c.deleted_at
FROM "11_somaerp".dtl_batch_ingredient_consumption c
LEFT JOIN "11_somaerp".fct_raw_materials rm ON rm.id = c.raw_material_id
LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = c.unit_id;
COMMENT ON VIEW "11_somaerp".v_batch_consumption IS 'dtl_batch_ingredient_consumption joined with raw_material + unit.';

CREATE VIEW "11_somaerp".v_batch_qc_results AS
SELECT
    q.id,
    q.tenant_id,
    q.batch_id,
    q.checkpoint_id,
    cp.name                 AS checkpoint_name,
    cp.scope_kind           AS checkpoint_scope_kind,
    q.outcome_id,
    o.code                  AS outcome_code,
    o.name                  AS outcome_name,
    q.measured_value,
    q.measured_unit_id,
    mu.code                 AS measured_unit_code,
    q.notes,
    q.photo_vault_key,
    q.performed_by_user_id,
    q.last_event_id,
    q.events_count,
    q.created_at,
    q.updated_at,
    q.created_by,
    q.updated_by,
    q.deleted_at
FROM "11_somaerp".dtl_batch_qc_results q
LEFT JOIN "11_somaerp".dim_qc_checkpoints cp ON cp.id = q.checkpoint_id
LEFT JOIN "11_somaerp".dim_qc_outcomes o ON o.id = q.outcome_id
LEFT JOIN "11_somaerp".dim_units_of_measure mu ON mu.id = q.measured_unit_id;
COMMENT ON VIEW "11_somaerp".v_batch_qc_results IS 'dtl_batch_qc_results joined with checkpoint + outcome + measured_unit.';

CREATE VIEW "11_somaerp".v_batch_summary AS
WITH cons AS (
    SELECT
        c.batch_id,
        c.tenant_id,
        SUM(COALESCE(c.line_cost_actual, 0)) AS total_cogs,
        COUNT(*)                             AS ingredient_count,
        BOOL_OR(
            c.unit_id IS NULL OR c.unit_cost_snapshot IS NULL
        )                                    AS has_unconvertible_units
    FROM "11_somaerp".dtl_batch_ingredient_consumption c
    WHERE c.deleted_at IS NULL
    GROUP BY c.batch_id, c.tenant_id
),
steps AS (
    SELECT
        sl.batch_id,
        sl.tenant_id,
        COUNT(*)                                                      AS step_count_total,
        COUNT(*) FILTER (WHERE sl.completed_at IS NOT NULL)            AS step_count_completed
    FROM "11_somaerp".dtl_batch_step_logs sl
    WHERE sl.deleted_at IS NULL
    GROUP BY sl.batch_id, sl.tenant_id
)
SELECT
    b.id                                                  AS batch_id,
    b.tenant_id,
    b.kitchen_id,
    b.product_id,
    b.recipe_id,
    b.run_date,
    b.status,
    b.planned_qty,
    b.actual_qty,
    CASE
        WHEN b.planned_qty > 0 AND b.actual_qty IS NOT NULL
        THEN (b.actual_qty / b.planned_qty) * 100.0
        ELSE NULL
    END                                                   AS yield_pct,
    COALESCE(cons.total_cogs, 0)                          AS total_cogs,
    CASE
        WHEN b.actual_qty IS NOT NULL AND b.actual_qty > 0
        THEN COALESCE(cons.total_cogs, 0) / b.actual_qty
        ELSE NULL
    END                                                   AS cogs_per_unit,
    CASE
        WHEN b.actual_qty IS NOT NULL AND b.actual_qty > 0
         AND p.default_selling_price IS NOT NULL
         AND p.default_selling_price > 0
        THEN (
            (p.default_selling_price
             - (COALESCE(cons.total_cogs, 0) / b.actual_qty))
            / p.default_selling_price
        ) * 100.0
        ELSE NULL
    END                                                   AS gross_margin_pct,
    CASE
        WHEN b.shift_start IS NOT NULL AND b.shift_end IS NOT NULL
        THEN EXTRACT(EPOCH FROM (b.shift_end - b.shift_start)) / 60.0
        ELSE NULL
    END                                                   AS duration_min,
    COALESCE(cons.ingredient_count, 0)                    AS ingredient_count,
    COALESCE(cons.has_unconvertible_units, FALSE)         AS has_unconvertible_units,
    COALESCE(steps.step_count_total, 0)                   AS step_count_total,
    COALESCE(steps.step_count_completed, 0)               AS step_count_completed,
    b.currency_code,
    p.default_selling_price
FROM "11_somaerp".fct_production_batches b
LEFT JOIN "11_somaerp".fct_products p ON p.id = b.product_id
LEFT JOIN cons  ON cons.batch_id = b.id
LEFT JOIN steps ON steps.batch_id = b.id
WHERE b.deleted_at IS NULL;
COMMENT ON VIEW "11_somaerp".v_batch_summary IS 'Per-batch computed metrics: yield_pct, total_cogs, cogs_per_unit, gross_margin_pct (vs product.default_selling_price), duration_min, step + ingredient counts.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_batch_summary;
DROP VIEW IF EXISTS "11_somaerp".v_batch_qc_results;
DROP VIEW IF EXISTS "11_somaerp".v_batch_consumption;
DROP VIEW IF EXISTS "11_somaerp".v_batch_step_logs;
DROP VIEW IF EXISTS "11_somaerp".v_production_batches;

DROP TABLE IF EXISTS "11_somaerp".dtl_batch_qc_results;
DROP TABLE IF EXISTS "11_somaerp".dtl_batch_ingredient_consumption;
DROP TABLE IF EXISTS "11_somaerp".dtl_batch_step_logs;
DROP TABLE IF EXISTS "11_somaerp".fct_production_batches;
