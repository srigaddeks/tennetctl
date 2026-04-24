# Data Model: Production

## Purpose

Models somaerp's central entity: the production batch. Per ADR-007, batches follow a state machine (`planned → in_progress → completed | cancelled`), are pinned to the exact `recipe_id` they were made under, and computed metrics (yield %, COGS per bottle) are exposed via views — never stored. Three detail tables capture per-step timestamps, planned vs actual ingredient consumption, and per-checkpoint QC summary. Consumption rows trigger `evt_inventory_movements` (per ADR-006) so inventory and FSSAI lot traceability stay in sync.

## Tables

### fct_production_batches

The batch header.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK DEFAULT uuid7() | |
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | |
| `product_id` | UUID NOT NULL REFERENCES fct_products(id) | |
| `recipe_id` | UUID NOT NULL REFERENCES fct_recipes(id) | pinned at insert; service rejects updates per ADR-007 |
| `run_date` | DATE NOT NULL | |
| `planned_qty` | NUMERIC(12,2) NOT NULL | bottles |
| `actual_qty` | NUMERIC(12,2) | NULL until completion |
| `yield_unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | usually "bottle" |
| `status` | TEXT NOT NULL DEFAULT 'planned' | planned / in_progress / completed / cancelled |
| `shift_start` | TIMESTAMPTZ | filled when status → in_progress |
| `shift_end` | TIMESTAMPTZ | filled when status → completed/cancelled |
| `cancel_reason` | TEXT | when status = cancelled |
| `currency_code` | CHAR(3) NOT NULL | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | tenant-specific (e.g. `{"shift":"morning","operator_notes":"..."}`) |
| `created_at` / `updated_at` | TIMESTAMPTZ | |
| `created_by` / `updated_by` | UUID | |
| `deleted_at` | TIMESTAMPTZ | rare; only for accidental creations before status change |

Constraints:
- `CHECK (status IN ('planned','in_progress','completed','cancelled'))`
- `CHECK ((status IN ('planned','cancelled')) OR shift_start IS NOT NULL)` — in_progress and completed must have shift_start
- `CHECK ((status <> 'completed') OR (shift_end IS NOT NULL AND actual_qty IS NOT NULL))`
- Service-level: `recipe_id` immutable after insert; transitions limited to `planned→in_progress`, `in_progress→completed`, `planned→cancelled`, `in_progress→cancelled`.

### dtl_batch_step_logs

One row per recipe step actually performed. Append-on-step but rows are mutable until batch completes (operator may edit a started step before logging completion).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `batch_id` | UUID NOT NULL REFERENCES fct_production_batches(id) | |
| `recipe_step_id` | UUID NOT NULL REFERENCES dtl_recipe_steps(id) | |
| `step_number` | SMALLINT NOT NULL | denormalized for sort |
| `started_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `completed_at` | TIMESTAMPTZ | NULL while in progress |
| `performed_by_user_id` | UUID NOT NULL | |
| `notes` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraint: `UNIQUE (tenant_id, batch_id, recipe_step_id)`. After batch completes, service rejects further updates.

### dtl_batch_ingredient_consumption

Per-ingredient planned vs actual consumption. Service inserts one row per recipe ingredient when batch transitions `planned → in_progress`; operator adjusts `actual_qty` and `lot_number` during/at-completion.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `batch_id` | UUID NOT NULL REFERENCES fct_production_batches(id) | |
| `raw_material_id` | UUID NOT NULL REFERENCES fct_raw_materials(id) | |
| `raw_material_variant_id` | UUID REFERENCES fct_raw_material_variants(id) | |
| `recipe_ingredient_id` | UUID REFERENCES dtl_recipe_ingredients(id) | source recipe line for traceability |
| `planned_qty` | NUMERIC(14,4) NOT NULL | from recipe |
| `actual_qty` | NUMERIC(14,4) | NULL until logged |
| `unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | |
| `lot_number` | TEXT | required when actual_qty > 0 (FSSAI) |
| `unit_cost_at_consumption` | NUMERIC(14,4) | snapshot |
| `currency_code` | CHAR(3) NOT NULL | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraint: `UNIQUE (tenant_id, batch_id, raw_material_id, lot_number)` (one consumption line per material per lot per batch).

When `actual_qty` is finalized, service inserts a corresponding `evt_inventory_movements` row with `movement_type='consumed'` and `batch_id_ref = this.batch_id`.

### dtl_batch_qc_results

Per-checkpoint summary for the batch. Each row is a "this checkpoint was performed N times during this batch with these outcomes" rollup. The actual events live in `evt_qc_checks`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `batch_id` | UUID NOT NULL REFERENCES fct_production_batches(id) | |
| `checkpoint_id` | UUID NOT NULL REFERENCES dim_qc_checkpoints(id) | |
| `result` | TEXT NOT NULL | "pass" / "fail" / "warn" — the worst-case across events |
| `events_count` | INTEGER NOT NULL DEFAULT 0 | |
| `last_event_id` | UUID REFERENCES evt_qc_checks(id) | |
| `notes` | TEXT | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraint: `UNIQUE (tenant_id, batch_id, checkpoint_id)`. Service rebuilds row on each new `evt_qc_checks` insert for that batch+checkpoint.

## Views (v_*)

- `v_production_batches` — `fct_production_batches` joined with `fct_kitchens`, `fct_products`, `fct_recipes` (recipe_name, recipe_version).
- `v_batch_step_logs` — `dtl_batch_step_logs` joined with `dtl_recipe_steps` and `dim_recipe_step_kinds`.
- `v_batch_ingredient_consumption` — `dtl_batch_ingredient_consumption` joined with `fct_raw_materials` and `dim_units_of_measure`.
- `v_batch_summary` — the headline view. Per batch: yield_pct (`actual_qty / planned_qty`), total_cogs (`sum(actual_qty * unit_cost_at_consumption)`), cogs_per_bottle (`total_cogs / actual_qty`), spoilage_qty (sum of `wasted` movements with `batch_id_ref = batch.id`), qc summary (passed/failed/warned counts via `v_batch_qc_summary`).

Pattern (illustrative):
```
CREATE VIEW v_batch_summary AS
SELECT b.id AS batch_id, b.tenant_id, b.kitchen_id, b.product_id, b.recipe_id,
       b.run_date, b.status, b.planned_qty, b.actual_qty,
       CASE WHEN b.planned_qty > 0 THEN (b.actual_qty / b.planned_qty) ELSE NULL END AS yield_pct,
       (SELECT sum(c.actual_qty * c.unit_cost_at_consumption)
          FROM dtl_batch_ingredient_consumption c
         WHERE c.batch_id = b.id AND c.tenant_id = b.tenant_id) AS total_cogs,
       CASE WHEN b.actual_qty > 0 THEN
         (SELECT sum(c.actual_qty * c.unit_cost_at_consumption)
            FROM dtl_batch_ingredient_consumption c
           WHERE c.batch_id = b.id AND c.tenant_id = b.tenant_id) / b.actual_qty
       ELSE NULL END AS cogs_per_unit,
       (SELECT sum(m.quantity)
          FROM evt_inventory_movements m
         WHERE m.batch_id_ref = b.id AND m.movement_type = 'wasted'
           AND m.tenant_id = b.tenant_id) AS spoilage_qty,
       qcs.checks_passed, qcs.checks_failed, qcs.checks_warned, qcs.checks_performed
FROM fct_production_batches b
LEFT JOIN v_batch_qc_summary qcs ON qcs.batch_id = b.id
WHERE b.deleted_at IS NULL;
```

## Indexes

- `fct_production_batches (tenant_id, kitchen_id, run_date DESC) WHERE deleted_at IS NULL` — operator's "today and recent" query
- `fct_production_batches (tenant_id, status, run_date) WHERE deleted_at IS NULL` — planning queries
- `fct_production_batches (tenant_id, product_id, run_date DESC) WHERE deleted_at IS NULL` — yield-by-SKU analytics
- `fct_production_batches (tenant_id, recipe_id, run_date DESC) WHERE deleted_at IS NULL` — recipe traceability
- `dtl_batch_step_logs (tenant_id, batch_id, step_number)`
- `dtl_batch_ingredient_consumption (tenant_id, batch_id)`
- `dtl_batch_qc_results (tenant_id, batch_id)`

## Audit emission keys

- `somaerp.production.batches.created` (status=planned)
- `somaerp.production.batches.started` (planned → in_progress)
- `somaerp.production.batches.completed` (in_progress → completed)
- `somaerp.production.batches.cancelled` (* → cancelled)
- `somaerp.production.step_logs.recorded` (insert / completion of a step)
- `somaerp.production.consumption.recorded` (per ingredient consumption finalize) — also triggers `somaerp.inventory.movements.consumed`
- `somaerp.production.qc_results.updated` (rollup row updated from a new evt_qc_check)

## Cross-layer relationships

- `fct_production_batches.kitchen_id` → `01_geography.fct_kitchens.id`
- `fct_production_batches.product_id` → `02_catalog.fct_products.id`
- `fct_production_batches.recipe_id` → `03_recipes.fct_recipes.id` (pinned)
- `dtl_batch_step_logs.recipe_step_id` → `03_recipes.dtl_recipe_steps.id`
- `dtl_batch_ingredient_consumption.raw_material_id` → `05_raw_materials.fct_raw_materials.id`
- `dtl_batch_ingredient_consumption.recipe_ingredient_id` → `03_recipes.dtl_recipe_ingredients.id`
- `dtl_batch_qc_results.checkpoint_id` → `04_quality.dim_qc_checkpoints.id`
- `dtl_batch_qc_results.last_event_id` → `04_quality.evt_qc_checks.id`
- `fct_production_batches.id` ← `06_procurement.evt_inventory_movements.batch_id_ref` (consumption + wastage linkage)

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `fct_production_batches` | empty at bootstrap |
| Example morning batch | `(kitchen=KPHB Home Kitchen, product=Green Morning, recipe=Green Morning v1, run_date=2026-04-25, planned_qty=20, actual_qty=18, status=completed, shift_start=04:15, shift_end=07:40, INR, properties={"shift":"morning"})` |
| `dtl_batch_ingredient_consumption` example | `(spinach, planned=1.6kg, actual=1.55kg, unit=kg, lot=KPHB-20260425-001-spinach, unit_cost=20.00)`; same for cucumber, apple, lemon, ginger, mint |
| `dtl_batch_step_logs` example | step1 wash 04:15-04:25, step2 chop 04:25-04:50, step3 press 04:50-06:30, step4 strain 06:30-07:00, step5 bottle 07:00-07:30, step6 label 07:30-07:40 |
| `dtl_batch_qc_results` example | `(checkpoint=Bottle temperature, result=pass, events=18, last_event_id=...)`, `(checkpoint=Final taste, result=pass, events=2)` |

## Open questions

- Materialized vs plain view for `v_batch_summary` — defaulted to plain; revisit at scale.
- Whether to allow batch splits (one planned batch → two production runs) — currently no; create two batches. Revisit if operator workflow demands.
- Recipe-step-vs-batch-step shape: currently 1:1 row in `dtl_batch_step_logs` per recipe step. Allowing 1:N (a step done in two passes) — carry as `properties.passes` until a use case demands.
- Multi-product co-production (one press cycle yields two products) — out of v0.9.0 scope; would require batch-shared-resource model.
