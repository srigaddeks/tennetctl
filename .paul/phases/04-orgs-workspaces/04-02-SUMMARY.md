---
phase: 04-orgs-workspaces
plan: 02
subsystem: api
tags: [iam, workspaces, crud, nodes, run_node, audit, cross-sub-feature, per-org-uniqueness]

requires:
  - phase: 04-orgs-workspaces-01
    provides: iam.orgs backend + iam.orgs.get control node (used for parent-org validation)
provides:
  - iam.workspaces sub-feature backend (schemas/repo/service/routes)
  - 5 FastAPI endpoints under /v1/workspaces (list filterable by org_id / create / get / patch / delete)
  - 2 catalog-registered nodes — iam.workspaces.create (effect, audit) + iam.workspaces.get (control)
  - Workspace sub-router included in backend/02_features/03_iam/routes.py alongside orgs
  - 4 pytest integration tests (CRUD + per-org conflict + missing-org 404 + run_node dispatch)
affects: [Phase 5 Users (membership lnk tables reference workspaces), Phase 6 role assignment to workspaces, all future iam.* that nest under workspace scope]

tech-stack:
  added: []
  patterns:
    - "Compound uniqueness (org_id, slug) enforced via partial unique index + service pre-check"
    - "Parent-FK validation via run_node('<parent>.get', ...) — sanctioned cross-sub-feature path; linter proves no direct import"
    - "List filter param (?org_id=...) instead of nested routes (/orgs/{id}/workspaces) — stays flat per 5-endpoint rule"

key-files:
  created:
    - backend/02_features/03_iam/sub_features/02_workspaces/{__init__,schemas,repository,service,routes}.py
    - backend/02_features/03_iam/sub_features/02_workspaces/nodes/{__init__,iam_workspaces_create,iam_workspaces_get}.py
    - tests/test_iam_workspaces_api.py
  modified:
    - backend/02_features/03_iam/feature.manifest.yaml
    - backend/02_features/03_iam/routes.py

key-decisions:
  - "org_id frozen on PATCH — cross-org workspace moves deferred (no concrete use case)"
  - "Unknown parent org returns NOT_FOUND (not CONFLICT) — matches REST convention for missing FK target"
  - "iam.workspaces.get node paralells iam.orgs.get — Phase 5+ user/role sub-features will call both to validate tenant scope"

patterns-established:
  - "Pattern for nested resources: flat routes + filter param + parent-FK validation via run_node"
  - "Cleanup order in tests (FK-safe): audit → lnk_* → dtl_attrs (child entity) → dtl_attrs (parent entity) → fct_* (child) → fct_* (parent)"

duration: ~15min
started: 2026-04-16T15:30:00Z
completed: 2026-04-16T15:45:00Z
---

# Phase 4 Plan 02: iam.workspaces Backend Vertical — Summary

**Second IAM vertical ships with per-org slug uniqueness and parent-org validation via `run_node("iam.orgs.get", ...)`. 5 routes, 2 nodes, 4 integration tests all green on first apply — the Plan 04-01 template ports cleanly.**

## AC Result

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AC-1: Workspace CRUD works end-to-end | Pass | `test_workspace_crud_end_to_end` — 5 routes + audit on every mutation |
| AC-2: Per-org slug conflict envelope | Pass | `test_workspace_slug_conflict_per_org` — (org_a, dup) → 409; (org_b, dup) → 201 |
| AC-3: Org-existence validation via run_node | Pass | `test_workspace_create_rejected_when_org_missing` — 404 NOT_FOUND, 0 fct rows, 0 audit events |
| AC-4: iam.workspaces.create node | Pass | `test_iam_workspaces_create_and_get_via_run_node` — in-tx dispatch writes fct+dtl+audit atomically |
| AC-5: iam.workspaces.get node (control, no audit) | Pass | Same test — returns `{workspace: dict\|None}`; zero audit rows from get calls |
| AC-6: Catalog boot + regression clean | Pass | Catalog: 2 features / 7 sub-features / **5 nodes** / 0 deprecated; lint clean; pytest 67/67 ex-migrator (63 prior + 4 new) |

## Deviations from Plan

**None.** Plan executed exactly as written. First-pass apply, all 4 tests green on first run.

## Files Changed

| File | Change |
|------|--------|
| `backend/02_features/03_iam/sub_features/02_workspaces/*.py` (5 files) | Created — sub-feature template |
| `backend/02_features/03_iam/sub_features/02_workspaces/nodes/*.py` (3 files) | Created — 2 catalog nodes |
| `backend/02_features/03_iam/feature.manifest.yaml` | Modified — iam.workspaces sub-feature entry populated with 2 nodes + 5 routes + views |
| `backend/02_features/03_iam/routes.py` | Modified — include workspace sub-router alongside orgs |
| `tests/test_iam_workspaces_api.py` | Created — 4 integration tests |

## Next Plan

**Ready:** Plan 05-01 (Users backend) — same shape; account_type FK to dim_account_types; email/display_name/avatar_url via EAV (dim_attr_defs already seeded in Phase 3).

---
*Phase: 04-orgs-workspaces, Plan: 02 — Completed: 2026-04-16*
