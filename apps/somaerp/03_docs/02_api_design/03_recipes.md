# API Design: Recipes

Conventions: see `00_conventions.md`. Endpoints rooted at `/v1/somaerp/recipes/...`. RBAC scopes: `somaerp.recipes.read` / `.write` / `.publish` / `.admin`. Audit emission keys mirror `01_data_model/03_recipes.md`.

## Endpoints

### Recipes

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/recipes/recipes` | `recipes.read` | (none) |
| POST | `/v1/somaerp/recipes/recipes` | `recipes.write` | `somaerp.recipes.recipes.created` (status=draft only) |
| GET | `/v1/somaerp/recipes/recipes/{id}` | `recipes.read` | (none) |
| PATCH | `/v1/somaerp/recipes/recipes/{id}` | `recipes.write` (drafts) / `recipes.publish` (status changes) | `.updated` / `.published` / `.archived` |
| DELETE | `/v1/somaerp/recipes/recipes/{id}` | `recipes.admin` | `somaerp.recipes.recipes.deleted` |

POST body — only creates `status=draft` rows. To publish, follow with PATCH `{"status":"active"}`.

```python
class RecipeCreate(BaseModel):
    product_id: UUID
    version: int           # service auto-assigns next if omitted; explicit allowed
    name: str
    yield_value: Decimal
    yield_unit_id: int
    expected_duration_min: int | None = None
    properties: dict = {}
    # nested optional convenience for one-shot create
    ingredients: list[RecipeIngredientLine] = []
    steps: list[RecipeStepLine] = []

class RecipeIngredientLine(BaseModel):
    raw_material_id: UUID
    quantity: Decimal
    unit_id: int
    is_optional: bool = False
    notes: str | None = None
    display_order: int = 0

class RecipeStepLine(BaseModel):
    step_number: int
    step_kind_id: int
    name: str
    instructions: str | None = None
    expected_duration_min: int | None = None
    equipment: str | None = None
```

PATCH state transitions:
- `draft → active` requires `recipes.publish` scope. Service auto-archives the prior active recipe for the same `product_id` (emits `.archived` for the prior). Sets `published_at`.
- `active → archived` requires `recipes.publish` scope. Sets `archived_at`. Returns 422 if any in_progress production batch references this recipe.
- `draft → archived` allowed (rejected draft).
- All other transitions return 409 `INVALID_STATE_TRANSITION`.

PATCH on field updates (name, yield, properties) only allowed while status=draft. Returns 409 `IMMUTABLE_FIELD` if mutating an active or archived recipe.

Response: row from `v_recipes` with embedded `ingredients` and `steps` arrays.

### Recipe ingredients

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/recipes/recipes/{recipe_id}/ingredients` | `recipes.read` | (none) |
| POST | `/v1/somaerp/recipes/recipes/{recipe_id}/ingredients` | `recipes.write` | `somaerp.recipes.ingredients.added` |
| PATCH | `/v1/somaerp/recipes/recipes/{recipe_id}/ingredients/{id}` | `recipes.write` | `somaerp.recipes.ingredients.updated` |
| DELETE | `/v1/somaerp/recipes/recipes/{recipe_id}/ingredients/{id}` | `recipes.write` | `somaerp.recipes.ingredients.removed` |

All only allowed when recipe `status=draft`.

### Recipe steps

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/recipes/recipes/{recipe_id}/steps` | `recipes.read` | (none) |
| POST | `/v1/somaerp/recipes/recipes/{recipe_id}/steps` | `recipes.write` | `somaerp.recipes.steps.added` |
| PATCH | `/v1/somaerp/recipes/recipes/{recipe_id}/steps/{id}` | `recipes.write` | `somaerp.recipes.steps.updated` |
| DELETE | `/v1/somaerp/recipes/recipes/{recipe_id}/steps/{id}` | `recipes.write` | `somaerp.recipes.steps.removed` |

All only allowed when recipe `status=draft`.

### Kitchen recipe overrides

| Method | Path | Scope | Audit key |
|---|---|---|---|
| GET | `/v1/somaerp/recipes/kitchen-overrides` | `recipes.read` | (none) |
| POST | `/v1/somaerp/recipes/kitchen-overrides` | `recipes.publish` | `somaerp.recipes.kitchen_override.applied` |
| DELETE | `/v1/somaerp/recipes/kitchen-overrides/{kitchen_id}/{base_recipe_id}/{effective_from}` | `recipes.publish` | `somaerp.recipes.kitchen_override.removed` |

Per ADR-004, `lnk_kitchen_recipe_overrides` is immutable; "removal" is a tombstone insert. The DELETE endpoint is a convenience that performs the tombstone insert with `effective_from = today`.

POST body:
```python
class KitchenOverrideCreate(BaseModel):
    kitchen_id: UUID
    base_recipe_id: UUID
    override_recipe_id: UUID
    effective_from: date
```

Service validates: `base_recipe_id` and `override_recipe_id` are both `status=active` for the same `product_id`; `kitchen_id` is active.

### Active recipe lookup (read helper)

| Method | Path | Scope | Notes |
|---|---|---|---|
| GET | `/v1/somaerp/recipes/active` | `recipes.read` | Query: `kitchen_id`, `product_id`. Returns the kitchen-override-aware active recipe (single row from `v_kitchen_active_recipe`). Used by production planner. |

This is a read; not a new entity. Could alternatively be a query param on the recipes list (`?for_kitchen_id=...&product_id=...&active_only=true`); chose a dedicated path because the resolution logic is non-trivial and centralizing it in service.py is clearer.

## Filter parameters

| Param | Endpoints | Notes |
|---|---|---|
| `product_id` | recipes list | |
| `status` | recipes list | comma list |
| `version` | recipes list | exact match |
| `q` | recipes list | name ILIKE |
| `kitchen_id` | kitchen-overrides list | |
| `base_recipe_id` | kitchen-overrides list | |
| `effective_on` | kitchen-overrides list | ISO date — returns rows current as of |

Standard `limit`, `cursor`, `sort`, `include_deleted`.

## Bulk operations

POST recipes accepts body array (tenant bootstrap). Each recipe may include nested `ingredients` and `steps`. Idempotency-Key recommended.

PATCH bulk allowed for ingredients (operator reorders/edits multiple lines while drafting) — body `[{id, ...patch}, ...]`.

## Cross-layer behaviors

- POST recipe validates `product_id` exists in catalog for same tenant.
- POST/PATCH recipe ingredient validates `raw_material_id` exists in raw_materials for same tenant.
- PATCH `status: active → archived` blocks if any `fct_production_batches` row with that `recipe_id` has `status='in_progress'`.
- POST kitchen-override blocks if `base_recipe_id` is not active or `override_recipe_id` is not active.
- DELETE recipe (soft) blocks if recipe is currently active or referenced by any non-cancelled production batch (planned/in_progress).

## Audit scope

| Endpoint | Additional scope |
|---|---|
| Recipe POST | `entity_kind="recipes.recipe"`, `properties={product_id, version, status:"draft"}` |
| Recipe PATCH publish | `properties={prior_active_recipe_id, product_id}` |
| Ingredient/step add/remove | `entity_kind="recipes.{ingredient|step}"`, `properties={recipe_id}` |
| Kitchen override applied | `entity_kind="recipes.kitchen_override"`, `properties={kitchen_id, base_recipe_id, override_recipe_id, effective_from}` |

Per audit-scope rule, every event carries the four-tuple plus the above. Setup-mode bootstrap of recipes (Soma Delights initial Green Morning v1) emits with `category=setup`.
