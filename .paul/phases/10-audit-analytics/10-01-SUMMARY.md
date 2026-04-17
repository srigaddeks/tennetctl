---
phase: 10-audit-analytics
plan: 01
subsystem: audit-analytics
tags: [postgres, asyncpg, pydantic, fastapi, cursor-pagination, audit, node-catalog, jinja-none]

requires:
  - phase: 03-iam-audit
    provides: evt_audit table + audit.events.emit node (write path)
  - phase: 02-catalog-foundation
    provides: NCP v1 + run_node dispatcher
  - phase: 08-auth
    provides: session middleware injecting user_id/session_id/org_id/workspace_id into request.state
provides:
  - dim_audit_categories + dim_audit_event_keys typed taxonomy
  - v_audit_events read-path view (label-resolving LEFT JOIN)
  - /v1/audit-events list/detail/stats endpoints + /v1/audit-event-keys
  - audit.events.query control node (cursor-paginated, read-only, no audit emission)
  - AuditEvent* TypeScript types in frontend/src/types/api.ts
  - upsert_event_key repository helper for future auto-sync
affects:
  - 10-02 (Audit Explorer UI — consumes these endpoints + TS types)
  - 10-03 (Funnel / retention — extends stats endpoint)
  - 10-04 (Outbox + subscribe — depends on v_audit_events shape)
  - 11-02 (Notify subscriptions — will consume audit.events.query via run_node)
  - 12-* (IAM security events — will register event keys via upsert_event_key)

tech-stack:
  added: []   # no new libraries — reused asyncpg / Pydantic / FastAPI
  patterns:
    - cursor pagination on UUID v7 via (created_at, id) compound tuple compare
    - glob matching on event_key via LIKE with * → % translation
    - metadata substring via `metadata::text ILIKE` (tsvector deferred)
    - read-path node pattern (control, tx=caller, emits_audit=false)
    - fire-and-forget audit-of-reads from HTTP (own conn, log-and-swallow)
    - cross-org fail-closed authz at route layer (session org_id injected into filter)
    - dim tables join evt_audit via TEXT code (no FK) — preserves emit backward compat

key-files:
  created:
    - 03_docs/features/04_audit/05_sub_features/01_events/00_bootstrap/09_sql_migrations/01_migrated/20260416_016_audit-taxonomy-and-view.sql
    - 03_docs/features/04_audit/05_sub_features/01_events/00_bootstrap/09_sql_migrations/seeds/04audit_categories.yaml
    - backend/02_features/04_audit/sub_features/01_events/schemas.py
    - backend/02_features/04_audit/sub_features/01_events/repository.py
    - backend/02_features/04_audit/sub_features/01_events/service.py
    - backend/02_features/04_audit/sub_features/01_events/routes.py
    - backend/02_features/04_audit/sub_features/01_events/nodes/query_events.py
    - backend/02_features/04_audit/routes.py
    - tests/test_audit_events_query.py
  modified:
    - backend/02_features/04_audit/feature.manifest.yaml
    - backend/main.py
    - frontend/src/types/api.ts

key-decisions:
  - "No FK on evt_audit.category_id — keep audit_category TEXT + existing CHECK; dim joins by code"
  - "dim_audit_categories plain SMALLINT (seeded with fixed ids); dim_audit_event_keys IDENTITY (dynamic)"
  - "Node tx=caller (not none as planned) — query needs ctx.conn (matches featureflags.flags.get)"
  - "HTTP reads emit audit.events.queried (fire-and-forget, separate conn); node reads do not"
  - "Cross-org filter guard at HTTP layer; service layer stays composable for admin surfaces"

patterns-established:
  - "Read-path control node + query HTTP endpoints live in same sub-feature as the write node"
  - "Route declares audit-of-reads in its own catch; failure-to-audit never fails the read"
  - "Cursor is base64url JSON {created_at,id}; decode raises ValueError → 400"

# Metrics
duration: ~22min
started: 2026-04-16T22:55:00Z
completed: 2026-04-16T23:17:00Z
---

# Phase 10 Plan 01: Audit Taxonomy + Query API Summary

**PostHog-class read surface over evt_audit shipped: typed taxonomy, 4 HTTP endpoints, `audit.events.query` control node, 21 integration tests green, catalog registered.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~22 min |
| Started | 2026-04-16T22:55:00Z |
| Completed | 2026-04-16T23:17:00Z |
| Tasks | 3/3 completed |
| Files modified | 12 (9 created, 3 modified) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Taxonomy migration (dim tables + view) | ✅ Pass (deviated) | No FK on evt_audit — kept audit_category TEXT. Simpler, back-compat with emit. View LEFT JOINs by TEXT code. UP + DOWN both verified clean. |
| AC-2: List + cursor pagination + glob + filter combos | ✅ Pass | 12 filter-focused tests cover exact key, glob `iam.orgs.*`, outcome, category, org, actor, trace, time range, metadata substring, combinations. Cursor round-trip: 50 rows / 5 pages / zero dupes. |
| AC-3: Detail + stats + registered-keys | ✅ Pass | GET /{id} resolves labels via view; stats hour/day buckets + by_event_key top-N + by_outcome + by_category all match manual count. /v1/audit-event-keys returns registered set. |
| AC-4: `audit.events.query` node + pytest | ✅ Pass | Node registered in catalog as control/emits_audit=false. Shape-equality vs HTTP. Zero audit rows emitted by node invocation (verified before/after count). Cross-org authz rejects with 403 when session org ≠ filter org; auto-injects filter when missing. |

## Accomplishments

- **Audit read path online end-to-end** — every Phase 11 Notify subscription and Plan 10-02 UI can now page events with rich filters via HTTP or `run_node("audit.events.query", ...)`.
- **Typed taxonomy without breaking the write path** — `dim_audit_categories` + `dim_audit_event_keys` added cleanly; the existing `audit.events.emit` node and its CHECK constraint are untouched, meaning every already-emitted row in the 110-row corpus shows up in `v_audit_events` with resolved `category_label` on first query.
- **21 integration tests over the live DB** — covers filters, pagination, stats, node-HTTP shape equality, no-audit-on-node, and two authz fail-closed cases. Full suite (skipping pre-existing migrator drift) went from 178 → 199 green.
- **Pyright zero-error** on audit module + tests.

## Task Commits

Not committed yet — Phase 8-02 parked work, Plan 10-01 deltas, and prior uncommitted Phase 4-6/9 work are all in the working tree. Unified commit deferred to a later plan (likely bundled with Plan 10-02 or a dedicated commit pass).

| Task | Status | Description |
|------|--------|-------------|
| Task 1: Taxonomy migration + seed + view | ✅ Done | 20260416_016 + seed YAML + v_audit_events view |
| Task 2: Query sub-feature + node + manifest + router + TS types | ✅ Done | 5 Python files + audit router + manifest + main.py + api.ts |
| Task 3: Pytest 18+ cases | ✅ Done | 21 cases (3 bonus — actor_user_id, trace_id, daily-bucket, metadata-substring) |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `20260416_016_audit-taxonomy-and-view.sql` | Created | dim_audit_categories + dim_audit_event_keys + v_audit_events view |
| `seeds/04audit_categories.yaml` | Created | 4 canonical category rows (system/user/integration/setup), idempotent |
| `sub_features/01_events/schemas.py` | Created | Pydantic v2 models for filter/list/detail/stats/keys |
| `sub_features/01_events/repository.py` | Created | asyncpg queries, cursor codec, filter builder, upsert helper |
| `sub_features/01_events/service.py` | Created | Thin wrapper around repo (service-layer reserved for future policy) |
| `sub_features/01_events/routes.py` | Created | 4 GET endpoints + cross-org guard + fire-and-forget audit-of-reads |
| `sub_features/01_events/nodes/query_events.py` | Created | control node `audit.events.query` (tx=caller, emits_audit=false) |
| `backend/02_features/04_audit/routes.py` | Created | Feature-level APIRouter aggregating sub-feature routers |
| `backend/02_features/04_audit/feature.manifest.yaml` | Modified | Added query node + 4 route entries under audit.events sub-feature |
| `backend/main.py` | Modified | Uncommented audit module in MODULE_ROUTERS (1 line) |
| `frontend/src/types/api.ts` | Modified | +76 lines — all AuditEvent* types for Plan 10-02 consumption |
| `tests/test_audit_events_query.py` | Created | 21 integration tests |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| No FK on evt_audit → dim_audit_categories; keep audit_category TEXT + CHECK unchanged | Deferred emit-node rewrite; preserves full backward compat; dim join by TEXT code costs nothing at read time | `audit.events.emit` unchanged. Future plan can cut evt_audit over to category_id when worthwhile. |
| `dim_audit_categories` plain SMALLINT PK (seeded), `dim_audit_event_keys` IDENTITY PK | Matches project dim_* convention for static-seeded vs dynamically-populated dims | Ambiguity-free: categories are immutable contract, event keys grow over time |
| Node uses `tx=caller`, requires `ctx.conn` | Matches `featureflags.flags.get` pattern; `tx=none` (as planned) is wrong — node needs a conn | Callers must pass conn via NodeContext (already the runner pattern); simpler than extracting pool from ctx.extras |
| HTTP list route emits `audit.events.queried` fire-and-forget in a separate conn | Audit-of-reads contract (vault precedent) without coupling read tx to audit tx | Node-level reads still bypass; hot-path perf unaffected |
| Cross-org authz at route layer, not service | Service stays composable for admin surfaces; HTTP layer fail-closes when session has org_id | Future admin UI can call service directly with any org_id |
| Migration number 016 (not 010 as planned) | 015 was the latest — plan was written before featureflags migrations landed | One-line deviation; filename correct |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 2 | Essential fixes caught during Task 1 |
| Scope additions | 2 | Better authz + 3 bonus tests |
| Deferred | 3 | Logged below |

**Total impact:** Minor — all deviations improve correctness or match existing project conventions.

### Auto-fixed Issues

**1. [DB convention] dim table identity generation**
- **Found during:** Task 1 (seed step)
- **Issue:** Migration created dim_audit_categories with `GENERATED ALWAYS AS IDENTITY`, causing seeder to fail with "cannot insert a non-DEFAULT value into column 'id'" when YAML specified ids.
- **Fix:** Changed to plain `SMALLINT NOT NULL` (matches existing dim_* convention in 01_catalog, 03_iam). Removed inline INSERT from migration; seed YAML is now the authoritative seed path. Kept IDENTITY on dim_audit_event_keys since it's dynamically populated.
- **Files:** 20260416_016 migration
- **Verification:** rollback + re-apply + `seed` twice (4 rows first, 0 skipped second) ✅

**2. [Node contract] tx_mode for query node**
- **Found during:** Task 2 (writing query_events.py)
- **Issue:** Plan specified `tx=none`, but existing control nodes (`featureflags.flags.get`) use `tx=caller` and rely on `ctx.conn`. `tx=none` means no conn available, which the query node needs.
- **Fix:** Used `tx=caller` in both the manifest and the node's runtime check.
- **Files:** feature.manifest.yaml, nodes/query_events.py
- **Verification:** Node dispatches correctly via `run_node` in tests; emit-count test passes ✅

### Scope Additions

**1. Cross-org authz enforcement at HTTP layer**
- Plan mentioned "authz rejection when session org ≠ filter org" in AC-4 as a single test, but implementation required structural decisions about where the guard lives. Added `_enforce_org_authz()` at the route layer (fail-closed + filter auto-injection). Service layer stays composable.

**2. Bonus tests (18 → 21)**
- Added: `test_filter_by_actor_user_id`, `test_filter_by_trace_id`, `test_filter_metadata_substring`, `test_stats_daily_bucket`, `test_authz_forces_session_org_when_filter_missing`. Each covers a filter/guard path not originally enumerated but cheap to include while the seeded corpus was warm.

### Deferred Items

- **Auto-sync event keys from observed evt_audit on boot** (Plan 10-04 or dedicated admin script). `upsert_event_key` helper exists; wiring into boot lifecycle deferred.
- **Manifest-side event-key registration** (Plan 10-04). Features could declare their event keys in feature.manifest.yaml for auto-upsert at catalog boot.
- **tsvector full-text index on metadata** — current `metadata::text ILIKE` is OK for the current corpus; upgrade if query perf degrades at scale.
- **Actor display-name enrichment in v_audit_events** — explicit non-goal per plan boundaries; Audit Explorer UI (Plan 10-02) will resolve actor → user display_name client-side.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Seeder failed on GENERATED ALWAYS identity column | Rolled back migration, changed dim_audit_categories to plain SMALLINT (matches convention), re-applied. ~2 min deviation. |
| `datetime.utcnow()` deprecation warning in one test | Replaced with `datetime.now(timezone.utc).replace(tzinfo=None)`; pyright clean. |

## Next Phase Readiness

**Ready:**
- Plan 10-02 (Audit Explorer UI — now a **full vertical** per user directive: TS hooks + pages + Robot E2E) has typed API + working endpoints to consume. All 12 AuditEvent* TS types live in `frontend/src/types/api.ts`.
- Plan 10-04 (Outbox) has a stable `v_audit_events` read shape to base the subscribe contract on.
- Phase 11 Notify subscription workers can now dispatch `audit.events.query` via `run_node` for replay/backfill.

**Concerns:**
- Emitting `audit.events.queried` inside the list route runs a second `audit.events.emit` per call. At scale this doubles writes. Rate-limit or batch-buffer in Plan 10-04.
- Cross-org authz relies on session middleware populating `request.state.org_id`. If a route bypasses middleware (e.g. internal health probe), the guard becomes a no-op. Keep in mind when adding admin surfaces.

**Blockers:** None.

---
*Phase: 10-audit-analytics, Plan: 01*
*Completed: 2026-04-16*
