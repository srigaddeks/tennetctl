---
phase: 05-users
plan: 01
subsystem: api
tags: [iam, users, crud, nodes, run_node, audit, eav, account_types]
requires:
  - phase: 04-orgs-workspaces
    provides: IAM sub-feature template (schemas/repo/service/routes + 2 nodes), feature router composition
provides:
  - iam.users sub-feature backend
  - 5 FastAPI routes under /v1/users
  - 2 catalog nodes: iam.users.create (effect) + iam.users.get (control)
  - 4 pytest integration tests
affects: [Plan 05-02 membership writes lnk_user_orgs + lnk_user_workspaces referencing fct_users; Phase 6 roles/groups call iam.users.get to validate user existence; Phase 7 auth reads user rows for login]
tech-stack:
  patterns:
    - "dim code → FK id resolution in service layer (account_type string → account_type_id smallint)"
    - "Multiple EAV attrs set sequentially on create — each gets its own attr_row_id for upsert-on-conflict semantics"
    - "is_active toggle as PATCH field, not a separate /activate endpoint — consistent with 5-endpoint rule"
key-files:
  created:
    - backend/02_features/03_iam/sub_features/03_users/{schemas,repository,service,routes}.py
    - backend/02_features/03_iam/sub_features/03_users/nodes/{iam_users_create,iam_users_get}.py
    - tests/test_iam_users_api.py
  modified:
    - backend/02_features/03_iam/feature.manifest.yaml
    - backend/02_features/03_iam/routes.py
key-decisions:
  - "account_type frozen on PATCH — changing auth type is a rare migration; wait for concrete use case"
  - "No email uniqueness in v1 — real email-based auth enforces it in Phase 7; duplicate emails allowed in v1 (multi-account-type per email is a real scenario)"
  - "avatar_url is optional — only set dtl_attrs row if provided on create"
  - "VALIDATION_ERROR (422) for unknown account_type — dim FK isn't 'not found', it's malformed input"
duration: ~10min
completed: 2026-04-16T16:00:00Z
---

# Phase 5 Plan 01: iam.users Backend Vertical — Summary

**Third IAM vertical ships: users with account_type FK resolution + 3 EAV attrs. Template ports cleanly — apply took under 10 minutes end-to-end including tests.**

## AC Result

| AC | Status |
|---|---|
| AC-1: User CRUD end-to-end | Pass — `test_user_crud_end_to_end` (POST → GET → PATCH display_name → PATCH is_active → no-op PATCH → DELETE → 404) + 3 dtl rows verified |
| AC-2: Invalid account_type rejected | Pass — 422 VALIDATION_ERROR for 'banana_oauth'; zero rows persisted |
| AC-3: run_node create + get | Pass — `test_iam_users_create_and_get_via_run_node` |
| AC-4: Catalog + regression clean | Pass — 2 features / 7 sub-features / **7 nodes** / 0 deprecated; lint clean; pytest 71/71 ex-migrator (67 prior + 4 new) |

## Files

Created 7, modified 2. ~800 new code lines.

## Next

Plan 05-02 — user memberships. Writes to `lnk_user_orgs` and `lnk_user_workspaces`. Validates user + org / workspace existence via `run_node("iam.users.get", ...)` + `run_node("iam.orgs.get", ...)`. 4 nodes: `iam.users.assign_to_org`, `iam.users.remove_from_org`, same for workspaces.

---
*Phase 05-users, Plan 01 — Completed 2026-04-16*
