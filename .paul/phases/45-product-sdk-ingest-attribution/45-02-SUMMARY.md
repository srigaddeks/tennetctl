# Plan 45-02 — SUMMARY

**Phase:** 45 — Product SDK + Ingest + Attribution
**Plan:** 02 — Browser SDK + identify path + visitor detail page
**Status:** APPLY complete. SDK npm install + integration test deferred to operator.
**Date:** 2026-04-19

## What was built

### `@tennetctl/browser` (new package at `sdks/browser/`)

- `package.json` — AGPL-3, ES module, esbuild bundle to `dist/`, target ES2018, vitest test runner
- `tsconfig.json` — strict, noUncheckedIndexedAccess, DOM lib
- `src/index.ts` — full SDK (~360 lines): init/track/identify/alias/reset/flush, anonymous-first cookie + localStorage fallback, batched POST /v1/track, sendBeacon flush on unload, auto page_view (init + history pushState/popstate intercept), DNT respect, opt-in/out PII hash (email + phone via fast non-cryptographic fingerprint), parseUtm helper, fetchImpl injection for testing, `_internal` test hooks (queue inspect, opts, reset)
- `src/index.test.ts` — vitest suite (20+ tests across init, track, identify, alias, DNT, flush, PII hashing, parseUtm)
- Standalone typecheck of `src/index.ts` clean (test file needs `npm install` for vitest types)

### Backend identify path

- `repository.py`: added `set_visitor_user_id`, `add_visitor_alias`
- `service.py`: added `identify_visitor` and `add_alias` standalone helpers + inlined identify-on-ingest behavior in `ingest_batch` (when an event has `kind=identify` with `properties.user_id`, the service mutates the visitor row; same for `kind=alias` with `properties.alias_anonymous_id`)
- No new node introduced — identify rides through the existing `product_ops.events.ingest` node via the kind switch. Keeps API surface minimal per ADR-026.

### `GET /v1/product-visitors/{visitor_id}`

- New route in `routes.py` returning visitor + last touch + linked aliases. Workspace authz guard reuses session.workspace_id pattern from list endpoint.

### Frontend visitor detail page

- `frontend/src/types/api.ts`: added `ProductVisitorAlias`, `ProductVisitorDetail`
- `frontend/src/features/product-ops/hooks/use-product-events.ts`: added `useProductVisitor`
- `frontend/src/app/(dashboard)/product/visitors/[visitor_id]/page.tsx`: 4-card layout (identity, first touch, last touch, aliases). Uses Next.js 15 `use(params)` for the dynamic route param.
- Visitor IDs in `/product` event table are now clickable → navigate to detail page.

## Verification

| Check | Result |
|---|---|
| Backend imports clean | ✅ |
| Standalone tsc on `sdks/browser/src/index.ts` | ✅ |
| Frontend `npx tsc --noEmit` (whole project) | ✅ |
| Pyright on backend product_ops files | ✅ (datetime.utcnow → timezone.utc fixed) |
| `npm install && npm test` in sdks/browser | ⚠ DEFERRED — operator runs locally |
| Live identify→merge end-to-end | ⚠ DEFERRED — needs Postgres + vault project key |

## Files

- New: 5 (package.json, tsconfig.json, src/index.ts, src/index.test.ts, visitor page)
- Modified: 4 (backend repository.py, service.py, routes.py; frontend types/hook/page)
- Total new lines: ~1,100

## Deferred to 45-03

Server-side `.product.track()` namespace (Python + TS SDKs), UTM dashboard.
