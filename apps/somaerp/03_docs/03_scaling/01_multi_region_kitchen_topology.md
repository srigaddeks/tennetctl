# Multi-Region, Multi-Kitchen Topology (Within One Tenant)

> A tenant in somaerp is one workspace. A workspace can run N kitchens across M regions. This doc specifies the rules.

## Hierarchy

```
tenant (= tennetctl workspace_id)
  └── region          (dim_regions — country/state level, e.g. India / Telangana)
        └── location  (fct_locations — city/area, e.g. Hyderabad / KPHB)
              └── kitchen      (fct_kitchens — physical facility, e.g. KPHB Home Kitchen)
                    └── service_zone (fct_service_zones — delivery area served by this kitchen)
```

Full schema lives in `../01_data_model/01_geography.md` (forward reference — Task 2 ships it).

Soma Delights at Stage 1 has exactly one of each: India / Hyderabad / KPHB Home Kitchen / KPHB Colony service zone. By Stage 3 (`brand-roadmap-vision.md`) the same tenant runs ~3 kitchens across the Kukatpally–Miyapur–Chandanagar corridor. By Year 2+ a Bangalore expansion could add a second region.

## Time zones — UTC in storage, kitchen-local in display

- Every timestamp column (`created_at`, `started_at`, `completed_at`, `valid_from`, `valid_to`, `run_date`, `time_window_start`) is `TIMESTAMP WITH TIME ZONE` stored as UTC.
- `fct_kitchens.timezone` carries the IANA TZ string for the kitchen (e.g. `Asia/Kolkata`).
- The frontend renders kitchen-scoped times in `fct_kitchens.timezone`. The repo never converts; it always returns UTC.
- "Today's batches at KPHB" is computed by:
  ```text
  date_trunc('day', batch.started_at AT TIME ZONE kitchen.timezone) =
  date_trunc('day', NOW() AT TIME ZONE kitchen.timezone)
  ```

A future Bangalore kitchen on the same tenant uses `Asia/Kolkata` too, but if a tenant ever opens an EU kitchen it gets `Europe/Berlin` and "today's batches" still works without code change.

## Currency — per-region currency code on every monetary column

- Every monetary column (`unit_cost`, `total_cost`, `price`, `cogs`) is paired with a `currency_code CHAR(3)` column (ISO 4217).
- `fct_locations.default_currency_code` is the fallback when the writer doesn't pin a currency explicitly.
- somaerp does not do currency conversion in v0.9.0. A multi-currency tenant is supported in storage; reporting that aggregates across currencies is deferred to v1.0.
- For Soma Delights every monetary row carries `currency_code = 'INR'`.

### Multi-currency price tables

When a tenant ships product priced in multiple currencies (a Bangalore tenant pricing in INR for India and AED for a Dubai pop-up), `dim_subscription_plans` carries `(plan_id, currency_code, price)` as a composite — one plan, multiple price rows. The same shape applies to `fct_products.list_price` if it ever needs multi-currency. Out of scope for the Soma Delights launch.

## Customer-to-kitchen routing

Subscriptions belong to customers; customers belong to a location; the location maps to one or more service zones; each service zone is owned by exactly one kitchen.

```text
customer.location_id
  → fct_service_zones (location coverage match)
    → fct_service_zones.kitchen_id (the serving kitchen)
```

### Routing rules

1. Default: a customer's serving kitchen is `service_zone.kitchen_id` for the zone covering their location.
2. Tie-break: if the customer's location is covered by multiple zones (overlap during expansion), the lower-`sequence`-numbered zone wins. Tenants edit `fct_service_zones.sequence` to control which kitchen takes priority.
3. Explicit override: `fct_subscriptions.kitchen_override_id` (nullable). When set, this kitchen serves the subscription regardless of the customer's zone. Used for VIP customers, household members in two zones, or temporary handoffs during a kitchen outage.
4. Production planning queries the subscription's effective kitchen (`COALESCE(kitchen_override_id, derived_from_zone)`) to decide which kitchen produces tomorrow's batch for that customer.

## Recipe variation per kitchen

Per ADR-004, recipes are versioned at the tenant level, with per-kitchen overrides via `lnk_kitchen_recipe_overrides (kitchen_id, base_recipe_id, override_recipe_id)`. The override resolves at production-batch creation time:

```text
resolve_recipe_for(kitchen_id, product_id) -> recipe_id:
    base = fct_recipes WHERE product_id=? AND status='active'
    override = lnk_kitchen_recipe_overrides WHERE kitchen_id=? AND base_recipe_id=base
    return override.override_recipe_id if override exists else base.id
```

The Hyderabad KPHB kitchen and a hypothetical Bangalore kitchen can serve the same product with kitchen-specific recipe variants (different turmeric source, different cucumber:spinach ratio for local taste) without forking the catalog. Soma Delights at Stage 1 has zero overrides; the override table is empty.

## Per-region capacity

`fct_kitchen_capacity` (per ADR-003) is per (kitchen × product_line × time_window × valid_period). A multi-region tenant gets per-region capacity automatically because each kitchen's capacity rows belong to that kitchen, and each kitchen belongs to a location which belongs to a region. No region-level capacity rollup is stored; if needed it is computed by summing kitchen capacity within a region.

Detailed capacity model in `02_capacity_planning_model.md`.

## Cross-region replication strategy (deferred to v1.0)

Out of scope for v0.9.0. Documented intent so v0.9.0 schema decisions don't preclude it:

- Stage A (read-local, write-global): one Postgres primary, one read replica per region, somaerp backends in each region read locally and write to the primary. Asynchronous lag (a few seconds) is acceptable for the read paths somaerp serves (today's batches, current inventory, route lists).
- Stage B (write-local, eventual reconcile): each region writes to its local cluster; an event bus reconciles to a global warehouse. Out of scope until a tenant has a regulatory reason to write-local.
- Stage C (per-region per-tenant cluster): the Stage B shape collapsed to one cluster per tenant per region for enterprise isolation.

None of these require schema changes from v0.9.0. The `tenant_id`-leading composite indexes plus the `evt_*` append-only model are the enabling primitives.

## What this means for Soma Delights at Stage 1

- 1 region (`IN`), 1 location (Hyderabad), 1 kitchen (KPHB Home), 1 service zone (KPHB Colony).
- Single timezone `Asia/Kolkata`, single currency `INR`.
- Zero kitchen overrides, zero overlapping zones, zero cross-region complexity.
- Stage 2-3 expansion (Miyapur, Chandanagar — see `delivery-routes.md`) adds rows to `fct_service_zones` and possibly a second `fct_kitchens` row. No schema change.
- Bangalore expansion (Year 2+) adds a second `fct_locations` row and possibly a second `dim_regions` row. No schema change.

## Related documents

- `00_multi_tenant_strategy.md` — inter-tenant scaling
- `02_capacity_planning_model.md` — kitchen capacity in detail
- `03_data_residency_compliance.md` — region selection drives residency
- `../00_main/08_decisions/003_multi_kitchen_capacity_model.md`
- `../00_main/08_decisions/004_recipe_versioning_and_kitchen_overrides.md`
- `../01_data_model/01_geography.md` (forward reference — Task 2)
