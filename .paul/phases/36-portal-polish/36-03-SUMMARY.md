# Phase 36 Plan 03 — SUMMARY

**Plan:** 36-03 Catalog browser enhancement
**Status:** ✅ Complete
**Date:** 2026-04-18

## What shipped
- Two new backend endpoints on the read-only catalog router:
  - `GET /v1/catalog/features` — feature_key, feature_number, module, sub_feature_count, node_count
  - `GET /v1/catalog/sub-features` — sub_feature_key, sub_feature_number, feature_key, module, node_count
- Frontend types + hooks (`useCatalogFeatures`, `useCatalogSubFeatures`)
- `/catalog` page — Features table (top) + Sub-features table (bottom), link through to `/nodes` for drill-down
- Nav entry: new "Catalog" feature in sidebar with an "Inventory" sub-link

## Files
- **Modified**
  - `backend/01_catalog/routes.py` — added `_FEATURES_SQL`, `_SUB_FEATURES_SQL`, two handlers
  - `frontend/src/types/api.ts` — `CatalogFeature`, `CatalogSubFeature`
  - `frontend/src/config/features.ts` — nav entry for Catalog feature
- **Created**
  - `frontend/src/features/catalog/hooks/use-catalog.ts`
  - `frontend/src/app/(dashboard)/catalog/page.tsx`

## Verification
- `importlib.import_module("backend.01_catalog.routes")` — clean
- `npx tsc --noEmit` — clean
- `npx next build` — success, `/catalog` registered as static

## Decisions
- Kept `/nodes` untouched — it's already a high-quality drill-down surface. `/catalog` is the inventory/rollup; `/nodes` is the deep-dive. Cross-link is sufficient.
- Two endpoints rather than one with grouping. Reason: `/features` stays small (one row per feature) and can be cached separately when Phase 37 (catalog hot-reload) adds manifest-change invalidation. Merging them would force the whole payload to refresh on any sub-feature change.
- SQL uses `COUNT(...) FILTER (WHERE ... IS NULL)` over `LEFT JOIN` to preserve features/sub-features with zero nodes — operationally important for newly scaffolded modules.
- No separate "features/[key]" detail route — `/nodes?feature=…` already serves that use case via its filter.

## Deferred
- Feature manifest YAML viewer (future; would need /catalog/features/{key}/manifest endpoint)
- Sub-feature detail page showing owning service/repo paths
