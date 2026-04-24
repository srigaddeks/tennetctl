# ADR-006: Inventory and procurement — append-only runs + append-only movements + computed current view
Status: ACCEPTED
Date: 2026-04-24

## Context

A cold-pressed kitchen's daily life is: buy raw materials at 5 AM (procurement run), receive them, consume some during today's batch, waste some that spoiled, possibly return some that arrived bad. FSSAI traceability requires lot-level tracking from receipt through consumption into the specific batch. The decision is how to model inventory state: as a mutable "current quantity per (kitchen, raw_material)" row (simple, fast reads, no history), or as an append-only event log of movements with current state derived (FSSAI-compliant, full history, slightly heavier reads).

## Decision

**Procurement and inventory are modeled as two append-only event tables plus a derived view. (1) `fct_procurement_runs (id, tenant_id, kitchen_id, supplier_id, run_date, performed_by_user_id, total_cost, currency_code, properties JSONB, ...)` is the header — one row per shopping trip or wholesale order. (2) `dtl_procurement_lines (id, tenant_id, procurement_run_id, raw_material_id, quantity, unit_id, unit_cost, lot_number, ...)` is the line items. (3) `evt_inventory_movements (id, tenant_id, kitchen_id, raw_material_id, movement_type, quantity, unit_id, lot_number, batch_id_ref, source_procurement_run_id, created_at, ...)` is the append-only movement log with `movement_type` ∈ `{received, consumed, wasted, returned, adjusted}`. Current inventory is exposed as the view `v_inventory_current (tenant_id, kitchen_id, raw_material_id, lot_number, current_qty, unit_id)` computed by summing signed movements. Lot numbers flow from receipt through consumption into batch_id_ref for FSSAI traceability.** Procurement runs and inventory movements are immutable after insert; corrections are new movements with `movement_type = adjusted`.

## Consequences

- **Easier:** FSSAI lot traceability is a single graph walk: batch_id → evt_inventory_movements (movement_type=consumed, batch_id_ref=...) → lot_number → original procurement_line → supplier.
- **Easier:** spoilage/waste accounting is automatic — every wasted unit is a `movement_type=wasted` event with a quantity and a reason.
- **Easier:** historical inventory ("what was the spinach stock on 2026-03-15?") is a sum of movements with `created_at <= '2026-03-15'`.
- **Harder:** every inventory read goes through a view that aggregates events. Performance requires a covering index on `evt_inventory_movements (tenant_id, kitchen_id, raw_material_id, lot_number, created_at)`. For very high movement volume, a periodic snapshot table (`dtl_inventory_snapshots`) may be added in v1.0; out of scope for v0.9.0.
- **Harder:** corrections require new event rows, not updates. The service layer encapsulates "correct movement" as "insert adjusted movement with reason = correction".
- **Constrains:** the raw materials and procurement data model layers (`01_data_model/05_raw_materials.md`, `01_data_model/06_procurement.md`); the production batch ingredient consumption (ADR-007 — consumption emits `evt_inventory_movements`); the FSSAI compliance scaling doc (`03_scaling/03_data_residency_compliance.md`).

## Alternatives Considered

- **Mutable `fct_inventory (kitchen_id, raw_material_id, current_qty)` row.** Simplest reads. Rejected: destroys lot traceability, destroys history, violates the project-wide append-only-`evt_*` rule.
- **Procurement and consumption merged into one event table.** Fewer tables. Rejected: procurement headers (one shopping trip with 30 line items, one supplier, one timestamp) have different shape from movements (one event per material per lot per action).
- **No lot numbers, FSSAI traceability deferred.** Faster v0.9.0. Rejected: FSSAI is a v0.9.0 hard requirement for Soma Delights, and lot tracking is the only mechanism.
- **Periodic snapshots from day 1.** Faster reads. Rejected: premature optimization; the view-over-events approach handles Soma Delights' volume (a few hundred movements per day) easily.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `99_business_refs/somadelights/05-operations/operations-model.md`
- `99_business_refs/somadelights/05-operations/supplier-vendor-directory.md`
- `99_business_refs/somadelights/09-execution/compliance-food-safety.md`
- `.claude/rules/common/database.md` (append-only `evt_*` rule)
