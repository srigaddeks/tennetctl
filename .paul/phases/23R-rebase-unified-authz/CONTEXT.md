---
milestone: v0.2.0 — Feature Flags + AuthZ Control Plane
phase: 23R (rebase of 23)
plans: 3
created: 2026-04-18
status: ready-for-planning
reference: /Users/sri/Documents/tennetctl/99_ref/backend/03_auth_manage/
supersedes:
  - 23-feature-flags-authz (LaunchDarkly-style targeting model)
---

# Phase 23R — Rebase onto the Unified Flag+Permission Model

## Why this phase exists

Phase 23 shipped a LaunchDarkly-style feature-flag engine (targeting rules,
per-entity overrides, rollout hashing) alongside a separate 48-permission
`dim_scopes` catalog. These two systems never met: `require_permission` used
scope strings; `09_featureflags` evaluated rollout.

The intended mental model — surfaced after reviewing `99_ref` — is simpler
and unified: **a feature flag IS a capability**. Each flag has a set of
permission actions (view/create/update/delete/assign/…). A
`feature_permission` is a `(flag_code, action_code)` pair. A **role is a
bundle of feature_permissions**. No separate "permission" concept floats
free of a flag.

Rollout is governed by the flag's own attributes:
- `lifecycle_state` — planned → active → deprecated → retired
- `env_dev / env_staging / env_prod` — per-env on/off
- `access_mode` — public / authenticated / permissioned

LaunchDarkly-style targeting (rules, % rollout, per-user overrides) is
preserved as an **opt-in advanced rollout layer** — only flags with
`rollout_mode = "targeted"` use the rule engine. Default flags do
env + access_mode + role grant.

## What changes

| Concern | Before (23) | After (23R) |
|---|---|---|
| Permission catalog | `dim_scopes` (48 free strings) | `dim_feature_flags × dim_permission_actions → dim_feature_permissions` |
| Role grants | `lnk_role_scopes` + `lnk_role_flags` (two separate lists) | `lnk_role_feature_permissions` (one list, keyed by flag × action) |
| `require_permission` | 2-branch scope lookup | Single-path join: `lnk_user_roles → lnk_role_feature_permissions → dim_feature_permissions → (dim_feature_flags, dim_permission_actions)`. Ref's 6 branches collapse because tennetctl has direct user→role assignment (no membership_type intermediation, no group→role links) |
| Flag model | rollout toggle | capability definition with category, scope, access_mode, lifecycle, env toggles, required_license |
| Rollout rules | always-on condition tree + overrides | opt-in advanced layer behind `rollout_mode="targeted"` |
| Roles UI | separate "permissions" + "flags" tabs | single Role Designer: (flag × action) grid grouped by category |
| Feature Flags UI | "Flag list → rules/overrides" | "Capability Catalog → per-flag permissions + optional advanced rollout" |
| Portal Views | unchanged | unchanged (role-keyed, orthogonal to this rebase) |

## What is preserved

- The `09_featureflags` code path, overrides engine, rules editor — demoted
  to "advanced rollout" and only active for flags that opt in.
- The SDKs (`sdks/python`, `sdks/typescript`) — continue to evaluate against
  the same flag codes; under the hood they fall through to access_mode + env
  + role grant unless rollout_mode is targeted.
- The audit trail — every grant/revoke still emits an event; event keys just
  change from `iam.scope.*` to `iam.feature_permission.*`.
- Portal Views — untouched; role→view assignment is orthogonal.

## What is discarded

- `dim_scopes` and its seed data.
- `lnk_role_scopes` and `lnk_role_flags` — merged into
  `lnk_role_feature_permissions`.
- The Roles UI "Permissions" + "Feature Flags" tabs — replaced by one
  "Capabilities" grid.
- APISIX compilation for request-path flag evaluation — replaced by APISIX
  compiling `require_permission("flag.action")` checks pulled from route
  metadata. (Cleaner; same performance.)

## Plan breakdown

### 23R-01 — Schema + seeds
Add `dim_permission_actions`, expand `dim_feature_flags`, create
`dim_feature_permissions` + `lnk_role_feature_permissions`. Seed 8
actions (view/create/update/delete/assign/configure/export/impersonate).
Seed one feature flag per existing sub-feature (orgs, users, roles,
workspaces, memberships, groups, applications, auth_policy, portal_views,
vault_secrets, vault_configs, audit_explorer, monitoring_*, notify_*,
feature_flags, nodes). Seed `(flag × action)` permissions for each.
Migrate existing role grants from `lnk_role_scopes` → new table by mapping
scope code to equivalent `flag.action`.

**Deliverables:** 1 migration, 2 seed YAMLs, data-migration SQL, down-migration.

### 23R-02 — Resolver + route migration
Port `99_ref/backend/03_auth_manage/_permission_check.py` to
`backend/01_core/authz.py::require_permission` (replacing the current
2-branch version with the 6-branch UNION). Update every existing
`require_permission("scope.code")` call to `require_permission("flag.action")`
using the mapping table from 23R-01. Update `AccessContext` to resolve
feature_permissions instead of scopes. Rebuild in-process LRU cache.

**Deliverables:** new `authz.py`, updated callers across `02_features/*/`,
updated `AccessContext`, 20+ pytest tests covering all 6 branches.

### 23R-03 — UI rebase
Roles page: replace two-list UI with single "Capabilities" tab — grid of
`flag_category → flag → action checkboxes`, bulk-select by row/column.
Feature Flags page: rename to "Capability Catalog"; each flag shows its
permission actions, env toggles, access_mode, and which roles grant it.
Old rules/overrides editor moves behind an "Advanced rollout" tab shown
only when `rollout_mode = "targeted"` is set.

**Deliverables:** rewritten `iam/roles/page.tsx`, rewritten
`feature-flags/page.tsx` + new `feature-flags/[flagId]/page.tsx`,
new hooks, updated types in `api.ts`.

## Non-goals for 23R

- Per-user permission overrides outside of roles (use groups).
- Changing how Portal Views attach to roles.
- SAML/SCIM/MFA/IP allowlist integration with the new model — phase 22
  sub-features already grant via the existing role model and continue to
  work unchanged through the mapping.
- Removing the advanced rollout layer — it stays, opt-in.

## Genericity principle

TennetCTL is a **generic self-hostable control panel**, not a GRC product.
The authz model must work for any project — e-commerce, SaaS, internal tools,
dev platforms. Drop anything that assumes a specific vertical:

- No GRC role branches (ref had 2). Resolver is 4 branches, period.
- No `grc_role_code` on workspace membership.
- No `47_lnk_grc_role_assignments` table.
- `role_level_code` dim keeps generic levels only: `platform`, `org`,
  `workspace`. No GRC-specific levels.

Any domain-specific roles a project needs are created as user-defined roles
at runtime — the catalog ships no built-in GRC / compliance / audit-specific
roles. Built-ins are limited to the universal set:
`platform_super_admin`, `org_admin`, `org_member`, `org_viewer`,
`workspace_admin`, `workspace_contributor`, `workspace_viewer`.

## Resolved design decisions (2026-04-18)

1. **Scope on the role, not per grant.** `fct_roles` keeps
   `scope_org_id` / `scope_workspace_id`. `lnk_role_feature_permissions` has
   no scope columns — a grant's scope is inherited from its role. If we ever
   need per-grant scope override, we add it then.
2. **No data migration.** v0.2.0 is pre-release. DROP `lnk_role_scopes` +
   `lnk_role_flags` + `dim_scopes` outright. Fresh seed of the new dim and
   feature_permission tables. Tests cover the new shape; no compatibility
   SQL.
