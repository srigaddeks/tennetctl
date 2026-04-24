---
phase: 56-somaerp-foundation
plan: 13
subsystem: reporting
completed: 2026-04-24
---

# Plan 56-13: Reporting Views — UNIFIED (final plan of Phase 56)

**7 views only. ZERO new tables. Cross-layer rollups for dashboards.**

## Views
- v_dashboard_today (today's active/completed counts across batches + runs + deliveries + subscriptions)
- v_batch_yield_daily + v_batch_cogs_daily (grouped time-series)
- v_inventory_reorder_alerts (current_qty vs raw_material.properties.reorder_point_qty with critical/low/ok levels + primary supplier)
- v_procurement_spend_monthly
- v_subscription_revenue_projected (monthly + weekly + daily from plan.price × frequency.deliveries_per_week × 4.333)
- v_fssai_compliance_batches (per batch with lot_numbers ARRAY + qc_results JSONB aggregated)

## Endpoints
7 under /v1/somaerp/reports/*. CSV download on /compliance/batches?format=csv returns text/csv with Content-Disposition attachment.

## Frontend
/reports landing (6 cards) + individual pages with simple div-bar visualizations (no chart lib per simplicity rule).

## Seed
NONE. Views only.

## Loop
PLAN ✓ APPLY ✓ UNIFY ✓ 2026-04-24
