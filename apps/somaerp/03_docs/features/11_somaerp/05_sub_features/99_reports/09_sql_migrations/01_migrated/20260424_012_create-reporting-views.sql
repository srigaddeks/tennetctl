-- UP ====================================================================

-- Reporting Views for somaerp (Plan 56-13) — FINAL plan of Phase 56.
--
-- HARD RULE: VIEWS ONLY. No new tables, no new dims, no seeds.
-- Every view is a read-only rollup over existing fct_/dtl_/evt_ data.
--
-- Views created:
--   * v_dashboard_today             — per-tenant KPI snapshot for a date.
--   * v_batch_yield_daily           — daily SUM/AVG of batch yield per (kitchen, product).
--   * v_batch_cogs_daily            — daily SUM/AVG of batch COGS per (kitchen, product).
--   * v_inventory_reorder_alerts    — per-(kitchen, raw_material) alert level.
--   * v_procurement_spend_monthly   — monthly SUM of procurement spend per (kitchen, supplier).
--   * v_subscription_revenue_projected — per-subscription MRR projection.
--   * v_fssai_compliance_batches    — per-batch compliance dossier for CSV export.

-- ── v_dashboard_today ────────────────────────────────────────────────────
--
-- One row per (tenant_id, as_of_date). Aggregates today's batch/delivery/
-- subscription activity via scalar sub-selects so the shape stays flat.
--
-- NOTE: we materialize the "as_of_date" via CROSS JOIN with CURRENT_DATE so
-- this view always returns "today". To look up a different day, callers
-- should filter a date-partitioned *_daily view or a reporting endpoint
-- that accepts ?date= (endpoint issues a parameterized query bypassing this
-- view for historical rollups — see repository.select_dashboard_today).

CREATE VIEW "11_somaerp".v_dashboard_today AS
WITH tenants AS (
    SELECT DISTINCT tenant_id
    FROM "11_somaerp".fct_kitchens
    WHERE deleted_at IS NULL
),
d AS (
    SELECT CURRENT_DATE AS as_of_date
)
SELECT
    t.tenant_id,
    d.as_of_date                                                            AS date,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".fct_production_batches b
        WHERE b.tenant_id = t.tenant_id
          AND b.run_date = d.as_of_date
          AND b.status IN ('planned','in_progress')
          AND b.deleted_at IS NULL
    ), 0)                                                                   AS active_batches,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".fct_production_batches b
        WHERE b.tenant_id = t.tenant_id
          AND b.run_date = d.as_of_date
          AND b.status = 'completed'
          AND b.deleted_at IS NULL
    ), 0)                                                                   AS completed_batches,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".fct_delivery_runs r
        WHERE r.tenant_id = t.tenant_id
          AND r.run_date = d.as_of_date
          AND r.status = 'in_transit'
          AND r.deleted_at IS NULL
    ), 0)                                                                   AS in_transit_runs,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".fct_delivery_runs r
        WHERE r.tenant_id = t.tenant_id
          AND r.run_date = d.as_of_date
          AND r.status = 'completed'
          AND r.deleted_at IS NULL
    ), 0)                                                                   AS completed_runs,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".dtl_delivery_stops s
        JOIN "11_somaerp".fct_delivery_runs r
          ON r.id = s.delivery_run_id AND r.tenant_id = s.tenant_id
        WHERE s.tenant_id = t.tenant_id
          AND r.run_date = d.as_of_date
          AND s.deleted_at IS NULL
          AND r.deleted_at IS NULL
    ), 0)                                                                   AS scheduled_deliveries,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".dtl_delivery_stops s
        JOIN "11_somaerp".fct_delivery_runs r
          ON r.id = s.delivery_run_id AND r.tenant_id = s.tenant_id
        WHERE s.tenant_id = t.tenant_id
          AND r.run_date = d.as_of_date
          AND s.status = 'delivered'
          AND s.deleted_at IS NULL
          AND r.deleted_at IS NULL
    ), 0)                                                                   AS completed_deliveries,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".fct_subscriptions s
        WHERE s.tenant_id = t.tenant_id
          AND s.status = 'active'
          AND s.deleted_at IS NULL
    ), 0)                                                                   AS active_subscriptions
FROM tenants t
CROSS JOIN d;
COMMENT ON VIEW "11_somaerp".v_dashboard_today IS 'Per-tenant KPI snapshot for CURRENT_DATE. Cross-layer rollup over batches, delivery runs, delivery stops, and subscriptions. Historical lookups use the repository helper that runs the same shape with a parameterized date.';

-- ── v_batch_yield_daily ─────────────────────────────────────────────────
--
-- One row per (tenant_id, kitchen_id, product_id, run_date) for completed
-- batches only. Used for trend charts.

CREATE VIEW "11_somaerp".v_batch_yield_daily AS
SELECT
    b.tenant_id,
    b.kitchen_id,
    k.name                                                                  AS kitchen_name,
    b.product_id,
    p.name                                                                  AS product_name,
    b.run_date,
    SUM(b.planned_qty)                                                       AS planned_qty,
    SUM(COALESCE(b.actual_qty, 0))                                           AS actual_qty,
    AVG(
        CASE
            WHEN b.planned_qty > 0 AND b.actual_qty IS NOT NULL
            THEN (b.actual_qty / b.planned_qty) * 100.0
            ELSE NULL
        END
    )                                                                        AS yield_pct,
    COUNT(*)::INT                                                            AS batch_count
FROM "11_somaerp".fct_production_batches b
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = b.kitchen_id
LEFT JOIN "11_somaerp".fct_products p ON p.id = b.product_id
WHERE b.status = 'completed'
  AND b.deleted_at IS NULL
GROUP BY b.tenant_id, b.kitchen_id, k.name, b.product_id, p.name, b.run_date;
COMMENT ON VIEW "11_somaerp".v_batch_yield_daily IS 'Completed-batch yield per (tenant, kitchen, product, run_date): SUM planned + actual, AVG yield_pct, COUNT batches.';

-- ── v_batch_cogs_daily ──────────────────────────────────────────────────
--
-- Joins v_batch_summary with fct_production_batches to roll up total_cogs
-- and cogs_per_unit per day.

CREATE VIEW "11_somaerp".v_batch_cogs_daily AS
SELECT
    b.tenant_id,
    b.kitchen_id,
    k.name                                                                  AS kitchen_name,
    b.product_id,
    p.name                                                                  AS product_name,
    b.run_date,
    SUM(COALESCE(bs.total_cogs, 0))                                          AS total_cogs,
    AVG(bs.cogs_per_unit)                                                    AS cogs_per_unit,
    COUNT(*)::INT                                                            AS batch_count,
    MAX(b.currency_code)                                                     AS currency_code
FROM "11_somaerp".fct_production_batches b
LEFT JOIN "11_somaerp".v_batch_summary bs ON bs.batch_id = b.id
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = b.kitchen_id
LEFT JOIN "11_somaerp".fct_products p ON p.id = b.product_id
WHERE b.status = 'completed'
  AND b.deleted_at IS NULL
GROUP BY b.tenant_id, b.kitchen_id, k.name, b.product_id, p.name, b.run_date;
COMMENT ON VIEW "11_somaerp".v_batch_cogs_daily IS 'Completed-batch COGS per (tenant, kitchen, product, run_date) from v_batch_summary.';

-- ── v_inventory_reorder_alerts ──────────────────────────────────────────
--
-- One row per (tenant, kitchen, raw_material) with current_qty vs
-- raw_material.properties->>''reorder_point_qty''. is_numeric guard via
-- CASE + explicit regex on the JSONB text to avoid cast errors.

CREATE VIEW "11_somaerp".v_inventory_reorder_alerts AS
WITH rp AS (
    SELECT
        rm.id                                                               AS raw_material_id,
        rm.name                                                             AS raw_material_name,
        rm.category_id,
        CASE
            WHEN rm.properties ? 'reorder_point_qty'
             AND (rm.properties->>'reorder_point_qty') ~ '^-?[0-9]+(\\.[0-9]+)?$'
            THEN (rm.properties->>'reorder_point_qty')::NUMERIC
            ELSE NULL
        END                                                                 AS reorder_point_qty
    FROM "11_somaerp".fct_raw_materials rm
    WHERE rm.deleted_at IS NULL
),
primary_supplier AS (
    SELECT
        lnk.tenant_id,
        lnk.raw_material_id,
        lnk.supplier_id,
        s.name                                                              AS supplier_name
    FROM "11_somaerp".lnk_raw_material_suppliers lnk
    LEFT JOIN "11_somaerp".fct_suppliers s ON s.id = lnk.supplier_id
    WHERE lnk.is_primary = TRUE
),
base AS (
    -- Every (kitchen, raw_material) in the tenant, whether or not stock exists
    SELECT
        k.tenant_id,
        k.id                                                                AS kitchen_id,
        k.name                                                              AS kitchen_name,
        rm.id                                                               AS raw_material_id,
        rm.name                                                             AS raw_material_name,
        rm.default_unit_id                                                  AS default_unit_id,
        u.code                                                              AS unit_code,
        rm.category_id                                                      AS category_id,
        cat.name                                                            AS category_name
    FROM "11_somaerp".fct_kitchens k
    JOIN "11_somaerp".fct_raw_materials rm
      ON rm.tenant_id = k.tenant_id AND rm.deleted_at IS NULL
    LEFT JOIN "11_somaerp".dim_units_of_measure u ON u.id = rm.default_unit_id
    LEFT JOIN "11_somaerp".dim_raw_material_categories cat ON cat.id = rm.category_id
    WHERE k.deleted_at IS NULL
)
SELECT
    b.tenant_id,
    b.kitchen_id,
    b.kitchen_name,
    b.raw_material_id,
    b.raw_material_name,
    b.category_id,
    b.category_name,
    COALESCE(inv.qty_in_default_unit, 0)                                    AS current_qty,
    b.unit_code,
    rp.reorder_point_qty,
    CASE
        WHEN COALESCE(inv.qty_in_default_unit, 0) <= 0 THEN 'critical'
        WHEN rp.reorder_point_qty IS NOT NULL
         AND COALESCE(inv.qty_in_default_unit, 0) < rp.reorder_point_qty THEN 'low'
        ELSE 'ok'
    END                                                                     AS alert_level,
    ps.supplier_id                                                          AS primary_supplier_id,
    ps.supplier_name                                                        AS primary_supplier_name
FROM base b
LEFT JOIN "11_somaerp".v_inventory_current inv
  ON inv.tenant_id = b.tenant_id
 AND inv.kitchen_id = b.kitchen_id
 AND inv.raw_material_id = b.raw_material_id
LEFT JOIN rp
  ON rp.raw_material_id = b.raw_material_id
LEFT JOIN primary_supplier ps
  ON ps.tenant_id = b.tenant_id AND ps.raw_material_id = b.raw_material_id;
COMMENT ON VIEW "11_somaerp".v_inventory_reorder_alerts IS 'Per-(tenant, kitchen, raw_material) current qty + reorder_point_qty (from raw_material.properties JSONB) + alert_level (critical|low|ok) + primary supplier. Null-safe numeric cast.';

-- ── v_procurement_spend_monthly ─────────────────────────────────────────

CREATE VIEW "11_somaerp".v_procurement_spend_monthly AS
SELECT
    pr.tenant_id,
    TO_CHAR(pr.run_date, 'YYYY-MM')                                          AS year_month,
    pr.kitchen_id,
    k.name                                                                  AS kitchen_name,
    pr.supplier_id,
    s.name                                                                  AS supplier_name,
    SUM(pr.total_cost)                                                       AS total_spend,
    MAX(pr.currency_code)                                                    AS currency_code,
    COUNT(*)::INT                                                            AS run_count,
    COALESCE(SUM(lc.cnt), 0)::INT                                            AS line_count
FROM "11_somaerp".fct_procurement_runs pr
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = pr.kitchen_id
LEFT JOIN "11_somaerp".fct_suppliers s ON s.id = pr.supplier_id
LEFT JOIN LATERAL (
    SELECT COUNT(*) AS cnt
    FROM "11_somaerp".dtl_procurement_lines l
    WHERE l.procurement_run_id = pr.id
      AND l.tenant_id = pr.tenant_id
      AND l.deleted_at IS NULL
) lc ON TRUE
WHERE pr.deleted_at IS NULL
  AND pr.status != 'cancelled'
GROUP BY pr.tenant_id, TO_CHAR(pr.run_date, 'YYYY-MM'),
         pr.kitchen_id, k.name, pr.supplier_id, s.name;
COMMENT ON VIEW "11_somaerp".v_procurement_spend_monthly IS 'Monthly procurement spend per (tenant, year_month, kitchen, supplier): SUM total_cost, COUNT runs, COUNT lines. Cancelled runs excluded.';

-- ── v_subscription_revenue_projected ────────────────────────────────────
--
-- Projected monthly revenue per active subscription:
--   monthly_projected = price_per_delivery * deliveries_per_week * 4.333

CREATE VIEW "11_somaerp".v_subscription_revenue_projected AS
SELECT
    s.id                                                                     AS subscription_id,
    s.tenant_id,
    s.customer_id,
    c.name                                                                   AS customer_name,
    s.plan_id,
    p.name                                                                   AS plan_name,
    f.code                                                                   AS frequency_code,
    f.deliveries_per_week                                                    AS deliveries_per_week,
    p.price_per_delivery                                                     AS price_per_delivery,
    CASE
        WHEN p.price_per_delivery IS NULL OR f.deliveries_per_week IS NULL THEN NULL
        ELSE p.price_per_delivery * f.deliveries_per_week
    END                                                                      AS weekly_projected,
    CASE
        WHEN p.price_per_delivery IS NULL OR f.deliveries_per_week IS NULL THEN NULL
        ELSE p.price_per_delivery * f.deliveries_per_week / 7.0
    END                                                                      AS daily_projected,
    CASE
        WHEN p.price_per_delivery IS NULL OR f.deliveries_per_week IS NULL THEN NULL
        ELSE p.price_per_delivery * f.deliveries_per_week * 4.333
    END                                                                      AS monthly_projected,
    p.currency_code                                                          AS currency_code,
    s.status,
    s.start_date,
    s.end_date
FROM "11_somaerp".fct_subscriptions s
LEFT JOIN "11_somaerp".fct_customers c           ON c.id = s.customer_id
LEFT JOIN "11_somaerp".fct_subscription_plans p  ON p.id = s.plan_id
LEFT JOIN "11_somaerp".dim_subscription_frequencies f ON f.id = p.frequency_id
WHERE s.deleted_at IS NULL;
COMMENT ON VIEW "11_somaerp".v_subscription_revenue_projected IS 'Per-subscription projected revenue (daily/weekly/monthly). monthly = price_per_delivery * deliveries_per_week * 4.333.';

-- ── v_fssai_compliance_batches ──────────────────────────────────────────
--
-- One row per completed or in-progress batch with lot_numbers (array) and
-- qc_results (jsonb array) pre-aggregated for CSV export.

CREATE VIEW "11_somaerp".v_fssai_compliance_batches AS
SELECT
    b.id                                                                     AS batch_id,
    b.tenant_id,
    b.run_date,
    p.name                                                                   AS product_name,
    r.version                                                                AS recipe_version,
    k.name                                                                   AS kitchen_name,
    b.planned_qty,
    b.actual_qty,
    b.status,
    b.lead_user_id                                                           AS completed_by,
    COALESCE(cons.lot_numbers, ARRAY[]::TEXT[])                              AS lot_numbers,
    COALESCE(qc.qc_results, '[]'::jsonb)                                     AS qc_results
FROM "11_somaerp".fct_production_batches b
LEFT JOIN "11_somaerp".fct_kitchens k ON k.id = b.kitchen_id
LEFT JOIN "11_somaerp".fct_products p ON p.id = b.product_id
LEFT JOIN "11_somaerp".fct_recipes  r ON r.id = b.recipe_id
LEFT JOIN LATERAL (
    SELECT ARRAY_AGG(DISTINCT c.lot_number) FILTER (WHERE c.lot_number IS NOT NULL) AS lot_numbers
    FROM "11_somaerp".dtl_batch_ingredient_consumption c
    WHERE c.batch_id = b.id
      AND c.tenant_id = b.tenant_id
      AND c.deleted_at IS NULL
) cons ON TRUE
LEFT JOIN LATERAL (
    SELECT JSONB_AGG(
        JSONB_BUILD_OBJECT(
            'checkpoint_id', q.checkpoint_id,
            'checkpoint_name', cp.name,
            'outcome_code', o.code,
            'outcome_name', o.name,
            'measured_value', q.measured_value,
            'notes', q.notes,
            'ts', q.updated_at
        )
        ORDER BY q.updated_at
    ) AS qc_results
    FROM "11_somaerp".dtl_batch_qc_results q
    LEFT JOIN "11_somaerp".dim_qc_checkpoints cp ON cp.id = q.checkpoint_id
    LEFT JOIN "11_somaerp".dim_qc_outcomes o ON o.id = q.outcome_id
    WHERE q.batch_id = b.id
      AND q.tenant_id = b.tenant_id
      AND q.deleted_at IS NULL
) qc ON TRUE
WHERE b.deleted_at IS NULL;
COMMENT ON VIEW "11_somaerp".v_fssai_compliance_batches IS 'Per-batch FSSAI compliance dossier: lot numbers (array) + QC results (JSONB array) pre-aggregated for CSV export.';


-- DOWN ==================================================================

DROP VIEW IF EXISTS "11_somaerp".v_fssai_compliance_batches;
DROP VIEW IF EXISTS "11_somaerp".v_subscription_revenue_projected;
DROP VIEW IF EXISTS "11_somaerp".v_procurement_spend_monthly;
DROP VIEW IF EXISTS "11_somaerp".v_inventory_reorder_alerts;
DROP VIEW IF EXISTS "11_somaerp".v_batch_cogs_daily;
DROP VIEW IF EXISTS "11_somaerp".v_batch_yield_daily;
DROP VIEW IF EXISTS "11_somaerp".v_dashboard_today;
