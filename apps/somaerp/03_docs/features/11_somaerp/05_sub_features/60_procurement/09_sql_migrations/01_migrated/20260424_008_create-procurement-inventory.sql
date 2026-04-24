-- UP ====================================================================

-- Procurement + Inventory vertical for somaerp (Plan 56-09).
-- Creates: fct_procurement_runs, dtl_procurement_lines,
--          evt_inventory_movements (append-only)
-- Plus views: v_procurement_runs, v_inventory_movements, v_inventory_current
--
-- Rules:
-- * fct_procurement_runs = soft-delete, mutable total_cost/status/notes.
-- * dtl_procurement_lines = soft-delete, line_cost = quantity*unit_cost STORED.
-- * evt_inventory_movements = append-only (NO updated_at, NO deleted_at);
--   quantity > 0 always; movement_type semantics drive sign in v_inventory_current.
-- * batch_id_ref is VARCHAR(36) without FK — fct_production_batches ships in
--   56-10. TODO(56-10): add FK once production batches exist.
-- * v_inventory_current converts each movement to a base-unit qty using the
--   INGREDIENT's unit.to_base_factor then back to the raw_material default
--   unit. We keep two numbers: qty_in_base_unit and qty_in_default_unit.

-- ── fct_procurement_runs ──────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_procurement_runs (
    id                     VARCHAR(36) NOT NULL,
    tenant_id              VARCHAR(36) NOT NULL,
    kitchen_id             VARCHAR(36) NOT NULL,
    supplier_id            VARCHAR(36) NOT NULL,
    run_date               DATE NOT NULL,
    performed_by_user_id   VARCHAR(36) NOT NULL,
    total_cost             NUMERIC(14,4) NOT NULL DEFAULT 0,
    currency_code          CHAR(3) NOT NULL,
    notes                  TEXT,
    status                 TEXT NOT NULL DEFAULT 'active',
    properties             JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(36) NOT NULL,
    updated_by             VARCHAR(36) NOT NULL,
    deleted_at             TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_procurement_runs PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_procurement_runs_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT fk_somaerp_fct_procurement_runs_supplier FOREIGN KEY (supplier_id)
        REFERENCES "11_somaerp".fct_suppliers(id),
    CONSTRAINT chk_somaerp_fct_procurement_runs_status
        CHECK (status IN ('active','reconciled','cancelled'))
);
COMMENT ON TABLE  "11_somaerp".fct_procurement_runs IS 'Procurement run header — one shopping trip / wholesale order per row. total_cost is refreshed as lines are added.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.kitchen_id IS 'FK — receiving kitchen.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.supplier_id IS 'FK — vendor.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.run_date IS 'Business date of the run.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.performed_by_user_id IS 'tennetctl user who performed the run.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.total_cost IS 'Sum of line_cost across active lines — refreshed by service on line add/patch/delete.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.notes IS 'Free-text notes.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.status IS 'active | reconciled | cancelled.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_procurement_runs.deleted_at IS 'Soft-delete sentinel.';

CREATE INDEX idx_somaerp_fct_procurement_runs_tenant_kitchen_date
    ON "11_somaerp".fct_procurement_runs(tenant_id, kitchen_id, run_date DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_procurement_runs_tenant_supplier_date
    ON "11_somaerp".fct_procurement_runs(tenant_id, supplier_id, run_date DESC)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_procurement_runs_tenant_status_date
    ON "11_somaerp".fct_procurement_runs(tenant_id, status, run_date DESC)
    WHERE deleted_at IS NULL;

-- ── dtl_procurement_lines ─────────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_procurement_lines (
    id                     VARCHAR(36) NOT NULL,
    tenant_id              VARCHAR(36) NOT NULL,
    procurement_run_id     VARCHAR(36) NOT NULL,
    raw_material_id        VARCHAR(36) NOT NULL,
    quantity               NUMERIC(12,3) NOT NULL,
    unit_id                SMALLINT NOT NULL,
    unit_cost              NUMERIC(14,4) NOT NULL,
    line_cost              NUMERIC(16,4) GENERATED ALWAYS AS (quantity * unit_cost) STORED,
    lot_number             TEXT,
    quality_grade          SMALLINT,
    received_at            TIMESTAMP,
    created_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by             VARCHAR(36) NOT NULL,
    updated_by             VARCHAR(36) NOT NULL,
    deleted_at             TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_procurement_lines PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_procurement_lines_run FOREIGN KEY (procurement_run_id)
        REFERENCES "11_somaerp".fct_procurement_runs(id),
    CONSTRAINT fk_somaerp_dtl_procurement_lines_raw_material FOREIGN KEY (raw_material_id)
        REFERENCES "11_somaerp".fct_raw_materials(id),
    CONSTRAINT fk_somaerp_dtl_procurement_lines_unit FOREIGN KEY (unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT chk_somaerp_dtl_procurement_lines_quantity_pos
        CHECK (quantity > 0),
    CONSTRAINT chk_somaerp_dtl_procurement_lines_quality_grade
        CHECK (quality_grade IS NULL OR (quality_grade BETWEEN 1 AND 5))
);
COMMENT ON TABLE  "11_somaerp".dtl_procurement_lines IS 'Per-material line item on a procurement run. line_cost is STORED generated column.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.procurement_run_id IS 'FK to fct_procurement_runs.id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.raw_material_id IS 'FK to fct_raw_materials.id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.quantity IS 'Positive quantity in unit_id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.unit_id IS 'FK to dim_units_of_measure.id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.unit_cost IS 'Per-unit cost at purchase.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.line_cost IS 'Generated column: quantity * unit_cost.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.lot_number IS 'Optional lot number (FSSAI).';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.quality_grade IS 'Optional 1..5 grade.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.received_at IS 'Timestamp received at kitchen.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".dtl_procurement_lines.deleted_at IS 'Soft-delete sentinel.';

CREATE INDEX idx_somaerp_dtl_procurement_lines_run
    ON "11_somaerp".dtl_procurement_lines(procurement_run_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_dtl_procurement_lines_tenant_material
    ON "11_somaerp".dtl_procurement_lines(tenant_id, raw_material_id)
    WHERE deleted_at IS NULL;

-- ── evt_inventory_movements (append-only) ─────────────────────────────

CREATE TABLE "11_somaerp".evt_inventory_movements (
    id                     VARCHAR(36) NOT NULL,
    tenant_id              VARCHAR(36) NOT NULL,
    kitchen_id             VARCHAR(36) NOT NULL,
    raw_material_id        VARCHAR(36) NOT NULL,
    movement_type          TEXT NOT NULL,
    quantity               NUMERIC(12,3) NOT NULL,
    unit_id                SMALLINT NOT NULL,
    lot_number             TEXT,
    batch_id_ref           VARCHAR(36),
    procurement_run_id     VARCHAR(36),
    reason                 TEXT,
    ts                     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    performed_by_user_id   VARCHAR(36) NOT NULL,
    metadata               JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT pk_somaerp_evt_inventory_movements PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_evt_inventory_movements_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT fk_somaerp_evt_inventory_movements_raw_material FOREIGN KEY (raw_material_id)
        REFERENCES "11_somaerp".fct_raw_materials(id),
    CONSTRAINT fk_somaerp_evt_inventory_movements_unit FOREIGN KEY (unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT fk_somaerp_evt_inventory_movements_run FOREIGN KEY (procurement_run_id)
        REFERENCES "11_somaerp".fct_procurement_runs(id),
    CONSTRAINT chk_somaerp_evt_inventory_movements_type
        CHECK (movement_type IN ('received','consumed','wasted','adjusted','expired')),
    CONSTRAINT chk_somaerp_evt_inventory_movements_quantity_pos
        CHECK (quantity > 0)
);
COMMENT ON TABLE  "11_somaerp".evt_inventory_movements IS 'Append-only inventory event log. One row per physical inventory change. No updated_at, no deleted_at. Quantity is always positive; movement_type drives add/subtract sign in v_inventory_current. batch_id_ref has no FK — fct_production_batches ships in 56-10 (TODO: add FK then).';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.kitchen_id IS 'FK to fct_kitchens.id — inventory holder.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.raw_material_id IS 'FK to fct_raw_materials.id.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.movement_type IS 'received | consumed | wasted | adjusted | expired.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.quantity IS 'Always positive; sign interpreted by movement_type.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.unit_id IS 'FK to dim_units_of_measure.id.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.lot_number IS 'Optional lot number (FSSAI).';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.batch_id_ref IS 'Optional ref to fct_production_batches.id — TODO(56-10) add FK.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.procurement_run_id IS 'Optional FK to fct_procurement_runs.id — set for received rows originating from a run.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.reason IS 'Required by service when type is wasted/adjusted/expired.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.ts IS 'App-managed UTC event timestamp.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.performed_by_user_id IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".evt_inventory_movements.metadata IS 'JSONB side-channel.';

CREATE INDEX idx_somaerp_evt_inventory_movements_tenant_k_rm_ts
    ON "11_somaerp".evt_inventory_movements(tenant_id, kitchen_id, raw_material_id, ts DESC);
CREATE INDEX idx_somaerp_evt_inventory_movements_tenant_type_ts
    ON "11_somaerp".evt_inventory_movements(tenant_id, movement_type, ts DESC);
CREATE INDEX idx_somaerp_evt_inventory_movements_tenant_run
    ON "11_somaerp".evt_inventory_movements(tenant_id, procurement_run_id)
    WHERE procurement_run_id IS NOT NULL;

-- ── Views ──────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_procurement_runs AS
SELECT
    pr.id,
    pr.tenant_id,
    pr.kitchen_id,
    k.name              AS kitchen_name,
    pr.supplier_id,
    s.name              AS supplier_name,
    s.slug              AS supplier_slug,
    pr.run_date,
    pr.performed_by_user_id,
    pr.total_cost,
    COALESCE(
        (SELECT SUM(l.line_cost)
           FROM "11_somaerp".dtl_procurement_lines l
          WHERE l.procurement_run_id = pr.id
            AND l.tenant_id = pr.tenant_id
            AND l.deleted_at IS NULL),
        0
    )                   AS computed_total,
    (SELECT COUNT(*)
       FROM "11_somaerp".dtl_procurement_lines l
      WHERE l.procurement_run_id = pr.id
        AND l.tenant_id = pr.tenant_id
        AND l.deleted_at IS NULL
    )                   AS line_count,
    pr.currency_code,
    pr.notes,
    pr.status,
    pr.properties,
    pr.created_at,
    pr.updated_at,
    pr.created_by,
    pr.updated_by,
    pr.deleted_at
FROM "11_somaerp".fct_procurement_runs pr
LEFT JOIN "11_somaerp".fct_kitchens k  ON k.id = pr.kitchen_id
LEFT JOIN "11_somaerp".fct_suppliers s ON s.id = pr.supplier_id;
COMMENT ON VIEW "11_somaerp".v_procurement_runs IS 'fct_procurement_runs joined with kitchen + supplier and augmented with line_count + computed_total (sum of active line_costs).';

CREATE VIEW "11_somaerp".v_inventory_movements AS
SELECT
    m.id,
    m.tenant_id,
    m.kitchen_id,
    k.name              AS kitchen_name,
    m.raw_material_id,
    rm.name             AS raw_material_name,
    rm.slug             AS raw_material_slug,
    rm.category_id      AS raw_material_category_id,
    cat.code            AS raw_material_category_code,
    cat.name            AS raw_material_category_name,
    m.movement_type,
    m.quantity,
    m.unit_id,
    u.code              AS unit_code,
    u.dimension         AS unit_dimension,
    m.lot_number,
    m.batch_id_ref,
    m.procurement_run_id,
    m.reason,
    m.ts,
    m.performed_by_user_id,
    m.metadata
FROM "11_somaerp".evt_inventory_movements m
LEFT JOIN "11_somaerp".fct_kitchens k  ON k.id = m.kitchen_id
LEFT JOIN "11_somaerp".fct_raw_materials rm ON rm.id = m.raw_material_id
LEFT JOIN "11_somaerp".dim_raw_material_categories cat ON cat.id = rm.category_id
LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = m.unit_id;
COMMENT ON VIEW "11_somaerp".v_inventory_movements IS 'evt_inventory_movements joined with kitchen + raw material + category + unit labels.';

CREATE VIEW "11_somaerp".v_inventory_current AS
SELECT
    agg.tenant_id,
    agg.kitchen_id,
    k.name              AS kitchen_name,
    agg.raw_material_id,
    rm.name             AS raw_material_name,
    rm.slug             AS raw_material_slug,
    rm.category_id      AS category_id,
    cat.code            AS category_code,
    cat.name            AS category_name,
    rm.default_unit_id,
    u.code              AS default_unit_code,
    u.dimension         AS default_unit_dimension,
    rm.target_unit_cost,
    rm.currency_code,
    agg.qty_in_base_unit,
    CASE WHEN u.to_base_factor IS NOT NULL AND u.to_base_factor > 0
         THEN agg.qty_in_base_unit / u.to_base_factor
         ELSE NULL
    END                 AS qty_in_default_unit
FROM (
    SELECT
        m.tenant_id,
        m.kitchen_id,
        m.raw_material_id,
        SUM(
            CASE
                WHEN m.movement_type IN ('received','adjusted')
                    THEN m.quantity * mu.to_base_factor
                ELSE -(m.quantity * mu.to_base_factor)
            END
        )               AS qty_in_base_unit
    FROM "11_somaerp".evt_inventory_movements m
    JOIN "11_somaerp".dim_units_of_measure mu ON mu.id = m.unit_id
    GROUP BY m.tenant_id, m.kitchen_id, m.raw_material_id
) agg
JOIN "11_somaerp".fct_raw_materials rm
      ON rm.id = agg.raw_material_id AND rm.tenant_id = agg.tenant_id
LEFT JOIN "11_somaerp".fct_kitchens k
      ON k.id = agg.kitchen_id AND k.tenant_id = agg.tenant_id
LEFT JOIN "11_somaerp".dim_raw_material_categories cat ON cat.id = rm.category_id
LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = rm.default_unit_id;
COMMENT ON VIEW "11_somaerp".v_inventory_current IS 'Per-(tenant, kitchen, raw_material) current inventory, converted to base unit + rolled up to raw_material default unit. received/adjusted add, consumed/wasted/expired subtract.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_inventory_current;
DROP VIEW IF EXISTS "11_somaerp".v_inventory_movements;
DROP VIEW IF EXISTS "11_somaerp".v_procurement_runs;

DROP TABLE IF EXISTS "11_somaerp".evt_inventory_movements;
DROP TABLE IF EXISTS "11_somaerp".dtl_procurement_lines;
DROP TABLE IF EXISTS "11_somaerp".fct_procurement_runs;
