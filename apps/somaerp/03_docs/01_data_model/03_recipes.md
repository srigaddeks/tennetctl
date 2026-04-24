# Data Model: Recipes

## Purpose

Models the operational truth of "how to make a product": versioned recipes (draft / active / archived), ingredient lines, step lines, and per-kitchen overrides. A production batch is permanently pinned to the exact `recipe_id` it was made under (per ADR-007), so recipes must be versioned, not mutated. Per-kitchen variation (KPHB has a slightly different process than the future Miyapur satellite) is modeled by `lnk_kitchen_recipe_overrides` (per ADR-004).

## Tables

### dim_recipe_step_kinds

Static taxonomy of process steps. Used to type recipe steps for UI grouping and time-based scheduling.

| Column | Type | Notes |
|---|---|---|
| `id` | SMALLINT PK | |
| `code` | TEXT NOT NULL UNIQUE | "wash" / "chop" / "press" / "blend" / "strain" / "bottle" / "label" / "store" / "dehydrate" / "ferment" |
| `name` | TEXT NOT NULL | |

### fct_recipes

Versioned recipe header. One product can have many recipes across versions; only one active per (product, kitchen-context) at a time.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK DEFAULT uuid7() | |
| `tenant_id` | UUID NOT NULL | |
| `product_id` | UUID NOT NULL REFERENCES fct_products(id) | |
| `version` | INTEGER NOT NULL | monotonic per product |
| `name` | TEXT NOT NULL | "Green Morning v1" |
| `status` | TEXT NOT NULL DEFAULT 'draft' | draft / active / archived |
| `published_at` | TIMESTAMPTZ | set on first transition to active |
| `archived_at` | TIMESTAMPTZ | set on transition to archived |
| `yield_value` | NUMERIC(12,2) NOT NULL | e.g. 1 (yields one bottle) |
| `yield_unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | |
| `expected_duration_min` | INTEGER | |
| `properties` | JSONB NOT NULL DEFAULT '{}' | tenant-specific notes |
| audit/timestamp/soft-delete columns | as conventions | |

Constraints:
- `UNIQUE (tenant_id, product_id, version) WHERE deleted_at IS NULL`
- Partial unique: `UNIQUE (tenant_id, product_id) WHERE status = 'active' AND deleted_at IS NULL` — at most one active recipe per product
- `CHECK (status IN ('draft','active','archived'))`

State machine: `draft → active → archived`. Editing an active recipe requires creating a new draft (next version), publishing it (which auto-archives the prior active), and the new draft becomes active. Service layer enforces this transition.

### dtl_recipe_ingredients

Per-ingredient line. One row per ingredient per recipe.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `recipe_id` | UUID NOT NULL REFERENCES fct_recipes(id) | |
| `raw_material_id` | UUID NOT NULL REFERENCES fct_raw_materials(id) | |
| `quantity` | NUMERIC(12,4) NOT NULL | e.g. 80.0 |
| `unit_id` | SMALLINT NOT NULL REFERENCES dim_units_of_measure(id) | "g" |
| `is_optional` | BOOLEAN NOT NULL DEFAULT FALSE | |
| `notes` | TEXT | "remove stems before pressing" |
| `display_order` | SMALLINT NOT NULL DEFAULT 0 | |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraint: `UNIQUE (tenant_id, recipe_id, raw_material_id)`.

### dtl_recipe_steps

Per-step line. Ordered by `step_number`.

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID NOT NULL | |
| `recipe_id` | UUID NOT NULL REFERENCES fct_recipes(id) | |
| `step_number` | SMALLINT NOT NULL | 1-based |
| `step_kind_id` | SMALLINT NOT NULL REFERENCES dim_recipe_step_kinds(id) | |
| `name` | TEXT NOT NULL | "Wash and chop spinach" |
| `instructions` | TEXT | |
| `expected_duration_min` | INTEGER | |
| `equipment` | TEXT | "cold-press juicer" |
| `created_at` / `updated_at` | TIMESTAMPTZ | |

Constraint: `UNIQUE (tenant_id, recipe_id, step_number)`.

### lnk_kitchen_recipe_overrides

Per-kitchen override of a base recipe. The base recipe is the canonical one; the override is a separate `fct_recipes` row whose ingredients/steps differ for that kitchen. Per ADR-004.

| Column | Type | Notes |
|---|---|---|
| `tenant_id` | UUID NOT NULL | |
| `kitchen_id` | UUID NOT NULL REFERENCES fct_kitchens(id) | |
| `base_recipe_id` | UUID NOT NULL REFERENCES fct_recipes(id) | the canonical recipe |
| `override_recipe_id` | UUID NOT NULL REFERENCES fct_recipes(id) | the kitchen-specific variant |
| `effective_from` | DATE NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL DEFAULT now() | |
| `created_by` | UUID NOT NULL | |
| PRIMARY KEY | `(tenant_id, kitchen_id, base_recipe_id, effective_from)` | |

No `updated_at`, no `deleted_at` (immutable join). To remove an override: insert a tombstone row with `override_recipe_id = base_recipe_id` and a new `effective_from`.

CHECK constraint: `base_recipe_id <> override_recipe_id` (sanity), enforced by service layer where the tombstone exception is needed.

## Views (v_*)

- `v_recipes` — `fct_recipes` joined with `fct_products` for product_name and `dim_units_of_measure` for yield_unit. Aggregates ingredient and step counts.
- `v_recipe_ingredients` — `dtl_recipe_ingredients` joined with `fct_raw_materials` for material_name and `dim_units_of_measure` for unit symbol.
- `v_recipe_steps` — `dtl_recipe_steps` joined with `dim_recipe_step_kinds` for step_kind_code.
- `v_kitchen_active_recipe` — for a given (kitchen_id, product_id), returns the override recipe if a current `lnk_kitchen_recipe_overrides` row exists, else the active base recipe. Used by the production planner.

## Indexes

- `fct_recipes (tenant_id, product_id, status) WHERE deleted_at IS NULL`
- `fct_recipes (tenant_id, status, product_id)` — supports "all active recipes" listing
- `dtl_recipe_ingredients (tenant_id, recipe_id, display_order)`
- `dtl_recipe_steps (tenant_id, recipe_id, step_number)`
- `lnk_kitchen_recipe_overrides (tenant_id, kitchen_id, base_recipe_id, effective_from DESC)`

## Audit emission keys

- `somaerp.recipes.recipes.created` (status=draft)
- `somaerp.recipes.recipes.published` (status: draft → active; auto-archives prior active)
- `somaerp.recipes.recipes.archived`
- `somaerp.recipes.recipes.updated` (draft only)
- `somaerp.recipes.ingredients.added` / `.updated` / `.removed`
- `somaerp.recipes.steps.added` / `.updated` / `.removed`
- `somaerp.recipes.kitchen_override.applied` / `.removed`

## Cross-layer relationships

- `fct_recipes.product_id` → `02_catalog.fct_products.id`
- `dtl_recipe_ingredients.raw_material_id` → `05_raw_materials.fct_raw_materials.id`
- `lnk_kitchen_recipe_overrides.kitchen_id` → `01_geography.fct_kitchens.id`
- `fct_recipes.id` ← `07_production.fct_production_batches.recipe_id` (the pinning per ADR-007)

## Soma Delights tenant seed examples

| Table | Row |
|---|---|
| `dim_recipe_step_kinds` | `(wash)`, `(chop)`, `(press)`, `(strain)`, `(bottle)`, `(label)`, `(store)` |
| `fct_recipes` | `(product=Green Morning, version=1, status=active, yield=1 bottle, expected_duration=12 min)` |
| `dtl_recipe_ingredients` (for Green Morning v1) | spinach 80g, cucumber 120g, green apple 80g, lemon 20g, ginger 5g, mint 5g |
| `dtl_recipe_steps` (for Green Morning v1) | step 1 wash all produce, step 2 chop greens & fruit, step 3 press through cold-press juicer, step 4 strain, step 5 bottle in 300ml PET, step 6 label with date/time |
| `lnk_kitchen_recipe_overrides` | none at Stage 1 (single kitchen) |

## Open questions

- Whether to allow multi-version active recipes per product if regional kitchens use different base recipes — current answer: no, override is the mechanism. Revisit if a tenant runs two product lines under one product slug.
- Allergen tags per ingredient line (deferred per phase-56 boundaries — out of v0.9.0 scope; carry in `properties` if needed).
- Recipe forking for R&D (a draft branched off an active recipe for taste testing) — carried in `properties.parent_recipe_id` until a workflow is built.
