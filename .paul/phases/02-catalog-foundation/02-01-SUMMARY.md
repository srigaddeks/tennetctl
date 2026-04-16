---
phase: 02-catalog-foundation
plan: 01
subsystem: infra
tags: [catalog, ncp, postgres, schema, migrations, eav, seeds, dim, fct, dtl]

requires:
  - phase: 01-core-infrastructure
    provides: SQL migrator, docker-compose postgres (port 5434), distributed `09_sql_migrations/` convention, YAML seeds
provides:
  - NCP v1 protocol document (authoritative spec for node catalog)
  - ADR-027 decision record for Node Catalog + Runner
  - `"01_catalog"` Postgres schema with 9 tables (4 dim + 3 fct + 2 dtl)
  - Dim seeds: 8 modules, 3 node kinds, 3 tx modes, 5 entity types (19 rows total)
  - CHECK constraint enforcing effect-nodes-must-emit-audit at DB level
affects: [02-02 manifest loader, 02-03 node runner, 03-01 IAM schema, 03-02 IAM manifest, all Phase 3+ feature verticals]

tech-stack:
  added: []
  patterns:
    - "catalog-mirrors-manifest: DB state == feature.manifest.yaml state"
    - "SMALLINT fct PKs for catalog (deviation from general UUID rule, documented)"
    - "EAV per-entity-type (entity_type_id + entity_id + attr_def_id + one-of key_*)"
    - "distributed migrations under 03_docs/features/{feat}/05_sub_features/{sub}/09_sql_migrations/"

key-files:
  created:
    - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
    - 03_docs/00_main/08_decisions/027_node_catalog_and_runner.md
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/01_migrated/20260416_001_create-catalog-schema.sql
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/01_migrated/20260416_002_catalog-dim-tables.sql
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/01_migrated/20260416_003_catalog-fct-tables.sql
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/seeds/01_dim_modules.yaml
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/seeds/02_dim_node_kinds.yaml
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/seeds/03_dim_tx_modes.yaml
    - 03_docs/features/00_setup/05_sub_features/01_catalog/09_sql_migrations/seeds/04_dim_entity_types.yaml
  modified: []

key-decisions:
  - "NCP v1 sub-features communicate only via run_node (catalog-dispatched); direct imports across sub-features will be lint-blocked in 02-02"
  - "Catalog fct_* tables use SMALLINT GENERATED IDENTITY PKs (documented deviation from VARCHAR(36) UUID v7 rule — user-approved 2026-04-16)"
  - "Catalog migrations live under 03_docs/features/00_setup/05_sub_features/01_catalog/ (correction from plan draft; follows database.md distributed-migration convention)"
  - "Effect nodes MUST emit audit — enforced by chk_fct_nodes_effect_must_emit_audit CHECK constraint at DB (not just Python validator)"

patterns-established:
  - "Pattern: `01_catalog` schema with SMALLINT system-level PKs, referencing dim_modules / dim_node_kinds / dim_tx_modes"
  - "Pattern: dtl_attrs EAV with one-value-only CHECK (CASE-based, not ::int casting for portability)"
  - "Pattern: every node gets execution policy (timeout_ms, retries, tx_mode_id) stored in fct_nodes, enforceable at runner"
  - "Pattern: tombstoned_at nullable TIMESTAMP for lifecycle (NCP §12), kept alongside deprecated_at"

duration: ~25min
started: 2026-04-16T10:37:00Z
completed: 2026-04-16T10:56:00Z
---

# Phase 2 Plan 01: Catalog Foundation — Protocol + Schema

**NCP v1 protocol, ADR-027, and the `"01_catalog"` Postgres schema (9 tables, 19 seeded rows) are in place; every future feature will register itself into this catalog via `feature.manifest.yaml`.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~25min |
| Started | 2026-04-16T10:37:00Z |
| Completed | 2026-04-16T10:56:00Z |
| Tasks | 3 completed + 1 checkpoint approved |
| Files modified | 9 created, 0 modified |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: NCP v1 protocol + ADR published | Pass | Protocol 16 sections + ADR "Accepted" 2026-04-16 |
| AC-2: Catalog schema migrated | Pass | 9 tables across dim/fct/dtl; 3 migrations moved to `01_migrated/` |
| AC-3: Dim tables seeded | Pass | 8 modules (core/iam/audit always_on=t) + 3 kinds + 3 tx_modes + 5 entity_types = 19 rows |
| AC-4: Migrator reports up to date | Pass | `runner status` shows 4 applied, 0 pending |

## Accomplishments

- Published **NCP v1** (`03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`) — 16 sections covering entities/identity, folder structure, manifest grammar, node contract, catalog DB, NodeContext, runner, execution policy, authz hook, cross-import rule, boot, lifecycle, versioning, error codes.
- Recorded **ADR-027** documenting the catalog + runner decision, the three rejected alternatives (direct imports, gRPC, DI container), and the two escape hatches (bulk nodes, shared infra).
- Landed the `"01_catalog"` schema end-to-end: **9 tables** migrated, **19 dim rows** seeded, and verified the `chk_fct_nodes_effect_must_emit_audit` CHECK constraint both rejects `(kind=effect, emits_audit=false)` and accepts all three valid combinations (effect+audit, request, control).

## Task Commits

No git commits made during this plan — this session is a PAUL planning + APPLY + UNIFY loop. Commits will batch at phase close (Phase 2 complete) or at user's request.

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1: Protocol + ADR | — (part of phase batch) | docs | NCP v1 + ADR-027 published |
| Task 2: Schema + dim + EAV | — (part of phase batch) | feat | Migrations 001–002 + 4 seeds applied |
| Task 3: fct tables | — (part of phase batch) | feat | Migration 003 applied; CHECK constraint verified |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md` | Created | Authoritative NCP v1 spec (16 §s) |
| `03_docs/00_main/08_decisions/027_node_catalog_and_runner.md` | Created | Decision record |
| `.../01_catalog/09_sql_migrations/01_migrated/20260416_001_create-catalog-schema.sql` | Created | Schema + dim_entity_types + EAV foundation |
| `.../01_catalog/09_sql_migrations/01_migrated/20260416_002_catalog-dim-tables.sql` | Created | dim_modules / dim_node_kinds / dim_tx_modes |
| `.../01_catalog/09_sql_migrations/01_migrated/20260416_003_catalog-fct-tables.sql` | Created | fct_features / fct_sub_features / fct_nodes |
| `.../01_catalog/09_sql_migrations/seeds/01_dim_modules.yaml` | Created | 8 module rows |
| `.../01_catalog/09_sql_migrations/seeds/02_dim_node_kinds.yaml` | Created | 3 kind rows |
| `.../01_catalog/09_sql_migrations/seeds/03_dim_tx_modes.yaml` | Created | 3 tx mode rows |
| `.../01_catalog/09_sql_migrations/seeds/04_dim_entity_types.yaml` | Created | 5 entity type rows |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Migrations moved to `03_docs/features/00_setup/05_sub_features/01_catalog/...` (from plan draft's `backend/01_catalog/...`) | `.claude/rules/common/database.md` mandates distributed migrations under `03_docs/features/...`; consistency with existing `00_setup/00_bootstrap` pattern | Plans 02-02 + 02-03 will still build Python at `backend/01_catalog/` — SQL and code are deliberately separated |
| Catalog `fct_*` PKs are SMALLINT GENERATED IDENTITY (not UUID v7) | User override after surfacing the deviation; catalog entities are system-level, small IDs keep downstream index pages small, deterministic IDs simplify manifest upsert-by-key | `dtl_attrs.entity_id` is SMALLINT (matches fct PKs); catalog stands apart from app-level fct_* which remain UUID |
| CHECK constraint `chk_fct_nodes_effect_must_emit_audit` enforces at DB layer | NCP §4 says "effect nodes must emit audit"; DB-level enforcement means validator bugs can never produce non-compliant rows | Any future catalog writer (loader, hand-insert, seed) must respect this — impossible to bypass |
| Used CASE-based one-value-only CHECK on `dtl_attrs` (not `::int` casting) | More portable, readable, avoids implicit boolean-to-int semantics | Consistent with how future EAV tables in other schemas should express this invariant |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 0 | — |
| Scope additions | 0 | — |
| Spec corrections (surfaced + user-approved before execution) | 2 | Both applied cleanly; plan spec updated conceptually, SUMMARY records actual paths/types |
| Deferred | 0 | Logged to issues |

**Total impact:** Two spec-level corrections made *before* code was written (path convention + PK type). Neither is a fix-after-the-fact — both were surfaced at the start of Task 2 execute step and approved by the user. No scope creep.

### Spec Corrections

**1. Migration path convention**
- **Found during:** Task 2 execute pre-flight (re-reading `.claude/rules/common/database.md`)
- **Issue:** Plan spec had `backend/01_catalog/09_sql_migrations/...`; rules mandate `03_docs/features/{feat}/05_sub_features/{sub}/09_sql_migrations/...`
- **Fix:** Created new sub-feature `03_docs/features/00_setup/05_sub_features/01_catalog/` (alongside existing `00_bootstrap` from Phase 1); migrations + seeds live there
- **Files:** All 3 SQL migrations + 4 seed YAMLs
- **Verification:** Migrator `rglob` discovered the new location automatically; 4 migrations shown as applied in `runner status`

**2. Catalog `fct_*` PK type**
- **Found during:** Task 2 execute pre-flight
- **Issue:** Plan spec called for SMALLINT GENERATED IDENTITY PKs on `fct_features`, `fct_sub_features`, `fct_nodes`; `.claude/rules/common/database.md` requires VARCHAR(36) UUID v7 on all `fct_*`
- **Resolution:** User overrode — SMALLINT retained because catalog is system-level, not user data; deviation documented in `20260416_003_catalog-fct-tables.sql` header comment
- **Files:** `20260416_003_catalog-fct-tables.sql` + `dtl_attrs.entity_id` (SMALLINT to match)
- **Verification:** All FK constraints resolve; CHECK constraint test validated both positive and negative cases

### Deferred Items

None.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Postgres container was stopped (exited 3 days ago) | `docker compose up -d postgres` brought `tennetctl_v2-postgres-1` back; `pg_isready` confirmed accepting connections before continuing |

## Next Phase Readiness

**Ready:**
- Catalog DB schema exists and is migration-managed; any future `backend/01_catalog/loader.py` can upsert into these tables directly.
- Dim rows are stable — `1=request, 2=effect, 3=control` for kinds, `1=caller, 2=own, 3=none` for tx modes, entity types 1–5 — manifest loader (Plan 02-02) can hard-code these IDs.
- Execution policy columns (`timeout_ms`, `retries`, `tx_mode_id`) exist on `fct_nodes`, ready for runner (Plan 02-03) to read.
- `emits_audit` column + CHECK constraint enforce the audit discipline at the database — Python validator in 02-02 only needs to echo the same rule, not implement it solo.

**Concerns:**
- No Python `backend/01_catalog/` module exists yet — Plan 02-02 starts from scratch (intentional; kept 02-01 pure schema).
- Node handler_path strings are free-text TEXT — no structural validation at DB level. 02-02 validator will resolve via `importlib` at boot.
- Catalog has no feature rows yet. First real consumer (`iam` feature) lands in Plan 03-02 after 02-02 + 02-03 complete.

**Blockers:**
- None. Ready to start Plan 02-02 (manifest loader + boot upsert + validator + `/tnt` skill).

---
*Phase: 02-catalog-foundation, Plan: 01*
*Completed: 2026-04-16*
