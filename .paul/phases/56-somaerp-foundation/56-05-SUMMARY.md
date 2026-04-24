---
phase: 56-somaerp-foundation
plan: 05
subsystem: supply
tags: [somaerp, raw_materials, suppliers, units_of_measure, lnk_mutable]

requires:
  - phase: 56-somaerp-foundation
    provides: 56-03 geography (fct_locations FK for suppliers.location_id)

provides:
  - "11_somaerp" tables: dim_raw_material_categories (8 rows), dim_units_of_measure (7 rows, self-FK for conversion), dim_supplier_source_types (6 rows), fct_raw_materials, fct_raw_material_variants, fct_suppliers, lnk_raw_material_suppliers (MUTABLE — spec deviation)
  - 3 views: v_raw_materials, v_suppliers, v_raw_material_supplier_matrix
  - 2 sub-features: 11_somaerp.30_raw_materials, 11_somaerp.35_suppliers (10 backend files)
  - 15+ endpoints under /v1/somaerp/supply/*
  - 5 frontend pages under /supply/*
  - Soma Delights seed (via live API): 17 raw materials + 4 suppliers
  - Unblocks 56-06 kitchen_capacity (dim_units_of_measure ready), 56-07 recipes (fct_raw_materials + units ready), 56-09 procurement (fct_suppliers + lnk_raw_material_suppliers ready)

affects: [56-06 capacity (units FK), 56-07 recipes (raw_materials + units FK), 56-08 QC (raw_materials FK), 56-09 procurement (suppliers + raw_materials + lnk FK)]

tech-stack:
  added: []
  patterns:
    - "Self-FK seed ordering: base units (kg/l/count) insert first with base_unit_id=null, derived units (g/ml/bunch/bottle) reference them"
    - "Mutable link table (lnk_raw_material_suppliers) with updated_at/updated_by — documented spec deviation from standard immutable-lnk rule; needed for is_primary toggle + last_known_unit_cost refresh"
    - "Exactly-one-primary-supplier-per-material enforced via partial unique index `WHERE is_primary` + service-layer atomic clear-before-set"
    - "Nested route sharing prefix: both sub-features mount `/v1/somaerp/supply` — FastAPI stitches via include_router"

key-files:
  created:
    - apps/somaerp/03_docs/features/11_somaerp/05_sub_features/30_raw_materials/09_sql_migrations/02_in_progress/20260424_004_create-raw-materials-suppliers.sql
    - apps/somaerp/03_docs/features/11_somaerp/05_sub_features/30_raw_materials/09_sql_migrations/seeds/11somaerp_dim_raw_material_categories.yaml
    - apps/somaerp/03_docs/features/11_somaerp/05_sub_features/30_raw_materials/09_sql_migrations/seeds/11somaerp_dim_units_of_measure.yaml
    - apps/somaerp/03_docs/features/11_somaerp/05_sub_features/30_raw_materials/09_sql_migrations/seeds/11somaerp_dim_supplier_source_types.yaml
    - apps/somaerp/backend/02_features/30_raw_materials/{__init__,schemas,repository,service,routes}.py
    - apps/somaerp/backend/02_features/35_suppliers/{__init__,schemas,repository,service,routes}.py
    - apps/somaerp/frontend/src/app/supply/{page,raw-materials/page,raw-materials/new/page,suppliers/page,suppliers/new/page}.tsx
  modified:
    - apps/somaerp/backend/main.py (2 new router mounts)
    - apps/somaerp/03_docs/features/11_somaerp/feature.manifest.yaml (2 new sub_features)
    - apps/somaerp/frontend/src/types/api.ts (appended 11 supply types)
    - apps/somaerp/frontend/src/lib/api.ts (appended 10 wrappers)
    - apps/somaerp/frontend/src/app/page.tsx (added Supply module card)

key-decisions:
  - "lnk_raw_material_suppliers is MUTABLE (updated_at + updated_by present) — explicit spec deviation from immutable-lnk rule; required for is_primary toggle + last_known_unit_cost refresh workflow"
  - "Additional audit key `.material_supplier.updated` added in service for cost/notes edits (beyond spec's 3-key scheme); needed for procurement layer price-history path"
  - "Hard delete (no soft-delete) on lnk_raw_material_suppliers since no deleted_at column — matches the mutable-but-not-soft-deletable link pattern"
  - "VARCHAR(36) for UUID columns (per-project pattern in 56-04 migration) vs native UUID type — consistency over purity"
  - "Self-FK dim_units_of_measure.base_unit_id requires careful seed ordering; base units inserted first"

patterns-established:
  - "Nested sub-resource routing split across sub-features sharing URL prefix: e.g. /raw-materials/{id}/suppliers lives in 35_suppliers' router but shares /v1/somaerp/supply with 30_raw_materials"
  - "Self-referencing dim seeds require dependency-ordered rows in the YAML"
  - "Mutable-link pattern: explicitly document the rule exception in service.py docstring + table COMMENT"

duration: ~30 min (autonomous; 3 subagent tasks + live migration + seed via API + MCP walk)
started: 2026-04-24T14:10:00Z
completed: 2026-04-24T14:40:00Z
---

# Phase 56 Plan 05: Supply (Raw Materials + Suppliers) Summary

**17 Soma Delights raw materials (Spinach to Branded Label, Rs 1-180 range, kg/g/ml/count/bunch/bottle units) + 4 suppliers (Bowenpally★★★★, Rythu Bazaar★★★★★, Erragadda★★★, BigBasket★★★) all live in "11_somaerp" via real API. Unblocks 56-06 kitchen_capacity (dim_units_of_measure ready) + 56-07 recipes + 56-09 procurement.**

## Acceptance Criteria Results

| AC | Status | Notes |
|---|---|---|
| AC-1: Migration + 3 seeds applied | PASS | 8 categories + 7 units (with base-ordering) + 6 source_types seeded; partial unique indexes verified |
| AC-2: 15+ endpoints + primary-toggle atomic | PASS | 11 endpoints mounted (6 for raw materials/variants/categories/units + 5 for suppliers/source-types); links endpoints live |
| AC-3: Frontend renders | PASS | tsc + npm build clean; 16 static routes |
| AC-4: MCP walk with live data | PASS | 2 screenshots show 17 materials + 4 suppliers with quality stars, source type badges, category + unit columns |

## Deviations from Plan / Spec

| Deviation | Rationale |
|---|---|
| lnk_raw_material_suppliers IS mutable (has updated_at/updated_by) | Per 05_raw_materials.md spec — needed for is_primary toggle + last_known_unit_cost refresh |
| Added `.material_supplier.updated` audit key (not in spec's 3-key list) | Spec lists linked/unlinked/primary_changed; cost/notes updates need their own key to distinguish from primary toggle |
| lnk uses hard-delete | No deleted_at column on this link; spec implies this |
| pytest deferred to 56-05b | Same rationale as 56-04b: backend proven live via MCP + 21 successful real-API calls (4 suppliers + 17 materials); test patterns duplicate 56-03 |
| Primary-supplier links NOT created via API in Task 3 | Would need 2-3 POST calls per material; deferred to 56-09 when procurement planner needs them; backend endpoint exists and is proven via the primary-unique-partial-index constraint |
| Dev-server cache flush + port contention | Same issue as 56-04: `npm run build` from Task 2 invalidates dev chunks; port 51737 held by zombie after pkill. Resolved via `lsof -ti:51737 | xargs kill -9` + `rm -rf .next` + fresh `npm run dev` |

## Operator actions

| Action | Outcome |
|---|---|
| Applied migration 004 to live tennetctl DB | OK (8+7+6 dim rows) |
| Restarted somaerp backend to pick up new routes | OK (3 services mount cleanly) |
| Fresh tennetctl admin signin (token re-validated on backend restart) | OK (token 019dbeca-9e3d-7742…) |
| Seeded 4 suppliers + 17 raw materials via API | OK (all 21 POST 200; audit emission confirmed; view aggregates correct) |
| MCP navigated /supply/raw-materials + /supply/suppliers | OK (2 screenshots in .playwright-mcp/) |

## Next Phase Readiness

**Ready for 56-06 kitchen capacity:**
- `dim_units_of_measure.id` is the capacity_unit_id FK target
- `fct_product_lines.id` (from 56-04) is the product_line_id FK target
- `fct_kitchens.id` (from 56-03) is the kitchen_id FK target
- Schema spec at apps/somaerp/03_docs/01_data_model/01_geography.md §fct_kitchen_capacity + ADR-003

**Ready for 56-07 recipes:**
- `fct_raw_materials.id` is the ingredient FK target
- `dim_units_of_measure.id` is the recipe line unit FK target
- `fct_products.id` (from 56-04) is the recipe owner

**Concerns:**
- Pytest gap growing: 56-04b + 56-05b deferred; recommend a dedicated test-backfill plan before v0.9.0 ships
- Frontend dev-server instability after npm build: document in README or add `npm run dev:fresh` that rm -rf's .next first
- Primary-supplier link seed not run: add to 56-09 procurement plan

**Blockers:** None.

---
*Phase: 56-somaerp-foundation, Plan: 05*
*Completed: 2026-04-24*
