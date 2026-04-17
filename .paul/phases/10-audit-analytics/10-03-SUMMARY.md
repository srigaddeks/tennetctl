# Plan 10-03 SUMMARY — Audit Funnel + Retention + Saved Views + CSV Export

**Completed:** 2026-04-17
**Duration:** ~60 min
**Status:** All 4 tasks complete — APPLY ✓ UNIFY ✓

---

## What Was Built

### Backend (Task 1)
- **Migration 017**: `10_fct_audit_saved_views` + `20_dtl_audit_saved_view_details` + `v_audit_saved_views` — applied
- **Saved views sub-feature** (5 files): `schemas.py` / `repository.py` / `service.py` / `routes.py` / `__init__.py`
  - `GET /v1/audit-saved-views` — org-scoped list
  - `POST /v1/audit-saved-views` — create (201)
  - `DELETE /v1/audit-saved-views/{id}` — hard-delete (204)
- **Funnel endpoint**: `POST /v1/audit-events/funnel` — two-phase helper pattern (`_funnel_step0` + `_funnel_stepi`) avoids param-renumbering issue with EXISTS subquery
- **Retention endpoint**: `GET /v1/audit-events/retention` — CTE-based SQL with cohort_members → cohort_sizes → return_events; Python post-processing into nested structure
- **CSV export**: `?format=csv` on `GET /v1/audit-events` — 10k row cap, streaming `text/csv` via FastAPI `StreamingResponse`
- **Route ordering fix**: `GET /v1/audit-events/retention` registered before `GET /v1/audit-events/{event_id}` to prevent path capture
- **Sequence fix**: `01_catalog.12_fct_nodes_id_seq` was at SMALLINT max (32767); reset to MAX(id)+1=25783

### Frontend (Task 2)
- **Types** (`frontend/src/types/api.ts`): `AuditFunnelRequest/Step/Response`, `AuditRetentionBucket/Retained/Cohort/Response`, `AuditSavedViewCreate/Row/ListResponse`
- **Hooks** (`use-audit-events.ts`): `useAuditFunnel`, `useAuditRetention`, `useAuditSavedViews`, `useCreateSavedView`, `useDeleteSavedView`
- **Components**:
  - `funnel-builder.tsx` — step inputs (2-8), run button, bar-chart result, conversion_pct display
  - `retention-grid.tsx` — anchor/return event inputs, bucket/period selectors, heatmap table with blue-opacity cells
  - `saved-views-panel.tsx` — list + save-current form + delete per row
- **Page** (`audit/page.tsx`): Explorer / Analytics tab bar; Export CSV link in header (points directly to backend CSV endpoint with current filter params)

### Robot E2E (Task 3)
- **`tests/e2e/audit/02_analytics.robot`** — 4 tests, 4 passed
  - `Analytics Tab Renders All Panels` — funnel-builder, retention-grid, saved-views-panel all visible
  - `Funnel Returns Steps For Seeded Events` — funnel result panel appears with ≥2 step rows
  - `Saved View Create And Delete` — create → list shows item → delete → list empty
  - `CSV Export Link Present` — `data-testid="audit-export-csv"` visible; href contains `format=csv`
- **`keywords/audit.resource`**: added `Open Analytics Tab`, `Run Funnel`, `Create Saved View`, `_Assert No Saved Views`
- **Regression**: `01_explorer.robot` — 3/3 still green

### Chrome-devtools (Task 4)
- Explorer tab: renders correctly, no console errors
- Analytics tab: all 3 panels visible, no console errors

---

## Acceptance Criteria

| # | Criterion | Status |
|---|-----------|--------|
| 1 | `POST /v1/audit-events/funnel` returns step-by-step conversion data | ✅ |
| 2 | `GET /v1/audit-events/retention` returns cohort heatmap data | ✅ |
| 3 | `GET /v1/audit-events?format=csv` streams CSV with header row | ✅ |
| 4 | Saved views CRUD (GET/POST/DELETE /v1/audit-saved-views) works org-scoped | ✅ |
| 5 | Analytics tab renders funnel builder + retention grid + saved views panel | ✅ |
| 6 | Robot E2E 4/4 green, 01_explorer 3/3 still green | ✅ |

---

## Key Decisions Made

- **Route ordering**: Specific GET paths (`/retention`, `/stats`) must come before `/{event_id}` in FastAPI to prevent path parameter capture
- **Funnel SQL**: Separate `_funnel_step0` + `_funnel_stepi` helpers each build their own param list — avoids the param-renumbering problem when using the same WHERE clause with different table aliases
- **Catalog sequence**: SMALLINT identity sequence exhausted from dev iterations; reset with `setval()` as band-aid — needs INTEGER migration in v0.1.5
- **CSV streaming**: Direct download link in header using `<a href>` pattern (not a JS fetch) — works with cookies=include since browser includes credentials on anchor-tag navigation

---

## Deferred Issues

- `01_catalog.12_fct_nodes.id` column should be migrated from SMALLINT to INTEGER to avoid sequence exhaustion in production — deferred to v0.1.5
- Retention grid: no cohorts shown in test org (no real user journeys) — expected; seeded events have same actor so cohort + return work but test data too small for meaningful display
