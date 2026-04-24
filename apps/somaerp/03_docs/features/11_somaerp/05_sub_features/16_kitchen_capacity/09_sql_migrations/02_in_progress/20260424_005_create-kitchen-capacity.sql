-- UP ====================================================================

-- Kitchen capacity vertical for somaerp (Plan 56-06) per ADR-003.
-- Creates: fct_kitchen_capacity (per kitchen × product_line × time_window ×
-- validity tuple) + v_kitchen_current_capacity + v_kitchen_capacity_history.
--
-- Cross-layer FKs:
--   kitchen_id       -> fct_kitchens(id)        (56-03)
--   product_line_id  -> fct_product_lines(id)   (56-04)
--   capacity_unit_id -> dim_units_of_measure(id) (56-05)
--
-- Overlap safety: partial unique index on
--   (tenant_id, kitchen_id, product_line_id, time_window_start, time_window_end)
-- WHERE valid_to IS NULL AND deleted_at IS NULL — one active row per
-- (kitchen, product_line, window). Historical rows may repeat.

-- ── fct_kitchen_capacity ───────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_kitchen_capacity (
    id                  VARCHAR(36) NOT NULL,
    tenant_id           VARCHAR(36) NOT NULL,
    kitchen_id          VARCHAR(36) NOT NULL,
    product_line_id     VARCHAR(36) NOT NULL,
    capacity_value      NUMERIC(12,2) NOT NULL,
    capacity_unit_id    SMALLINT NOT NULL,
    time_window_start   TIME NOT NULL,
    time_window_end     TIME NOT NULL,
    valid_from          DATE NOT NULL,
    valid_to            DATE,
    properties          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by          VARCHAR(36) NOT NULL,
    updated_by          VARCHAR(36) NOT NULL,
    deleted_at          TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_kitchen_capacity PRIMARY KEY (id),
    CONSTRAINT fk_kc_kitchen FOREIGN KEY (kitchen_id)
        REFERENCES "11_somaerp".fct_kitchens(id),
    CONSTRAINT fk_kc_product_line FOREIGN KEY (product_line_id)
        REFERENCES "11_somaerp".fct_product_lines(id),
    CONSTRAINT fk_kc_unit FOREIGN KEY (capacity_unit_id)
        REFERENCES "11_somaerp".dim_units_of_measure(id),
    CONSTRAINT chk_kc_window
        CHECK (time_window_end > time_window_start),
    CONSTRAINT chk_kc_validity
        CHECK (valid_to IS NULL OR valid_to > valid_from),
    CONSTRAINT chk_kc_value_positive
        CHECK (capacity_value > 0)
);
COMMENT ON TABLE  "11_somaerp".fct_kitchen_capacity IS 'Per-(kitchen × product_line × time_window × validity) capacity. See ADR-003 — capacity is replaced via close-old + insert-new, never in-place update.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.kitchen_id IS 'FK to fct_kitchens.id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.product_line_id IS 'FK to fct_product_lines.id (cross-layer).';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.capacity_value IS 'Units produced in the window (e.g. 50 bottles).';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.capacity_unit_id IS 'FK to dim_units_of_measure.id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.time_window_start IS 'Daily window start (e.g. 04:00:00).';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.time_window_end IS 'Daily window end (must be > start).';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.valid_from IS 'Date this capacity row becomes effective.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.valid_to IS 'NULL = currently active. Set by a PATCH to close the row.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.properties IS 'JSONB EAV side-channel (e.g. {"notes":"2-staff morning shift"}).';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_kitchen_capacity.deleted_at IS 'Soft-delete sentinel.';

-- Partial unique: only one ACTIVE row per (tenant, kitchen, product_line, window).
CREATE UNIQUE INDEX idx_kc_current
    ON "11_somaerp".fct_kitchen_capacity
    (tenant_id, kitchen_id, product_line_id, time_window_start, time_window_end)
    WHERE valid_to IS NULL AND deleted_at IS NULL;

-- Secondary range index — covers "active at date X" and historical lookups.
CREATE INDEX idx_kc_lookup
    ON "11_somaerp".fct_kitchen_capacity
    (tenant_id, kitchen_id, product_line_id, valid_from, valid_to);

-- ── v_kitchen_current_capacity ─────────────────────────────────────────
-- Active rows only (valid_to IS NULL AND deleted_at IS NULL).

CREATE VIEW "11_somaerp".v_kitchen_current_capacity AS
SELECT
    c.id,
    c.tenant_id,
    c.kitchen_id,
    k.name                AS kitchen_name,
    c.product_line_id,
    pl.name               AS product_line_name,
    c.capacity_value,
    c.capacity_unit_id,
    u.code                AS capacity_unit_code,
    u.name                AS capacity_unit_name,
    u.dimension           AS capacity_unit_dimension,
    c.time_window_start,
    c.time_window_end,
    c.valid_from,
    c.valid_to,
    c.properties,
    c.created_at,
    c.updated_at,
    c.created_by,
    c.updated_by,
    c.deleted_at
FROM "11_somaerp".fct_kitchen_capacity c
JOIN "11_somaerp".fct_kitchens k ON k.id = c.kitchen_id
JOIN "11_somaerp".fct_product_lines pl ON pl.id = c.product_line_id
JOIN "11_somaerp".dim_units_of_measure u ON u.id = c.capacity_unit_id
WHERE c.valid_to IS NULL AND c.deleted_at IS NULL;
COMMENT ON VIEW "11_somaerp".v_kitchen_current_capacity IS 'Active kitchen capacity rows only (valid_to IS NULL AND deleted_at IS NULL) joined with kitchen, product_line, and unit labels.';

-- ── v_kitchen_capacity_history ─────────────────────────────────────────
-- All rows including closed + soft-deleted (consumer filters).

CREATE VIEW "11_somaerp".v_kitchen_capacity_history AS
SELECT
    c.id,
    c.tenant_id,
    c.kitchen_id,
    k.name                AS kitchen_name,
    c.product_line_id,
    pl.name               AS product_line_name,
    c.capacity_value,
    c.capacity_unit_id,
    u.code                AS capacity_unit_code,
    u.name                AS capacity_unit_name,
    u.dimension           AS capacity_unit_dimension,
    c.time_window_start,
    c.time_window_end,
    c.valid_from,
    c.valid_to,
    c.properties,
    c.created_at,
    c.updated_at,
    c.created_by,
    c.updated_by,
    c.deleted_at
FROM "11_somaerp".fct_kitchen_capacity c
JOIN "11_somaerp".fct_kitchens k ON k.id = c.kitchen_id
JOIN "11_somaerp".fct_product_lines pl ON pl.id = c.product_line_id
JOIN "11_somaerp".dim_units_of_measure u ON u.id = c.capacity_unit_id;
COMMENT ON VIEW "11_somaerp".v_kitchen_capacity_history IS 'All kitchen capacity rows (active + closed + soft-deleted). Consumer filters by valid_to / deleted_at.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_kitchen_capacity_history;
DROP VIEW IF EXISTS "11_somaerp".v_kitchen_current_capacity;
DROP TABLE IF EXISTS "11_somaerp".fct_kitchen_capacity CASCADE;
