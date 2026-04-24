# ADR-003: Multi-kitchen capacity model — (kitchen × product_line × time_window) with valid_from/valid_to history
Status: ACCEPTED
Date: 2026-04-24

## Context

somaerp must support a tenant running N kitchens across M regions, with each kitchen producing one or more product lines under different time-window constraints. Soma Delights at home-kitchen stage runs ~30-50 cold-pressed bottles between 4-8 AM; the same physical kitchen might later run fermented drinks between 6-10 AM on different equipment. Capacity also changes over time (hire staff, upgrade equipment, expand to a commercial kitchen). The capacity model also drives the demand-vs-capacity check at production planning time. A single `kitchen_capacity` integer per kitchen is wrong on three axes: it ignores product-line variation, ignores time-window constraints, and ignores historical change.

## Decision

**Capacity is modeled as `fct_kitchen_capacity (id, tenant_id, kitchen_id, product_line_id, capacity_value, capacity_unit_id, time_window_start, time_window_end, valid_from, valid_to, properties JSONB, ...)`. Each row says: this kitchen can produce this much of this product line in this daily time window, valid between these dates.** Multiple rows per kitchen are normal: one row per (kitchen × product_line × time_window) tuple per validity period. Overlapping rows for the same (kitchen, product_line, time_window) are forbidden via a partial unique index keyed on (kitchen_id, product_line_id, time_window_start, time_window_end) where `valid_to IS NULL`. Historical capacity remains queryable by intersecting `valid_from / valid_to` ranges.

## Consequences

- **Easier:** demand-vs-capacity planning queries "what is the active capacity at KPHB Kitchen for Cold-Pressed Drinks in the 4-8 AM window on 2026-05-01?" with one indexed query.
- **Easier:** historical analytics (yield % vs capacity utilization over 6 months) work because old capacity rows are not destroyed when capacity changes.
- **Easier:** future planning works (insert a row with `valid_from = next_month` to model a planned capacity expansion) without breaking today's queries.
- **Harder:** mutating capacity is a two-step operation (close the old row by setting `valid_to`, insert a new row with `valid_from`). The service layer wraps this in a single function.
- **Harder:** queries that assume "one row per kitchen" must be rewritten; the v_kitchen_current_capacity view exposes the active row only.
- **Constrains:** the geography data model layer; the production planning workflow; the capacity planning scaling doc (`03_scaling/02_capacity_planning_model.md`).

## Alternatives Considered

- **One row per kitchen with a single capacity integer.** Simplest. Rejected: ignores product-line variation, time windows, and history.
- **Capacity per (kitchen × product) (not per product_line).** More granular. Rejected: explosion of rows (N products × M kitchens × T windows), and most product variation within a line shares the same capacity envelope (all cold-pressed bottles use the same press).
- **Capacity stored as JSONB on `fct_kitchens`.** Avoids a new table. Rejected: kills indexability, kills the validity history pattern.
- **No capacity model, free-form planning.** Defers the question. Rejected: production planning is a v0.9.0 driving workflow.

## References

- `~/.gstack/projects/srigaddeks-tennetctl/sri-feat-saas-build-design-20260424-111411.md`
- `99_business_refs/somadelights/05-operations/operations-model.md`
- `99_business_refs/somadelights/05-operations/daily-production-tracker.md`
- `apps/somaerp/03_docs/03_scaling/02_capacity_planning_model.md` (to be written in Task 3)
