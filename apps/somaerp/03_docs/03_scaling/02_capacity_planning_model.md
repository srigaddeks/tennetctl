# Capacity Planning Model

> Deep dive on `fct_kitchen_capacity` — why it is time-windowed, why it is versioned, and how the production planner uses it.

## The shape

Per ADR-003, `fct_kitchen_capacity` is a single source of truth for "what can this kitchen produce, of what, when, between which dates":

| Column | Type | Purpose |
| --- | --- | --- |
| `id` | UUID v7 | PK |
| `tenant_id` | UUID NOT NULL | tennetctl `workspace_id` |
| `kitchen_id` | UUID NOT NULL | FK → `fct_kitchens.id` |
| `product_line_id` | UUID NOT NULL | FK → `fct_product_lines.id` |
| `capacity_value` | NUMERIC(12,2) NOT NULL | how many units |
| `capacity_unit_id` | SMALLINT NOT NULL | FK → `dim_units_of_measure.id` (bottles, liters, kg) |
| `time_window_start` | TIME NOT NULL | daily window start, kitchen-local |
| `time_window_end` | TIME NOT NULL | daily window end, kitchen-local |
| `valid_from` | DATE NOT NULL | first day this row applies |
| `valid_to` | DATE NULL | last day; NULL = open-ended (currently active) |
| `properties` | JSONB NOT NULL DEFAULT '{}' | tenant-specific extension |
| `created_at` / `updated_at` / `deleted_at` | timestamps | standard |

Full schema column list lives in `../01_data_model/01_geography.md` (forward reference).

A single `(tenant_id, kitchen_id, product_line_id, time_window_start, time_window_end)` partial unique index where `valid_to IS NULL` enforces "exactly one open-ended row per kitchen × product_line × window."

## Why time-windowed

A kitchen does different things at different times of day. Soma Delights at Stage 2 (`operations-model.md`):

- Cold-pressed bottles, 4:00–8:00 AM: ~30–50 bottles. Equipment: cold-press juicer, bottling station.
- (Future) Fermented drinks, 6:00–10:00 AM: ~50 units. Equipment: fermentation jars (different equipment, overlapping time).
- (Future) Wellness shots, 8:00–10:00 AM: ~40 shots. Same press, different SKU recipe.

A single integer `kitchen.capacity` would model none of this. Two rows in `fct_kitchen_capacity` model the cold-press + fermented overlap: same kitchen, different product_line, overlapping windows. Equipment-conflict detection (can both windows really run at once?) is a separate planning concern handled by the production scheduler — capacity rows describe **available** capacity per product line; they do not enforce equipment exclusivity. That logic stays in service-layer business rules.

## Why valid_from / valid_to

Capacity changes over time. Examples from Soma Delights' staged growth (`operations-model.md` Stage table):

- Stage 1 (today): 30 bottles/day cold-pressed, 4–8 AM.
- Stage 2 (after second juicer + part-time helper): 90 bottles/day, 4–8 AM.
- Stage 3 (rented production unit + 2 helpers): 250 bottles/day, 4–9 AM.

If `fct_kitchen_capacity` were mutable, the Stage 1→Stage 2 transition would destroy historical "what was capacity on 2026-04-15?" The append-shape with `valid_from` / `valid_to` keeps history queryable: the Stage 1 row gets `valid_to = '2026-06-30'`, a new Stage 2 row is inserted with `valid_from = '2026-07-01'`, and capacity yield analytics ("we ran at 85% of capacity in May") still produce the right denominator.

Future planning works identically: a planned Stage 3 expansion goes in today as a row with `valid_from = '2026-09-01'` and the production planner already knows to expect higher capacity from that date. No retroactive insert needed.

## Mutating capacity (the two-step service operation)

Direct UPDATE on a capacity row is forbidden. The service layer wraps the change as one transaction:

```text
service.update_capacity(kitchen_id, product_line_id, time_window, new_value, effective_from):
    # 1. Close the open-ended row, if any
    UPDATE fct_kitchen_capacity
       SET valid_to = effective_from - 1 day, updated_at = NOW()
     WHERE tenant_id = ctx.workspace_id
       AND kitchen_id = ?
       AND product_line_id = ?
       AND time_window_start = ?
       AND time_window_end = ?
       AND valid_to IS NULL
    # 2. Insert the new open-ended row
    INSERT INTO fct_kitchen_capacity (
        id, tenant_id, kitchen_id, product_line_id,
        capacity_value, capacity_unit_id,
        time_window_start, time_window_end,
        valid_from, valid_to, properties
    ) VALUES (uuid7(), ctx.workspace_id, ..., effective_from, NULL, '{}')
    # 3. Emit audit
    audit.events.emit('somaerp.geography.kitchen_capacity.changed', {
        kitchen_id, product_line_id, old_value, new_value, effective_from
    })
```

## Reading capacity (the active-row view)

`v_kitchen_current_capacity` exposes the currently-valid row per (kitchen, product_line, time_window):

```text
SELECT *
  FROM fct_kitchen_capacity
 WHERE tenant_id = current_setting('somaerp.workspace_id')::uuid
   AND CURRENT_DATE BETWEEN valid_from AND COALESCE(valid_to, 'infinity')
```

Most application reads use this view. Historical/future planning reads the raw `fct_kitchen_capacity` table with an explicit date filter.

## Capacity-vs-demand check (the production planner)

When the planner schedules tomorrow's production, it asks: "for each (kitchen, product_line) we are scheduling, is the demand within the active capacity for that day's window?"

```text
plan_tomorrow(kitchen_id, target_date):
    # Demand = sum of subscription line items mapped to this kitchen and date
    demand = SELECT product_line_id, SUM(qty) AS demanded_units
               FROM v_subscription_demand_for_date(kitchen_id, target_date)
              GROUP BY product_line_id

    # Capacity = active row per product_line for target_date
    capacity = SELECT product_line_id, time_window_start, time_window_end,
                      capacity_value
                 FROM fct_kitchen_capacity
                WHERE tenant_id = ctx.workspace_id
                  AND kitchen_id = ?
                  AND target_date BETWEEN valid_from AND COALESCE(valid_to, 'infinity')

    # For each demanded product_line, check capacity ≥ demand
    for d in demand:
        c = capacity.get(d.product_line_id)
        if c is None or c.capacity_value < d.demanded_units:
            yield CapacityShortfall(d, c)
```

Shortfalls are returned to the operator as a planning warning, not a hard block — the operator can decide to overproduce (push the kitchen) or under-serve (skip some subscribers, refund). The planner's job is to make the trade-off visible, not to make it.

## Capacity utilization analytics

```text
SELECT product_line_id,
       date_trunc('week', batch.run_date) AS week,
       SUM(batch.actual_qty)::numeric / SUM(capacity.capacity_value) AS utilization_pct
  FROM fct_production_batches batch
  JOIN fct_kitchen_capacity capacity
    ON capacity.kitchen_id = batch.kitchen_id
   AND capacity.product_line_id = batch.product_line_id
   AND batch.run_date BETWEEN capacity.valid_from AND COALESCE(capacity.valid_to, 'infinity')
 WHERE batch.tenant_id = ctx.workspace_id
   AND batch.kitchen_id = ?
 GROUP BY product_line_id, week
```

This query is correct across capacity changes because each batch is joined to the capacity row that was valid on that batch's date. A capacity expansion mid-quarter does not retroactively change historical utilization numbers.

## What capacity does NOT model (intentionally)

- **Equipment-level conflicts.** Two rows can claim overlapping time windows; whether the kitchen actually has the equipment to run both is a service-layer rule, not a schema rule. Future enhancement: `dim_equipment` + `lnk_capacity_equipment` to declare which capacity rows share equipment.
- **Staff scheduling.** Who is at the kitchen during a window is HR; out of v0.9.0 scope.
- **Day-of-week variation.** All capacity rows are daily. A "Sunday off" rule is modeled by inserting a row with `valid_from / valid_to` that excludes Sundays — clumsy, deferred. v1.0 may add `dim_weekday_masks` to capacity rows.
- **Per-batch yield variation.** Capacity is the planning ceiling. Actual yield per batch is in `fct_production_batches.actual_qty` and can exceed capacity if the operator pushed it; `actual_qty > capacity_value` is a flag for analytics, not an error.

## Soma Delights seed example (Stage 1)

Per `operations-model.md` Stage 1 timeline + `daily-production-tracker.md`:

```text
Row: KPHB Home Kitchen, Cold-Pressed Drinks, 30 bottles, time 04:00-08:00 IST,
     valid_from 2026-04-24, valid_to NULL
```

When the Stage 2 transition happens, the service layer closes this row at the day before the transition and inserts:

```text
Row: KPHB Home Kitchen, Cold-Pressed Drinks, 90 bottles, time 04:00-08:00 IST,
     valid_from 2026-07-01, valid_to NULL
```

Detailed seed in `../05_tenants/01_somadelights_tenant_config.md`.

## Related documents

- `../00_main/08_decisions/003_multi_kitchen_capacity_model.md`
- `01_multi_region_kitchen_topology.md`
- `../01_data_model/01_geography.md` (forward reference — Task 2)
- `../01_data_model/07_production.md` (forward reference — Task 2)
- `99_business_refs/somadelights/05-operations/operations-model.md`
- `99_business_refs/somadelights/05-operations/daily-production-tracker.md`
