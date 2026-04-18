---
phase: 23R-rebase-unified-authz
status: complete
completed: 2026-04-18
commits:
  - ec93b58 (23R-01 + 23R-02 schema + resolver)
  - eab604b (23R-03 Role Designer)
  - d874a14 (23R-03 dead-code removal)
---

# Phase 23R — Summary

## What shipped

**Schema (migration `20260418_050_rebase-flags-as-capabilities.sql`):**
- Dropped: `03_iam.03_dim_scopes`, `03_iam.44_lnk_role_scopes`,
  `03_iam.45_lnk_application_scopes`, `09_featureflags.04_dim_flag_permissions`,
  `09_featureflags.40_lnk_role_flag_permissions`
- Created in `"09_featureflags"`:
  - `01_dim_permission_actions` (8 rows: view/create/update/delete/assign/configure/export/impersonate)
  - `02_dim_feature_flag_categories` (8 rows)
  - `03_dim_feature_flags` (40 capability rows)
  - `04_dim_feature_permissions` (138 flag × action rows)
  - `40_lnk_role_feature_permissions` (role ↔ permission bundles)
- Untouched: `10_fct_flags`, `11_fct_flag_states`, rules, overrides — these
  survive as the opt-in "advanced rollout" layer for user-created flags

**Resolver (`backend/01_core/authz.py`, 247 → 243 LOC):**
- `require_permission(conn, user_id, "flag.action", scope_org_id=…)`
- Single-path join through new tables (tennetctl has direct user→role
  assignment, so the ref's 6-branch UNION collapses to 1 branch)
- `AccessContext.permission_codes` frozenset, 5-min SWR cache
- Back-compat `.scope_codes` alias preserved

**API (new `09_featureflags/sub_features/06_capabilities/`):**
- `GET /v1/capabilities` — full catalog
- `GET /v1/roles/{id}/grants`
- `POST /v1/roles/{id}/grants` (batch, idempotent)
- `DELETE /v1/roles/{id}/grants/{permission_code}`
- Old `02_permissions` sub-feature unmounted

**UI (`frontend/src/features/capabilities/`):**
- `capability-grid.tsx` — category-grouped grid of flag × action checkboxes,
  per-row bulk toggle, optimistic updates, dark-mode native
- Role page "Permissions" tab → "Capabilities" tab
- Flag detail page lost its "Permissions" tab (dead endpoint); environments,
  rules, overrides tabs stay for advanced-rollout flags

## Genericity

Ref had GRC-specific resolver branches (workspace GRC role, org GRC role
assignments). All dropped — tennetctl ships as a generic control panel.
Built-in roles: `superadmin`, `platform_admin`, `workspace_admin`. Any
domain-specific roles are user-created.

## Outstanding / deferred

- **Applications sub-feature scope bindings** — `lnk_application_scopes` was
  dropped with no replacement. OAuth app scopes need rewiring in a follow-up
  to `lnk_application_feature_permissions` (or equivalent). v0.2.0 pre-release
  so no data loss.
- **System role seeding** — the 7 canonical roles from the plan aren't all in
  the DB. Current state: 3 roles exist (superadmin, platform_admin,
  workspace_admin). 4 others (org_admin, org_member, org_viewer,
  workspace_contributor, workspace_viewer) need to be seeded by app init for
  completeness. Superadmin + platform_admin both have full 138-perm grants.
- **Capability Catalog page** — read-only `/feature-flags` registry view
  showing capabilities by category with "granted by N roles" counts. Not
  built — current Role Designer grid surfaces the same data. Low priority.

## Metrics

- 3 commits
- 11 files changed in commit 1 (+3,575, −71)
- 10 files changed in commit 2 (+776, −18)
- 3 files changed in commit 3 (+4, −227)
- 40 capabilities, 8 actions, 138 feature_permissions, 276 grants seeded
