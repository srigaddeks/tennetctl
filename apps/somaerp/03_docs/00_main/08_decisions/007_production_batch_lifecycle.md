# ADR-007: Production batch lifecycle — state machine, recipe-pinned, computed metrics not stored
Status: ACCEPTED
Date: 2026-04-24

## Context

The production batch is somaerp's central entity. Every other layer (recipes, raw materials, procurement, QC, customers/subscriptions, delivery) ties back to "which batch did this come from / go into?" The driving Soma Delights workflow is the daily 4 AM production run logged from a phone with juice on the operator's hands. The decision is the lifecycle shape: what states a batch passes through, what immutable fields are pinned at creation (vs editable later), and what derived metrics (yield %, COGS per bottle) are stored vs computed on read.

## Decision

**`fct_production_batches (id, tenant_id, kitchen_id, product_id, recipe_id, run_date, planned_qty, actual_qty, status, shift_start, shift_end, currency_code, properties JSONB, created_by, created_at, updated_by, updated_at, deleted_at)` carries one row per batch with `status` ∈ `{planned, in_progress, completed, cancelled}`. Allowed transitions: `planned → in_progress`, `in_progress → completed`, `planned → cancelled`, `in_progress → cancelled`. `recipe_id` is pinned at creation and never changes — a batch is forever tied to the recipe version it was made under (per ADR-004). Batch detail is stored across three append-only/detail tables: `dtl_batch_step_logs` (timestamps + actor per recipe step), `dtl_batch_ingredient_consumption` (planned vs actual qty per raw material with cost), `dtl_batch_qc_results` (link to evt_qc_checks plus pass/fail summary). Computed metrics — yield % (actual_qty / planned_qty), COGS per bottle (sum of consumption.actual_qty * unit_cost / actual_qty), spoilage rate — are NOT stored; they are exposed via `v_batch_summary` computed at read time.**

## Consequences

- **Easier:** the 4 AM operator UI is shaped by the state machine — start a planned batch, log step timestamps, log actual consumption, record QC, complete. Each transition is one PATCH call.
- **Easier:** computed metrics are always consistent with the underlying detail rows; no double-write skew between stored yield and recomputed yield.
- **Easier:** FSSAI traceability is automatic — every completed batch has an immutable recipe_id, immutable consumption rows (each tied to a lot_number via inventory movement), immutable QC events.
- **Harder:** every read of yield % / COGS is a view-level aggregation. Acceptable at Soma Delights volume (~30-50 batches per day per kitchen). At higher volume, a materialized view with periodic refresh becomes the path; not for v0.9.0.
- **Harder:** state transitions need server-side validation (cannot complete a batch with no actual_qty, cannot start a batch whose recipe is not active for that kitchen). Service layer enforces.
- **Constrains:** ADR-004 (recipe pinning); ADR-005 (QC events tied to batch_id); ADR-006 (consumption emits `evt_inventory_movements` with `batch_id_ref`); the production data model layer (`01_data_model/07_production.md`); the production API design (`02_api_design/07_production.md`).

## Alternatives Considered

- **Action endpoints (`POST /v1/somaerp/production/batches/{id}/start`, `/complete`, `/cancel`).** Familiar shape. Rejected: violates the project-wide PATCH-for-state-changes rule; `PATCH {"status": "in_progress"}` is the canonical form.
- **Stored yield % and stored COGS per bottle.** Faster reads. Rejected: double-write skew is real; consumption corrections (an `adjusted` inventory movement) would silently desync stored metrics.
- **Editable recipe_id after batch creation.** More flexible. Rejected: destroys FSSAI traceability — a batch that started under recipe v1 and was retroactively re-pointed to recipe v2 is a regulatory disaster.
- **No state machine; status as free-text string.** Simplest. Rejected: every consumer would invent its own status taxonomy; transitions could not be validated.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `99_business_refs/somadelights/05-operations/daily-production-tracker.md`
- `99_business_refs/somadelights/09-execution/erp-system-plan.md`
- `apps/somaerp/03_docs/00_main/08_decisions/004_recipe_versioning_and_kitchen_overrides.md`
- `apps/somaerp/03_docs/00_main/08_decisions/005_qc_checkpoint_model.md`
- `apps/somaerp/03_docs/00_main/08_decisions/006_inventory_and_procurement_model.md`
