---
phase: 09-featureflags
plan: 01
subsystem: database
tags: [featureflags, schema, dim, bootstrap, iam-scopes, catalog-module]
requires:
  - phase: 06-roles-groups-applications (IAM backend complete with dim_scopes extensible)
provides:
  - Module `featureflags` registered in catalog + _VALID_MODULES + Literal
  - Schema `"09_featureflags"` + 4 dim tables seeded (environments, value_types, flag_scopes, flag_permissions)
  - 5 new IAM scope dim rows (flags:view/toggle/write/admin:org + flags:admin:all)
  - Feature manifest with 5 empty sub-feature shells (flags / permissions / rules / overrides / evaluations)
affects: [Plan 09-02 flags CRUD + fct tables; 09-03 permissions lnk; 09-04 rules+overrides; 09-05 evaluator; 09-06 UI]
duration: ~15min
completed: 2026-04-16T17:15:00Z
---

# Phase 9 Plan 01: featureflags Bootstrap — Summary

**Feature 09 (featureflags) stood up at the catalog + schema + seed layer. Three scopes (global / org / application) and four environments (dev / staging / prod / test) are now addressable; five IAM scope codes gate flag mutations. No HTTP endpoints yet — 09-02 adds the first fct table.**

## AC Result

| AC | Status | Evidence |
|---|---|---|
| AC-1: module registered | Pass | `_VALID_MODULES` contains `featureflags`; dim_modules has a row (id auto-assigned); Literal accepts the module code |
| AC-2: schema + 4 dims seeded | Pass | envs=4, value_types=4, flag_scopes=3, flag_permissions=4 |
| AC-3: IAM scope rows added | Pass | `03_iam.03_dim_scopes` now has 11 rows (6 prior + 5 flag:* entries at ids 7-11) |
| AC-4: feature manifest registered | Pass | Catalog upsert: **3 features / 13 sub-features / 17 nodes / 0 deprecated**; lint clean; pytest 84/84 |

## Seeds delivered

| Dim | Rows |
|---|---|
| `09_featureflags.01_dim_environments` | dev / staging / prod / test |
| `09_featureflags.02_dim_value_types` | boolean / string / number / json |
| `09_featureflags.03_dim_flag_scopes` | global / org / application |
| `09_featureflags.04_dim_flag_permissions` | view (rank 1) / toggle (2) / write (3) / admin (4) |
| `03_iam.03_dim_scopes` (extended) | flags:view:org, flags:toggle:org, flags:write:org, flags:admin:org, flags:admin:all |

## Files

**Created:**
- `03_docs/features/09_featureflags/00_bootstrap/09_sql_migrations/01_migrated/` × 3 migrations (008 module register, 009 bootstrap, 010 IAM scopes)
- `backend/02_features/09_featureflags/__init__.py` + `sub_features/` (5 dirs with `__init__.py`)
- `backend/02_features/09_featureflags/feature.manifest.yaml`

**Modified:**
- `backend/01_catalog/manifest.py` — added `featureflags` to `_VALID_MODULES` and the `FeatureMetadata.module` Literal

## Decisions locked in

| Decision | Rationale |
|---|---|
| IAM scope extension via direct SQL migration (not YAML seed edit) | Avoids the checksum-mismatch pain hit in Phase 6; INSERT ON CONFLICT DO NOTHING is idempotent |
| `always_on: true` on the feature | Matches audit's posture; deployments can simply create no flags if they don't use the feature. Optional-module toggle deferred to v0.1.5 |
| `dim_flag_permissions.rank` column | Lets the permission helper (09-03) answer "does this user have at least X permission?" with a single `>=` compare |
| Constraint prefix `ff_` | Keeps the global constraint namespace clean; matches existing `iam_`, `audit_` prefixes |
| Workspace-scoped flags deferred | Spec + schema leave the door open (add a row to dim_flag_scopes + nullable workspace_id column) without breaking anything |

## Next plan

**09-02** — `featureflags.flags` sub-feature backend:
- `fct_flags` (with `scope_id` + nullable `org_id` + nullable `application_id` + CHECK + three partial unique indexes on `flag_key`)
- `fct_flag_states` (per-environment is_enabled + env_default_value)
- `v_flags` view (flat shape with scope + env state joined)
- schemas / repo / service / routes / 2 nodes (`featureflags.flags.create` effect, `featureflags.flags.get` control)
- Tests: CRUD at all 3 scopes, scope/target CHECK violations surfaced as 422, per-env toggle, parent FK validation via run_node

---
*Phase 09-featureflags, Plan 01 — Completed 2026-04-16*
