---
phase: 56-somaerp-foundation
plan: 07
subsystem: recipes_equipment
completed: 2026-04-24
---

# Plan 56-07: Recipes + Equipment + BOM cost rollup — UNIFIED

**7 tables + 6 views. Recipes versioned with state machine + ingredients + steps. Equipment catalog + kitchen-equipment + recipe-step-equipment links. Live client-side cost display on /recipes/[id] (the "play with values" UI user requested).**

## Schema
- fct_recipes (versioned, partial-unique "one active per product")
- dtl_recipe_ingredients (raw_material + qty + unit + position)
- dtl_recipe_steps (step_number + name + duration_min + instructions)
- dim_equipment_categories (12 seeded: juicer/cold_press/fridge/freezer/cutting_board/knife_set/gas_stove/press/scale/bottler/labeler/storage_shelf)
- fct_equipment (purchase_cost, lifespan, status)
- lnk_kitchen_equipment (immutable — kitchen×equipment×quantity)
- lnk_recipe_step_equipment (immutable — step×equipment)
- Views: v_recipes, v_recipe_ingredients, v_recipe_steps, v_recipe_cost_summary (SUM with unit conversion via to_base_factor), v_equipment, v_kitchen_equipment

## Endpoints
14 under /v1/somaerp/recipes/* + /v1/somaerp/equipment/* + /v1/somaerp/geography/kitchens/{id}/equipment/*

## Seed
**ZERO tenant recipe data** per user directive 2026-04-24. Universal dim_equipment_categories seeded.

## Deviations
- User directive mid-execution: Green Morning recipe seed REMOVED; recipe tables cleaned via hard DELETE. Memory rule saved at feedback_never_seed_recipes.md.
- 6 equipment items + kitchen links were seeded pre-directive; kept but tenant-specific — user can edit/delete via UI. Future tenants ship with empty equipment.

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
