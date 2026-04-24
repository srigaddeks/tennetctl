# Data Model: Quality

## Purpose

Models multi-stage QC: pre-production (raw material acceptance), in-production (per recipe step), post-production (bottle/label/temperature checks), and FSSAI traceability events. Per ADR-005, checkpoints are reusable definitions in `dim_qc_checkpoints` and the actual results are append-only events in `evt_qc_checks`. Photos referenced via `tennetctl 02_vault` keys (per ADR-008 and `04_integration/03_vault_for_secrets_and_blobs.md`).

## Tables

### dim_qc_check_types

What is being checked.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "visual" / "smell" / "weight" / "temperature" / "taste" / "ph" / "color" / "firmness" |
| `name` | TEXT NOT NULL | |
| `result_type` | TEXT NOT NULL | "boolean" / "numeric" / "scale_1_5" |

### dim_qc_stages

When in the process the check happens.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "pre_production" / "in_production" / "post_production" / "fssai" |
| `name` | TEXT NOT NULL | |

### dim_qc_checkpoints

A reusable checkpoint definition. Tenant-scoped because criteria are tenant-specific. Optionally bound to a recipe step (when stage = in_production) or a raw material (when stage = pre_production).

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | uuid7; `dim_*` here is `dim` by role (lookup of definitions), but tenant-scoped, so it carries `tenant_id` |
| `tenant_id` | UUID NOT NULL | |
| `name` | TEXT NOT NULL | "Spinach color/freshness check" |
| `stage_id` | SMALLINT NOT NULL REFERENCES dim_qc_stages(id) | |
| `check_type_id` | SMALLINT NOT NULL REFERENCES dim_qc_check_types(id) | |
| `recipe_id` | UUID REFERENCES fct_recipes(id) | nullable |
| `recipe_step_number` | SMALLINT | nullable; only set when stage = in_production |
| `raw_material_id` | UUID REFERENCES fct_raw_materials(id) | nullable; only set when stage = pre_production |
| `criteria_jsonb` | JSONB NOT NULL DEFAULT '{}' | e.g. `{"min_temp_c":2,"max_temp_c":8}` or `{"required_color":"deep_green"}` |
| `is_required` | BOOLEAN NOT NULL DEFAULT TRUE | failure = batch blocks |
| `properties` | JSONB NOT NULL DEFAULT '{}' | |
| audit/timestamp/soft-delete columns | as conventions | |

CHECK constraints:
- `(recipe_id IS NULL) OR (recipe_step_number IS NOT NULL)` not enforced — `recipe_step_number` only meaningful when `recipe_id IS NOT NULL` and stage = `in_production`. Service layer validates.

### evt_qc_checks

Append-only QC event. One row per check performed. Immutable.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `checkpoint_id` | UUID NOT NULL REFERENCES dim_qc_checkpoints(id) | |
| `batch_id` | UUID REFERENCES fct_production_batches(id) | nullable for pre_production checks on raw materials |
| `procurement_line_id` | UUID REFERENCES dtl_procurement_lines(id) | nullable; populated for pre_production checks |
| `lot_number` | TEXT | populated when applicable |
| `performed_by_user_id` | UUID NOT NULL | tennetctl user id |
| `result` | TEXT NOT NULL | "pass" / "fail" / "warn" |
| `result_value` | NUMERIC(12,4) | for numeric check_type |
| `result_scale` | SMALLINT | for scale_1_5 |
| `notes` | TEXT | |
| `photo_vault_key` | TEXT | tennetctl vault key |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |

No `updated_at`, no `deleted_at`. Corrections are new rows with `notes` pointing to the corrected event.

CHECK: `result IN ('pass','fail','warn')`.

## Views (v_*)

- `v_qc_checkpoints` — `dim_qc_checkpoints` joined with `dim_qc_stages` and `dim_qc_check_types` for code labels; resolves the optional `recipe_id` to recipe name and `raw_material_id` to material name.
- `v_qc_checks_recent` — `evt_qc_checks` for last 90 days joined with checkpoint label, batch summary, and result; used by QC dashboard.
- `v_batch_qc_summary` — per-batch aggregation: count of checkpoints required, count performed, count passed/failed/warned. Used by `v_batch_summary` (07_production).

Pattern (illustrative):
```
CREATE VIEW v_batch_qc_summary AS
SELECT b.id AS batch_id, b.tenant_id,
       count(*) FILTER (WHERE qc.id IS NOT NULL) AS checks_performed,
       count(*) FILTER (WHERE qc.result = 'pass') AS checks_passed,
       count(*) FILTER (WHERE qc.result = 'fail') AS checks_failed,
       count(*) FILTER (WHERE qc.result = 'warn') AS checks_warned
FROM fct_production_batches b
LEFT JOIN evt_qc_checks qc ON qc.batch_id = b.id AND qc.tenant_id = b.tenant_id
GROUP BY b.id, b.tenant_id;
```

## Indexes

- `dim_qc_checkpoints (tenant_id, stage_id) WHERE deleted_at IS NULL`
- `dim_qc_checkpoints (tenant_id, recipe_id, recipe_step_number) WHERE deleted_at IS NULL`
- `evt_qc_checks (tenant_id, batch_id, created_at)` — for batch-detail queries
- `evt_qc_checks (tenant_id, lot_number)` — for FSSAI lot traceability queries
- `evt_qc_checks (tenant_id, performed_by_user_id, created_at DESC)` — for operator audit

## Audit emission keys

- `somaerp.quality.checkpoints.created` / `.updated` / `.deleted`
- `somaerp.quality.checks.recorded` (one per `evt_qc_checks` insert)
- `somaerp.quality.checks.failure` (emitted in addition when `result = 'fail'` — triggers downstream notification flow)

## Cross-layer relationships

- `dim_qc_checkpoints.recipe_id` → `03_recipes.fct_recipes.id`
- `dim_qc_checkpoints.raw_material_id` → `05_raw_materials.fct_raw_materials.id`
- `evt_qc_checks.batch_id` → `07_production.fct_production_batches.id`
- `evt_qc_checks.procurement_line_id` → `06_procurement.dtl_procurement_lines.id`
- `evt_qc_checks.photo_vault_key` → tennetctl 02_vault key (no FK; cross-system)

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_qc_check_types` | `(visual)`, `(smell)`, `(weight)`, `(temperature)`, `(taste)`, `(firmness)` |
| `dim_qc_stages` | `(pre_production)`, `(in_production)`, `(post_production)`, `(fssai)` |
| `dim_qc_checkpoints` | `(Spinach acceptance, pre_production, visual, raw_material=spinach, criteria={"required_color":"bright_green","no_yellowing":true})`; `(Bottle temperature, post_production, temperature, criteria={"max_temp_c":8})`; `(Final taste, post_production, taste, criteria={"scale_min":4})`; `(FSSAI lot record, fssai, visual)` |
| `evt_qc_checks` | none initially; populated per batch from Stage 1 onward |

## Open questions

- Whether `dim_qc_checkpoints` should be split into `fct_qc_checkpoints` since it carries tenant_id and uuid PK — naming kept as `dim` because it functions as a checkpoint catalog; revisit at audit time.
- Whether to support multiple photo attachments per check (carry as JSONB array of vault keys) — currently single `photo_vault_key`; promote when multi-photo workflow ships.
- Lab analysis integration (when sending samples to an external lab for FSSAI batch testing) — out of v0.9.0 scope; carry external lab_report_id in `properties` when needed.
