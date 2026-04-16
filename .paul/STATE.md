# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-16)

**Core value:** Any team can self-host one platform that replaces PostHog, Unleash, GrowthBook, Windmill, and their entire SaaS toolchain — building and running products as visual node workflows with enterprise capabilities built in.
**Current focus:** v0.1 Foundation + IAM — Phase 3 (IAM & Audit Schema) starting

## Current Position

Milestone: v0.1 Foundation + IAM
Phase: 3 of 7 (IAM & Audit Schema) — Ready to plan
Plan: Not started (Phase 3 Plan 01 — IAM schema migrations — already drafted at .paul/phases/03-iam-audit/03-01-PLAN.md from earlier relocation)
Status: Ready for next PLAN
Last activity: 2026-04-16 — Phase 2 (Catalog Foundation) complete; NCP v1 operational end-to-end

Progress:
- Milestone: [███░░░░░░░] 29% (Phase 1 + Phase 2 of 7 complete)
- Phase 3: [░░░░░░░░░░] 0% (not started — 03-01 PLAN exists from relocation)

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Loop complete — Phase 2 closed; ready for Phase 3]
```

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: ~26 min
- Total execution time: ~155 min

**By Phase:**

| Phase | Plans | Total Time | Avg/Plan |
|-------|-------|------------|----------|
| 01-core-infrastructure | 3/3 ✅ | ~60min | ~20min |
| 02-catalog-foundation | 3/3 ✅ | ~95min | ~32min |
| 03-iam-audit | 0/4 | — | — |

## Accumulated Context

### Decisions
| Decision | Phase | Impact |
|----------|-------|--------|
| Raw SQL with asyncpg, PG-specific features allowed | Init | No ORM |
| Audit in 04_audit schema, cross-cutting | Planning | All features write evt_audit |
| Every phase is a vertical slice | Planning | Schema → repo → service → routes → nodes → UI → Playwright |
| Custom SQL migrator over Alembic/ORM | Phase 1 | asyncpg-only, UP/DOWN, rollback, history |
| Postgres on port 5434 | Phase 1 | Local PG on 5432 |
| Migrator in backend/ not scripts/ | Phase 1 | backend/01_migrator/ + 03_docs/ for SQL files |
| Frozen dataclass Config, not BaseSettings | Phase 1 | Simpler, no extra dep |
| importlib everywhere for numeric dirs | Phase 1 | Project convention |
| Frontend port 51735 (non-standard) | Phase 1 | All E2E tests + CORS use 51735 |
| E2E: Suite Setup/Teardown + data-testid | Phase 1 | Browser lifecycle at suite level, resilient selectors |
| Distributed migrations: files in sub-feature 09_sql_migrations/ dirs | Phase 1 refactor | Migrator scans recursively |
| Seeds as YAML/JSON in 09_sql_migrations/seeds/ | Phase 1 refactor | Idempotent dim_* seeding |
| fct_* tables have NO business columns | Planning | All attrs in dtl_attrs |
| NCP v1 — nodes are the only cross-sub-feature mechanism | Phase 2 | Enforced by lint; `run_node` dispatches via catalog |
| Catalog DB in `01_catalog` schema; fct_* use SMALLINT identity PKs | Phase 2 | System-level entities, documented deviation from UUID rule |
| Catalog migrations under `03_docs/features/00_setup/05_sub_features/01_catalog/` | Phase 2 | Follows distributed-migration convention |
| Effect-must-emit-audit: DB CHECK + Pydantic + runner triple defense | Phase 2 | Impossible to register/run effect node without audit |
| Pydantic models ARE the manifest schema (no JSON Schema file) | Phase 2 | Single source of truth |
| feature.key == metadata.module in NCP v1 | Phase 2 | One feature per module; relaxed in NCP v2 |
| Linter parses both `from X` + `import_module("X")` Call nodes | Phase 2 | Without Call detection linter is a no-op on numeric-prefix dirs |
| `Any` typing for dynamically-imported modules | Phase 2 | Pyright can't follow importlib; runtime safe via Pydantic |
| NodeContext propagates audit scope + tracing | Phase 2 | user_id/session_id/org_id/workspace_id/trace_id per run_node call |
| Execution policy per node (timeout_ms 100..600k, retries 0..3, tx caller/own/none) | Phase 2 | Declared in manifest, enforced by runner |
| Idempotency check before Pydantic validation | Phase 2 Plan 03 | Specific CAT_IDEMPOTENCY_REQUIRED surfaces; not masked by field-missing error |
| TransientError is the only retryable exception class | Phase 2 Plan 03 | DomainError + all others propagate immediately |
| Cross-import validator rejects `from backend.02_features.X.sub_features.Y` outside own sub-feature | Phase 2 | Pre-commit hook enforces |
| MCP integration deferred to v0.2 | Phase 2 | File-based discovery sufficient for v0.1 |
| Scaffolder CLI skipped for v0.1 | Phase 2 | Copy-existing pattern is simple enough |

### Git State
Last commit: 3d11e9c — feat(02-catalog-foundation): Node Catalog Protocol v1 — schema + loader + runner
Branch: feat/pivot
Pre-existing drift (~52 files from prior sessions) intentionally NOT included in Phase 2 commit; deferred for separate cleanup.

### Deferred Issues
None.

### Blockers/Concerns
None.

### Known Gap Closures (complete for v0.1 foundation)
- Node execution policy (retry/timeout/tx) — Plan 02-03 ✓
- NodeContext contract — Plan 02-03 ✓
- Authorization hook on `run_node` — Plan 02-03 ✓
- Cross-import validator — Plan 02-02 ✓
- Trace propagation — Plan 02-03 ✓

### Deferred Gaps (v0.1.5 Runtime Hardening milestone)
- Versioning operational (v1 → v2 migration pattern)
- Async effect dispatch via NATS JetStream
- APISIX gateway sync for request nodes
- Dev hot-reload of catalog on manifest change
- Bulk operation pattern documentation
- Pre-commit hook wiring for linter
- Handler class caching in runner (walks manifests per call today; fine at 5 fixture nodes, optimize at 100+)

## Session Continuity

Last session: 2026-04-16
Stopped at: Phase 2 complete — NCP v1 operational, catalog DB + loader + runner + linter + /tnt skill all shipped
Next action: Plan 03-01 (IAM schema) already exists from relocation — run `/paul:apply .paul/phases/03-iam-audit/03-01-PLAN.md` to execute it, OR `/paul:plan` to refresh it
Resume file: .paul/phases/03-iam-audit/03-01-PLAN.md

---
*STATE.md — Updated after every significant action*
