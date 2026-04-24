# ADR-004: Recipe versioning + per-kitchen overrides
Status: ACCEPTED
Date: 2026-04-24

## Context

Recipes change. A cold-pressed Green Morning recipe in v1 might call for 200g spinach + 100g cucumber; v2 (after taste testing) might call for 180g spinach + 120g cucumber. FSSAI traceability requires that any production batch can be tied back to the exact recipe version that produced it; "we changed the recipe last Tuesday" is not a defensible answer to a complaint about a Monday batch. Multi-kitchen tenants also need per-kitchen overrides: a Hyderabad kitchen might use turmeric from Erode while a Bangalore kitchen uses turmeric from Mysore — same recipe key, different ingredient sourcing, possibly different quantities. The decision is how to model versioning and overrides without exploding the schema.

## Decision

**Recipes are first-class versioned entities. `fct_recipes (id, tenant_id, product_id, version, status, ...)` carries one row per recipe version with `status` ∈ `{draft, active, archived}`. Only one `active` row per (tenant_id, product_id) at any time. `fct_production_batches.recipe_id` references the EXACT recipe row (and therefore the exact version) used. Per-kitchen variation is modeled via `lnk_kitchen_recipe_overrides (id, tenant_id, kitchen_id, base_recipe_id, override_recipe_id, properties JSONB, ...)` — a join row that says "for this kitchen, when the active recipe for this product would otherwise be base_recipe_id, use override_recipe_id instead."** Recipe rows are never mutated after `status = active`; changing a recipe means inserting a new row at `version + 1` with `status = draft`, then atomically promoting it to `active` (and demoting the previous active row to `archived`).

## Consequences

- **Easier:** every batch has an unambiguous, immutable, FSSAI-defensible recipe pointer.
- **Easier:** historical analytics (yield % under recipe v1 vs v2) work directly.
- **Easier:** per-kitchen overrides are explicit and auditable; the override link is a real row, not a fork of the recipe table.
- **Harder:** "the recipe" is no longer a single row but a (product_id, status=active) lookup, optionally redirected through `lnk_kitchen_recipe_overrides`. The service layer encapsulates this resolution as `resolve_recipe_for(kitchen_id, product_id) -> recipe_id`.
- **Harder:** recipe-mutation is a multi-step transaction (insert new draft → promote to active → demote previous active). The service layer wraps it.
- **Constrains:** ADR-005 (QC checkpoints reference recipe steps and must therefore reference a recipe version); ADR-007 (production batches pin recipe_id at creation time); the recipes data model layer (`01_data_model/03_recipes.md`); the recipes API design (`02_api_design/03_recipes.md`).

## Alternatives Considered

- **Mutable recipes, no versioning.** Simplest. Rejected: breaks FSSAI traceability and historical analytics; "what did the recipe look like on 2026-03-15?" becomes unanswerable.
- **Versioning via `dtl_recipe_versions` events.** Models versions as event log. Rejected: every read of "the active recipe" becomes an event-replay query; recipes are the wrong shape for an event log.
- **Per-kitchen forks of the entire recipe.** Copy the recipe per kitchen. Rejected: explodes row counts, breaks "this is one recipe with two kitchen variations" semantics, makes promoting an upstream change to all kitchens manual and error-prone.
- **Override stored as `properties JSONB` on `fct_kitchens`.** Avoids a new table. Rejected: kills FK integrity, kills indexability, hides the override from queries.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `99_business_refs/somadelights/03-product/recipe-standardization.md`
- `99_business_refs/somadelights/09-execution/compliance-food-safety.md`
- `apps/somaerp/03_docs/00_main/08_decisions/005_qc_checkpoint_model.md`
- `apps/somaerp/03_docs/00_main/08_decisions/007_production_batch_lifecycle.md`
