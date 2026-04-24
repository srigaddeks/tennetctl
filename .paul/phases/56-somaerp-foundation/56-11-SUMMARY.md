---
phase: 56-somaerp-foundation
plan: 11
subsystem: customers_subscriptions
completed: 2026-04-24
---

# Plan 56-11: Customers + Subscription Plans + Subscriptions — UNIFIED

## Schema
- dim_subscription_frequencies (7 seeded: daily/5x_week/3x_week/weekly/biweekly/monthly/custom with deliveries_per_week factor for revenue compute)
- fct_customers (status state machine prospect/active/paused/churned/blocked)
- fct_subscription_plans (status draft/active/archived)
- dtl_subscription_plan_items (product + optional variant + qty_per_delivery)
- fct_subscriptions (status machine active/paused/cancelled/ended; transitions auto-emit evt_subscription_events)
- evt_subscription_events (append-only: started/paused/resumed/cancelled/ended/plan_changed)
- Views: v_customers (join location + COUNT active subs), v_subscription_plans (join freq + item count), v_subscription_plan_items, v_subscriptions (join all + days_active)

## Endpoints
Under /v1/somaerp/customers/* + /v1/somaerp/subscriptions/*: 21 total.

## Seed
ZERO customers/plans/subs. Only universal dim_subscription_frequencies.

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
