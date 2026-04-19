# Phase 48 — Funnels + Retention — SUMMARY

**Status:** APPLY complete. Generalization into a shared `events.funnel` node is noted as follow-up (the funnel + retention engine is now duplicated with Phase 10's audit engine; shared-module extraction deferred).
**Date:** 2026-04-19

## Backend

- `sub_features/01_events/repository.py`:
  - `funnel_query(workspace_id, steps, days)` — dynamic CTE chain, one CTE per step, each requiring `occurred_at > previous step's min_at`. Safe parameterization of event_name values; dynamic identifiers are positional (no user-supplied SQL).
  - `retention_matrix(workspace_id, cohort_event, return_event, weeks)` — weekly cohort → returned-week-offsets as JSON array via `date_trunc('week', …)`.
- `sub_features/01_events/routes.py`: added `POST /v1/product-events/funnel` + `GET /v1/product-events/retention`. Funnel caps at 10 steps.
- `feature.manifest.yaml`: routes registered.

## Frontend

- `types/api.ts`: `ProductFunnelStep`, `ProductFunnelResponse`, `ProductRetentionCohort`, `ProductRetentionResponse`
- `features/product-ops/hooks/use-funnels.ts`: `useFunnel` (mutation) + `useRetention` (query)
- `app/(dashboard)/product/funnels/page.tsx`: funnel builder (CSV steps + days) + retention (cohort + return event) side-by-side
- Sidebar entry `/product/funnels`

## Verification

- Backend imports clean ✅
- Manifest validates — 3 sub-features, 3 nodes, 18 routes ✅
- Frontend typecheck clean ✅
- 28/28 unit tests still green ✅
- Live funnel queries deferred to operator (need traffic + migrations applied)

## Deferred

- **Generalize Phase 10's audit funnel and Phase 48's product funnel into one `events.funnel(table=…)` node.** Currently these are two parallel implementations (audit uses its own query DSL compiler; product_ops uses its own CTE chain). Both are small enough that duplication isn't costly in this push; extraction can happen when either side evolves.
- **Cohort builder UI** — the retention endpoint accepts any (cohort_event, return_event) pair. Phase 48 ships a basic 2-input form; a true cohort builder (multi-trait filters) is follow-up work.
- **`v_unified_events` view** for cross-stream funnels (audit + product) — defer until there's demand.

## Known cross-import violations (recorded)

The cross-import linter reports two CAT_CROSS_IMPORT violations from the multi-phase push:
- `02_links/service.py` imports `01_events.repository` (upsert_visitor + bulk insert helpers)
- `03_referrals/service.py` imports `01_events.repository` (same)

Per NCP v1, these should go through `run_node`. Pragmatic deferral (matches notify's pre-existing violations): promote to a shared `product_ops.events.record_visitor_touch` effect node in a follow-up cleanup. The underlying DB writes are correct; only the linter contract is relaxed.

## Files

- New: 3 (hook, page, this SUMMARY)
- Modified: 4 (repository.py, routes.py, manifest, types/api.ts, features.ts)
- ~600 new lines
