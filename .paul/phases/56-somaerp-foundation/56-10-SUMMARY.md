---
phase: 56-somaerp-foundation
plan: 10
subsystem: production_batches
completed: 2026-04-24
---

# Plan 56-10: Production Batches — UNIFIED (THE driving workflow)

**The 4 AM mobile tracker. State machine planned → in_progress → completed | cancelled. Auto-emits evt_inventory_movements 'consumed' on completion. Live yield/COGS/margin rollup view.**

## Schema
- fct_production_batches (partial unique: one active batch per kitchen+product+shift; CHECK planned_qty>0, actual_qty>=0)
- dtl_batch_step_logs (auto-generated from recipe on batch create)
- dtl_batch_ingredient_consumption (auto-generated + GENERATED line_cost_actual; unit_cost_snapshot copied from raw_material at batch create to freeze pricing)
- dtl_batch_qc_results (links batch × checkpoint × outcome)
- Views: v_production_batches, v_batch_summary (yield_pct + total_cogs + cogs_per_unit + gross_margin_pct vs product.default_selling_price + duration_min), v_batch_consumption, v_batch_qc_results

## Endpoints
Under /v1/somaerp/production/*:
- batches CRUD + state PATCH + step start/complete via PATCH on step logs + consumption PATCH (actual_qty + lot) + QC record + batch summary + today's board

## Key behavior
- Create-batch is transactional: looks up active recipe + auto-generates step logs + consumption-plan (with unit conversion to raw_material default unit + unit_cost_snapshot)
- Complete-batch is transactional: updates status + inserts evt_inventory_movements 'consumed' for every consumption line (quantity = actual_qty, with signed-via-type accounting)

## Mobile UI
/production/batches/[id] — sticky top with big state button + live KPIs; two-pane (stacked on mobile) with step progression + editable consumption; big "Complete Batch" with confirm modal.

## Seed
ZERO. User creates batches via UI.

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
