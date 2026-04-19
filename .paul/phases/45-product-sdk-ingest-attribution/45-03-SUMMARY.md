# Plan 45-03 — SUMMARY

**Phase:** 45 — Product SDK + Ingest + Attribution
**Plan:** 03 — Server-side SDK + UTM dashboard
**Status:** APPLY complete. Plan 45 (foundation) is now fully shipped.
**Date:** 2026-04-19

## What was built

### Server-side SDKs

**Python (`@tennetctl/sdk` Python — `sdk/python/tennetctl/`):**
- New `product_ops.py` module — `ProductOps` class with `.track()`, `.track_batch()`, `.identify()`, `.list_events()`, `.get_visitor()`
- Wired into `client.py` — accessible via `client.product`
- Server-side calls don't auto-hash PII (caller's responsibility for backend contract)

**TypeScript (`@tennetctl/sdk` — `sdks/typescript/src/index.ts`):**
- Appended `ProductOpsClient` class with same shape: `.track()`, `.identify()`, `.trackBatch()`
- Standalone class (separate from FlagsClient), exported alongside

### UTM aggregate endpoint

- `repository.py`: added `utm_campaign_aggregate(workspace_id, days)` — single CTE query: visitors per (utm_source, utm_campaign) joined to conversions (events with metadata->>'is_conversion'='true'). Date-window WHERE enables partition pruning.
- `routes.py`: `GET /v1/product-events/utm-aggregate?workspace_id=…&days=30` returning rows + days
- `feature.manifest.yaml`: registered the new route + the visitor-detail route from 45-02

### UTM dashboard frontend

- `frontend/src/types/api.ts`: `UtmAggregateRow`, `UtmAggregateResponse`
- `frontend/src/features/product-ops/hooks/use-product-events.ts`: `useUtmAggregate(workspaceId, days)`
- `frontend/src/app/(dashboard)/product/utm/page.tsx`: window selector (1/7/30/90 days), table (source, campaign, visitors, conversions, CVR%)
- Sidebar gets new entry "UTM Campaigns" → `/product/utm`

## Verification

- Backend imports clean ✅
- Manifest validates against catalog parser (4 routes registered) ✅
- Frontend `npx tsc --noEmit` clean ✅
- Live integration tests deferred to operator (need Postgres + traffic for UTM aggregate to return rows)

## Files

- New: 3 (product_ops.py, UTM page.tsx, this SUMMARY)
- Modified: 8 (client.py, TS index.ts, repository.py, routes.py, feature.manifest.yaml, types/api.ts, use-product-events.ts, features.ts)
- Total new lines: ~600

## Phase 45 closeout

| Plan | Concern | Status |
|---|---|---|
| 45-01 | Schema + ingest backend + admin tail | ✅ |
| 45-02 | Browser SDK + identify/alias + visitor detail | ✅ |
| 45-03 | Server SDK + UTM dashboard | ✅ |

Phase 45 is complete. Next: Phase 46 (link shortener).
