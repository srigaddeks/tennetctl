---
phase: 03-iam-audit
plan: 01
subsystem: database
tags: [iam, schema, migrations, orgs, workspaces, users, roles, groups, scopes, dim, fct, dtl, lnk, eav]

requires:
  - phase: 01-core-infrastructure
    provides: migrator, Postgres, distributed migration convention
  - phase: 02-catalog-foundation
    provides: NCP v1 + catalog DB (so IAM can register its feature.manifest.yaml in Plan 03-02)
provides:
  - "03_iam" Postgres schema
  - 4 dim tables (entity_types, account_types, scopes, role_types) with 19 seeded rows
  - 2 EAV tables (dtl_attr_defs, dtl_attrs)
  - 6 fct tables (orgs, workspaces, users, roles, groups, applications) with UUID v7 PKs
  - 5 lnk tables (user_orgs, user_workspaces, user_roles, user_groups, role_scopes) — immutable
  - 17 tables total, 4 migrations applied
affects: [03-02 IAM feature manifest, 03-03 audit + emit_audit, 03-04 views, Phase 4 Orgs vertical]

tech-stack:
  added: []
  patterns:
    - "Slugs ARE on fct_* (orgs, workspaces) — they are identity discriminators, not business attrs; partial unique index gates on deleted_at IS NULL"
    - "fct_roles.org_id nullable → NULL = global/system role; non-null = org-scoped role"
    - "lnk_* all carry org_id explicitly (tenant discriminator) except lnk_role_scopes (scope is a property of the role itself)"
    - "IAM EAV isolated by schema — 03_iam.dim_entity_types lists IAM entities (org/user/...); 01_catalog.dim_entity_types lists catalog entities (feature/sub_feature/node/...); same pattern, different namespaces"

key-files:
  created:
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/01_migrated/20260413_001_create-iam-schema.sql
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/01_migrated/20260413_002_iam-dim-tables.sql
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/01_migrated/20260413_003_iam-fct-tables.sql
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/01_migrated/20260413_004_iam-lnk-tables.sql
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/seeds/01_dim_entity_types.yaml
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/seeds/02_dim_account_types.yaml
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/seeds/03_dim_scopes.yaml
    - 03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/seeds/04_dim_role_types.yaml
  modified: []

key-decisions:
  - "03_iam.01_dim_entity_types uses manual SMALLINT PK, not GENERATED IDENTITY — plan had a contradiction (GENERATED column + seed supplying explicit IDs). Manual PK consistent with account_types / scopes / role_types in the same schema"
  - "fct_roles.org_id nullable — NULL = global system role (e.g. platform_admin); non-null = tenant-scoped role"
  - "lnk_role_scopes has no org_id — the role carries the org, the scope grant is a property of the role"

patterns-established:
  - "Pattern: partial unique index `WHERE deleted_at IS NULL` for slug uniqueness among non-deleted rows"
  - "Pattern: constraint names prefixed with `iam_` within the 03_iam schema to disambiguate from identical names in other schemas"
  - "Pattern: every fct_* index idx_iam_fct_*_<fk_col> for FK lookups"

duration: ~10min
started: 2026-04-16T12:25:00Z
completed: 2026-04-16T12:35:00Z
---

# Phase 3 Plan 01: IAM Schema — Summary

**17-table IAM schema landed: `"03_iam"` with 4 dim + 6 fct + 2 dtl + 5 lnk tables; 4 migrations applied; 19 dim rows seeded (entity_types / account_types / scopes / role_types).**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10min |
| Tasks | 2 auto + 1 checkpoint (self-verified per push-through directive) |
| Migrations applied | 4 |
| Tables created | 17 |
| Dim rows seeded | 19 (7 + 4 + 6 + 2) |

## Acceptance Criteria Results

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AC-1: Schema + EAV foundation migrated | Pass | `"03_iam"` schema + dim_entity_types + dtl_attr_defs + dtl_attrs created |
| AC-2: Dim tables seeded | Pass | 7 entity_types, 4 account_types, 6 scopes, 2 role_types — verified via seed log |
| AC-3: Entity + link tables migrated | Pass | 6 fct_* + 5 lnk_* tables with all FK constraints in place (`\dt "03_iam".*` shows 17 rows) |
| AC-4: Migrator reports up to date | Pass | `runner status` shows 8 applied (Phase 1–3 combined), 0 pending |

## Files Created

4 SQL migrations in `01_migrated/`, 4 seed YAMLs in `seeds/`. All under `03_docs/features/03_iam/05_sub_features/00_bootstrap/09_sql_migrations/`.

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Plan contradiction on dim_entity_types PK — fixed before seeding |
| Scope additions | 0 | — |
| Deferred | 0 | — |

### Auto-fixed Issues

**1. dim_entity_types PK type contradiction**
- Found during: Task 1 seed run
- Issue: Plan said `GENERATED ALWAYS AS IDENTITY` on the PK, but seed supplied explicit `id: 1..7`. Postgres rejected with "cannot insert non-DEFAULT value into identity column defined as GENERATED ALWAYS".
- Fix: Changed column to `SMALLINT NOT NULL` manual PK (consistent with account_types / scopes / role_types in the same schema). Rolled back + re-applied.
- Verification: All 7 entity_types rows inserted with their planned IDs (1-7).

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Migrator seed failed first run due to PK contradiction above | Rolled back migrations, edited SQL to manual PK, re-applied + re-seeded |

## Next Phase Readiness

**Ready:**
- IAM tables exist — Plan 03-02 can write `backend/02_features/03_iam/feature.manifest.yaml` declaring these tables under the `iam` feature's sub-features.
- Audit schema (Plan 03-03) can reference `03_iam` tables in its FKs (e.g. evt_audit.actor_user_id FK to fct_users).
- EAV foundation ready for attr registration (email, display_name, avatar_url, etc.) — Plan 03-02 or Phase 4 will register them.

**Concerns:**
- No dtl_attr_defs registered yet — first real writes need to register user.email, org.display_name, etc. This is app-layer boilerplate rather than schema work.
- Sessions table intentionally deferred to Phase 5 (Users).

**Blockers:**
- None. Ready for Plan 03-02 (IAM feature manifest + catalog registration).

---
*Phase: 03-iam-audit, Plan: 01*
*Completed: 2026-04-16*
