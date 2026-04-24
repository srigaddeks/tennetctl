---
phase: 56-somaerp-foundation
plan: 12
subsystem: delivery
completed: 2026-04-24
---

# Plan 56-12: Delivery Routes + Riders + Runs — UNIFIED

## Schema
- dim_rider_roles (5 seeded: owner/contractor/employee/partner/gig)
- fct_delivery_routes
- lnk_route_customers (IMMUTABLE; reorder = DELETE+INSERT in tx)
- fct_riders (user_id optional to tennetctl iam; validated via tennetctl_client if provided)
- fct_delivery_runs (mutable lifecycle: planned/in_transit/completed/cancelled; partial unique per route+date)
- dtl_delivery_stops (mutable: pending/delivered/missed/customer_unavailable/cancelled/rescheduled; photo_vault_key placeholder)
- Views: v_delivery_routes (+customer count), v_delivery_runs (+completion_pct), v_delivery_stops (+delay computed)

## Endpoints
Under /v1/somaerp/delivery/*: 3 sub-features across routes + riders + runs + today's board. Rider mobile UI on /runs/[id] (big Delivered/Missed buttons per stop).

## Seed
ZERO routes/riders/runs/stops. Only universal dim_rider_roles.

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
