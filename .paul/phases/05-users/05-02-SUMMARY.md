---
phase: 05-users
plan: 02
subsystem: api
tags: [iam, memberships, lnk, cross-sub-feature, run_node, audit]
requires:
  - phase: 04-orgs-workspaces (iam.orgs.get, iam.workspaces.get nodes)
  - phase: 05-users-01 (iam.users.get node)
provides:
  - New iam.memberships sub-feature (number=7) owning lnk_user_orgs + lnk_user_workspaces
  - 6 HTTP endpoints (/v1/org-members, /v1/workspace-members × POST/GET/DELETE)
  - 4 catalog nodes (org.assign/revoke, workspace.assign/revoke) — all effect + emits_audit
  - 4 integration tests
affects: [Phase 6 roles/groups build on same parent-validation pattern; Phase 7 auth reads memberships for scope evaluation]
key-files:
  created:
    - backend/02_features/03_iam/sub_features/07_memberships/{schemas,repository,service,routes}.py + nodes/ (4 handlers)
    - tests/test_iam_memberships_api.py
  modified:
    - backend/02_features/03_iam/feature.manifest.yaml (removed lnk tables from orgs/workspaces; added iam.memberships sub-feature #7)
    - backend/02_features/03_iam/routes.py (composed memberships sub-router)
key-decisions:
  - "iam.memberships as its own sub-feature (not nested under orgs/workspaces) — keeps parent sub-features at 5 files, gives a single home for both lnk tables"
  - "Lnk table ownership transferred from iam.orgs/workspaces → iam.memberships in manifest — reflects where the writes actually happen"
  - "Revoke = hard DELETE — matches lnk immutability rule (no deleted_at on lnk_*)"
  - "No individual GET by id — lnk rows don't have rich state; list-by-filter is the lookup primitive"
  - "Three cross-sub-feature validations per assign call (iam.users.get + iam.orgs.get OR iam.workspaces.get) — proves run_node fan-out works"

duration: ~15min
completed: 2026-04-16T16:20:00Z
---

# Phase 5 Plan 02: iam.memberships Sub-Feature — Summary

**User-org and user-workspace memberships live: 4 effect nodes, 6 HTTP endpoints, all cross-entity validation goes through run_node.**

## AC Result
| AC | Status |
|---|---|
| AC-1: Org membership CRUD | Pass |
| AC-2: Workspace membership CRUD (org_id auto-derived) | Pass |
| AC-3: Missing parent returns NOT_FOUND | Pass |
| AC-4: Catalog + lint + regression | Pass — 8 sub-features / **11 nodes** / 0 deprecated; 75 passed ex-migrator |

## Files: 8 created, 2 modified

---
*Phase 05-users, Plan 02 — Completed 2026-04-16*
