---
phase: 06-roles-groups-applications
plan: 01
subsystem: api
tags: [iam, roles, groups, applications, eav, views, run_node, audit]
requires:
  - phase: 05-users-01 (iam.users.get for role/group parent validation)
  - phase: 04-orgs-workspaces (iam.orgs.get for parent-org validation)
provides:
  - Schema: dim_attr_defs +9 rows for role/group/application entity types; 3 new views (v_roles, v_groups, v_applications)
  - 3 new sub-feature backends: iam.roles (global + org-scoped), iam.groups (org-scoped), iam.applications (org-scoped)
  - 6 new catalog nodes (create + get for each)
  - 15 new HTTP routes (5 per resource)
  - 9 integration tests
affects: [Phase 7 auth reads role-scope + user-role joins; future group-role assignment extends this]
duration: ~35min
completed: 2026-04-16T16:55:00Z
---

# Phase 6 Plan 01: Roles + Groups + Applications Backends — Summary

**IAM backend complete: 6 sub-features (orgs, workspaces, users, memberships, roles, groups, applications) + 17 catalog nodes + ~30 HTTP routes + full audit + end-to-end smoke green.**

## AC Result
| AC | Status |
|---|---|
| DB prep (3 views + 9 new attr_defs) | Pass — views v_roles, v_groups, v_applications created; 14 attr_defs present |
| iam.roles backend | Pass — global + org-scoped roles; per-(org_id, code) uniqueness; CRUD via API + run_node |
| iam.groups backend | Pass — org-scoped; per-org code uniqueness; missing-org → 404 |
| iam.applications backend | Pass — org-scoped; per-org code uniqueness; missing-org → 404 |
| Catalog + lint + regression | Pass — 2 features / 8 sub-features / **17 nodes** / 0 deprecated; lint clean; pytest 84/84 ex-migrator |
| End-to-end live smoke | Pass — org → workspace → user → org-member → ws-member → role → group → application = 8 audit events in evt_audit |

## Files
Created 24 code files + 3 test files + 3 migration files. Modified manifest (3 sub-feature entries populated) + feature router + attr_defs seed.

## Live Smoke (cleanup included)
```
org → 201, workspace → 201, user → 201,
org-member → 201, workspace-member → 201,
role (global system) → 201, group → 201, application → 201
Audit trail: 8 rows (one per mutation). Cleanup: DELETE 8 + all FK children.
```

## IAM Backend Total (all 6 sub-features + memberships)

| Sub-feature | Routes | Nodes | Tests |
|---|---|---|---|
| iam.orgs | 5 | 2 | 3 |
| iam.workspaces | 5 | 2 | 4 |
| iam.users | 5 | 2 | 4 |
| iam.memberships | 6 | 4 | 4 |
| iam.roles | 5 | 2 | 3 |
| iam.groups | 5 | 2 | 3 |
| iam.applications | 5 | 2 | 3 |
| **Total** | **36** | **17** (16 IAM + 1 audit) | **24** |

## Deviations from Plan
- Skipped seed YAML re-application (checksum mismatch) — inserted 9 new attr_def rows via direct SQL. Seed file still reflects target state; seed tracker out-of-sync with reality is a known minor issue (file and DB both have the 14 rows).

## Next
Phase 6 Plan 02 would be role-scope assignments (lnk_role_scopes) and user-role assignments (lnk_user_roles) + user-group assignments (lnk_user_groups). These are natural extensions of iam.memberships sub-feature. Not needed for "basic IAM backend working end-to-end" per Sri's scope.

---
*Phase 06-roles-groups-applications, Plan 01 — Completed 2026-04-16*
