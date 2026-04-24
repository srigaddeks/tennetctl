---
phase: 56-somaerp-foundation
plan: 09
subsystem: procurement_inventory_mrp
completed: 2026-04-24
---

# Plan 56-09: Procurement + Inventory + MRP-lite planner — UNIFIED

**Ships user's "raw materials needed for any given day" workflow as POST /v1/somaerp/inventory/plan BOM-explosion endpoint.**

## Schema
- fct_procurement_runs (status state machine active/reconciled/cancelled)
- dtl_procurement_lines (GENERATED line_cost column)
- evt_inventory_movements (append-only, 5 movement_types, signed via type not quantity)
- Views: v_procurement_runs, v_inventory_movements, v_inventory_current (base-unit conversion via to_base_factor)

## Endpoints
- Procurement runs + lines CRUD (adding a line auto-emits 'received' movement in same tx)
- Inventory movements read-only feed + POST manual adjustment
- **POST /inventory/plan** — BOM explosion: demand list → active-recipe ingredient rollup → unit conversion → subtract v_inventory_current → gap + primary supplier + est cost

## Seed
ZERO — no procurement runs, no movements, no plans.

## Live verification
- `empty arrays` for runs / current / movements
- POST /plan with real kitchen + product → errors.no_active_recipe (expected — no recipes seeded)

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
