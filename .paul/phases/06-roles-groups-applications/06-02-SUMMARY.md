---
phase: 06-roles-groups-applications
plan: 02
subsystem: iam
tags: [iam, applications, scopes, rbac, postgres, lnk-table]

requires:
  - phase: 06-01
    provides: roles + groups + scopes backend
provides:
  - lnk_application_scopes M:N table
  - PATCH /v1/applications/{id} accepts scope_ids (REPLACE semantics)
  - scope_ids hydrated on GET + list responses

tech-stack:
  added: []
  patterns:
    - "REPLACE semantics via single-tx DELETE + executemany INSERT"
    - "Bulk-hydration helper list_scope_ids_many to avoid N+1 on list endpoints"

key-files:
  created:
    - 03_docs/features/03_iam/05_sub_features/06_applications/09_sql_migrations/01_migrated/20260417_051_iam-application-scopes.sql
  modified:
    - backend/02_features/03_iam/sub_features/06_applications/schemas.py
    - backend/02_features/03_iam/sub_features/06_applications/repository.py
    - backend/02_features/03_iam/sub_features/06_applications/service.py
    - backend/02_features/03_iam/sub_features/06_applications/routes.py
    - tests/test_iam_applications_api.py

key-decisions:
  - "Scope assignment piggy-backs on PATCH /v1/applications/{id} (optional scope_ids field) rather than a dedicated action endpoint — keeps API surface minimal per CLAUDE.md SIMPLICITY rules"
  - "REPLACE semantics, not PATCH — idempotent, simpler reasoning, fewer audit events"
  - "Invalid scope_ids rejected via ValidationError (400); existence checked against dim_scopes before replace"

duration: ~25min
completed: 2026-04-17
---

# Phase 6 Plan 02: Applications Scope Assignment Summary

**PATCH /v1/applications/{id} now accepts `scope_ids` for atomic REPLACE of the application-to-scope linkage. New table `45_lnk_application_scopes` + 2 new tests, all 88 IAM tests green.**

## Acceptance Criteria Results

| AC | Status | Notes |
|---|---|---|
| AC-1: Application CRUD verified | Pass | Existing `test_application_crud` still green |
| AC-2: Scope assignment path | Pass | PATCH accepts scope_ids; REPLACE semantics verified; re-submit idempotent; audit fires under existing `iam.applications.updated` event with `changed: [scope_ids]` |
| AC-3: Cross-org isolation | N/A this plan | Enforced at session/middleware layer; no new attack surface added |
| AC-4: UI verifies flow | Deferred | Frontend already has applications page; scope multi-select hookup is follow-up UI work |
| AC-5: Manifest + nodes | N/A | No new node added; scope replacement is a route-level operation, not a distinct catalog node |

## What Was Built

### Migration 051
- `03_iam.45_lnk_application_scopes` (id, org_id, application_id, scope_id, created_by, created_at)
- PK + 3 FKs (app CASCADE, scope, org)
- UNIQUE (application_id, scope_id) + index on application_id
- Respects 40-59 lnk_* numbering range

### Backend changes
- `schemas.py` — `ApplicationUpdate.scope_ids: list[int] | None` and `ApplicationRead.scope_ids: list[int]`
- `repository.py` — `list_scope_ids`, `list_scope_ids_many` (bulk hydrator), `replace_application_scopes`, `dim_scope_ids_exist`
- `service.py` — `update_application` validates scope_ids against `dim_scopes`, compares to current, replaces atomically in the caller's tx when changed
- `service.py` — `get_application` + `list_applications` hydrate `scope_ids` (bulk query on list, no N+1)
- `routes.py` — PATCH passes `body.scope_ids` through

### Tests (2 new, both green)
- `test_application_scope_assignment` — 6 assertions: initial empty, assign [4,5], GET hydrates, replace to [6], clear to [], reject 999, re-submit idempotent
- `test_application_list_includes_scope_ids` — verifies list endpoint bulk-hydrates

### Regression
- 88 passed / 472 deselected (full IAM suite) — no regressions

## Deviations from Plan

| Type | Deviation | Why |
|------|-----------|-----|
| API shape | Used PATCH /v1/applications/{id} with scope_ids instead of a separate POST /scopes endpoint | Honors the project-wide rule "PATCH handles ALL state changes — never action endpoints" (CLAUDE.md) |
| Node registration | No new catalog node added for scope assignment | Route-level operation; audit emission already flows via existing `audit.events.emit` node under `iam.applications.updated` event. Adding a dedicated node would duplicate the control-plane audit story. |
| Test file | Added tests to existing `test_iam_applications_api.py` rather than creating `test_iam_applications_scopes.py` | Reuses the `live_app` fixture + org cleanup; single file keeps the applications test surface together |

## Next Phase Readiness

**Ready:** Role-scope assignment could follow the same pattern using the existing `44_lnk_role_scopes` table — same REPLACE-via-PATCH shape.

**Concerns:** None.

**Blockers:** None.

---
*Phase: 06-roles-groups-applications, Plan: 02*
*Completed: 2026-04-17*
