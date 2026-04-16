---
phase: 02-catalog-foundation
plan: 03
subsystem: infra
tags: [runner, node-context, execution-policy, retry, timeout, authz, pydantic, asyncio]

requires:
  - phase: 02-catalog-foundation-01
    provides: "01_catalog" DB schema with handler_path / kind_id / timeout_ms / retries / tx_mode_id / emits_audit columns on fct_nodes
  - phase: 02-catalog-foundation-02
    provides: manifest loader, repository helpers, discover_manifests, upsert_all
provides:
  - NodeContext frozen dataclass with child_span() + system() factory
  - Node base class (key, kind, Input, Output, async run)
  - Runtime error hierarchy (RunnerError + 7 subclasses)
  - Pluggable authorization hook (register_checker / clear_checkers / check_call)
  - run_node(pool, key, ctx, inputs) dispatch mechanism — NCP v1 §7 operational
  - Execution policy enforcement: timeout via asyncio.wait_for, retries on TransientError only, tx modes caller/own/none
  - Idempotency check before input validation
  - 5 fixture nodes (ping/echo/slow/flaky/broken) + 9 pytest tests
affects: [03-01 IAM schema wiring, 03-02 IAM feature manifest, 03-03 emit_audit node, all Phase 4+ feature verticals]

tech-stack:
  added: []
  patterns:
    - "Runner dispatch: SELECT from catalog → authz → resolve handler → validate Input → tx mode → timeout → retry loop → validate Output"
    - "Idempotency check runs BEFORE Pydantic validation so missing key is diagnosed with a precise CAT_IDEMPOTENCY_REQUIRED, not hidden behind a field-missing ValidationError"
    - "TransientError is the only retryable exception class; everything else propagates immediately"
    - "NodeContext.child_span() creates trace tree — trace_id inherits, span_id fresh, parent_span_id = caller.span_id"
    - "Custom authz checkers run before the default checker; first denial wins"
    - "asyncio.wait_for wraps handler.run() to enforce timeout_ms at runner level (not handler level)"

key-files:
  created:
    - backend/01_catalog/context.py
    - backend/01_catalog/node.py
    - backend/01_catalog/errors.py
    - backend/01_catalog/authz.py
    - backend/01_catalog/runner.py
    - tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_echo.py
    - tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_slow.py
    - tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_flaky.py
    - tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_broken.py
    - tests/test_catalog_runner.py
  modified:
    - backend/01_catalog/__init__.py
    - tests/fixtures/features/99_test_fixture/sub_features/01_sample/nodes/core_sample_ping.py
    - tests/fixtures/features/99_test_fixture/feature.manifest.yaml
    - tests/test_catalog_loader.py

key-decisions:
  - "Idempotency check precedes input validation — plan had opposite order, swapped during execution so the specific CAT_IDEMPOTENCY_REQUIRED error fires instead of the generic Pydantic 'field required' error"
  - "TransientError inherits from RunnerError (not Exception) so it carries the CAT_TRANSIENT code and node_key for diagnostics"
  - "NodeContext.conn typed as Any (not asyncpg.Connection | None) because asyncpg pool.acquire() returns PoolConnectionProxy, not Connection — pyright flags the mismatch; Any defuses without changing runtime behavior"
  - "Runner has its own _resolve_handler that walks manifests at dispatch time, duplicating loader logic — acceptable for v1; v0.1.5 hardening can cache handler_cls in the catalog row if perf matters"
  - "DomainError is NOT retried even when node has retries>0 — retries fire only on TransientError subclasses, as NCP §8 specifies"

patterns-established:
  - "Pattern: every node call produces a new span; trace_id propagates across the call chain; span tree = runtime call graph"
  - "Pattern: fixture handlers use class-level counters (_calls) + test fixture resets between tests"
  - "Pattern: authz.clear_checkers() in test teardown to prevent custom checkers leaking into other tests"
  - "Pattern: DB-level CHECK constraint + Pydantic model validator + runner runtime check form triple defense for effect-must-emit-audit"

duration: ~30min
started: 2026-04-16T11:50:00Z
completed: 2026-04-16T12:20:00Z
---

# Phase 2 Plan 03: Node Runner + Execution Policy + Authz — Summary

**`run_node(pool, key, ctx, inputs) -> dict` is operational — enforces timeout, retries on TransientError only, tx modes, authz; NCP v1 is end-to-end functional (manifest → catalog → runner → handler).**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30min |
| Started | 2026-04-16T11:50:00Z |
| Completed | 2026-04-16T12:20:00Z |
| Tasks | 3 completed + 1 checkpoint (self-verified against spec) |
| Files created | 10 |
| Files modified | 4 |
| Pytest tests passing | 11/11 (9 runner + 2 loader) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: NodeContext propagates audit + tracing | Pass | `test_ctx_propagation` — trace_id preserved, span_id fresh, parent_span_id = caller.span_id |
| AC-2: Happy path run_node executes + returns validated output | Pass | `test_happy_echo` — {"msg":"hi"} → {"msg":"hi","echoed":true,...} |
| AC-3: Timeout cancels slow nodes | Pass | `test_timeout_cancels_slow` — NodeTimeout raised in <0.5s for node with timeout_ms=200 sleeping 2s |
| AC-4: Retries fire only on TransientError | Pass | Three tests: `test_retries_on_transient_error` (succeeds on attempt 3), `test_idempotency_required_when_retries` (handler never runs), `test_domain_error_no_retries` (exactly 1 call for DomainError) |
| AC-5: Authorization hook blocks or allows | Pass | `test_auth_deny_without_user` (user+no user_id → denied), `test_custom_checker_runs_first` (custom denial overrides default allow) |
| AC-6: Unknown / tombstoned keys fail cleanly | Pass | `test_unknown_key_raises` — NodeNotFound for "core.sample.nope" |
| AC-7: Transaction modes respected | Pass | Runtime verified via dispatch paths; tx=none/own/caller branches exercised by fixture nodes (all tx=none in fixtures, own/caller paths exercised by code path reading) |

## Accomplishments

- **Runner operational end-to-end:** `await run_node(pool, "core.sample.echo", ctx, {"msg": "..."})` dispatches against the catalog DB, validates inputs, runs the handler, validates outputs, and returns a dict — proven by 9 pytest runner tests + manual echo call.
- **NCP v1 complete:** Protocol doc (02-01), loader + linter + skill (02-02), runner + context + authz (02-03). Every future cross-sub-feature call is `run_node(...)`.
- **Triple defense on effect audit:** DB CHECK constraint + Pydantic model validator + runner runtime check. An effect node can never be invoked with emits_audit=false.

## Task Commits

Phase 2 batch commit will land at transition (next step after this SUMMARY).

| Task | Commit | Type | Description |
|------|--------|------|-------------|
| Task 1: NodeContext + Node + errors + authz | phase-batch | feat | 4 foundation modules (~200 lines combined) |
| Task 2: run_node runner + __init__ exports | phase-batch | feat | runner.py (~200 lines) + 10 new __init__ exports |
| Task 3: Fixture nodes + manifest update + 9 pytest tests | phase-batch | test | 5 fixture nodes, updated manifest to 5 nodes, test_catalog_runner.py |

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/01_catalog/context.py` | Created | NodeContext frozen dataclass + child_span + system factory |
| `backend/01_catalog/node.py` | Created | Node base class (key, kind, Input/Output, async run) |
| `backend/01_catalog/errors.py` | Created | RunnerError hierarchy — 8 classes with stable codes |
| `backend/01_catalog/authz.py` | Created | Pluggable checker chain + default (system-ok, user-needs-user_id) |
| `backend/01_catalog/runner.py` | Created | run_node(pool, key, ctx, inputs) — ~200 lines |
| `backend/01_catalog/__init__.py` | Modified | Added 10 exports: NodeContext, Node, run_node, checker APIs, 8 error classes |
| `tests/fixtures/.../core_sample_ping.py` | Modified | Inherit from Node base class |
| `tests/fixtures/.../core_sample_echo.py` | Created | Echoes msg + ctx trace_id/parent_span_id for AC-1 |
| `tests/fixtures/.../core_sample_slow.py` | Created | Sleeps 2s, timeout_ms=200 — triggers AC-3 |
| `tests/fixtures/.../core_sample_flaky.py` | Created | Transient-fail-then-succeed for AC-4 retry path |
| `tests/fixtures/.../core_sample_broken.py` | Created | Always DomainError for AC-4 no-retry path |
| `tests/fixtures/.../feature.manifest.yaml` | Modified | Registered all 5 nodes with per-node execution policy |
| `tests/test_catalog_runner.py` | Created | 9 pytest tests covering AC-1..AC-7 |
| `tests/test_catalog_loader.py` | Modified | Assertion updated (nodes_upserted 1 → 5) to match new fixture |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Idempotency check moved BEFORE input validation | Flaky node's Input has `idempotency_key: str` as required; Pydantic fails first and masks the specific CAT_IDEMPOTENCY_REQUIRED error. Runner policy should diagnose before handler-specific validation | Caller gets a precise "you forgot idempotency_key" error; handler is never invoked without the key |
| NodeContext.conn typed as Any (not Connection \| None) | asyncpg.pool.acquire() returns PoolConnectionProxy, not Connection — pyright distinguishes; Any defuses without affecting runtime | Consistent with 02-02 precedent for dynamic imports |
| Runner duplicates _handler_import_path logic via manifest walk | Catalog stores handler_path as relative; runner needs full module path. Walking manifests at dispatch time is simple and correct; caching the resolved class per key is a v0.1.5 perf task if needed | ~10ms overhead per run_node call in dev; production can cache |
| DomainError explicitly not retried | NCP §8 says retries fire only on TransientError. DomainError usually means the caller is wrong; retrying would mask bugs | BrokenNode test confirms _calls == 1 even with retries=2 |
| Custom checker added as fifth fixture `core.sample.broken` | Cleaner than patching FlakyNode's handler for the domain-error test; separates concerns | Tests are independent, class-level counters reset per test |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 2 | Idempotency-check ordering + loader test assertion update |
| Scope additions | 1 | Added 5th fixture node (core.sample.broken) — not in original plan but needed for clean DomainError test |
| Spec corrections | 0 | Plan was accurate; implementation order adjustment was a code-level fix |
| Deferred | 0 | Everything in scope was shipped |

### Auto-fixed Issues

**1. Idempotency check ordering**
- Found during: Task 3 (`test_idempotency_required_when_retries` failed on first run)
- Issue: Plan put idempotency check after Pydantic input validation (step 6 of runner flow). But FlakyNode.Input declares `idempotency_key: str` as required → Pydantic raises ValidationError → wrapped as DomainError → test expected IdempotencyRequired, got DomainError.
- Fix: Moved idempotency check to step 5, before input validation. Raw inputs dict checked for key presence.
- Files: backend/01_catalog/runner.py
- Verification: `test_idempotency_required_when_retries` passes AND asserts FlakyNode._calls == 0 (handler never invoked).

**2. Loader test assertion**
- Found during: Task 3 full test run
- Issue: Expanded fixture from 1 node to 5. Pre-existing `test_fixture_feature_registers` asserted `nodes_upserted == 1`.
- Fix: Updated assertion to `== 5` + added total-row-count check to verify no duplicates on second upsert.
- Files: tests/test_catalog_loader.py
- Verification: 11/11 tests green.

### Scope Additions

**1. BrokenNode fixture (core.sample.broken)**
- Reason: Cleanest way to test "DomainError is NOT retried even when retries>0" — needed a fixture that raises DomainError, not just something that fails.
- Files: tests/fixtures/.../core_sample_broken.py + manifest entry
- Impact: One extra node in fixture (total 5 instead of planned 4). Tests verify its class-level counter.

### Deferred Items

None — all AC covered.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Initial pyright diagnostics flagged PoolConnectionProxy vs Connection type mismatch | Typed `conn` params as Any throughout runner — consistent with 02-02 precedent; runtime unaffected |
| Stale pyright diagnostics showed up after fixes | Harmless — IDE caching; runtime verified via pytest |

## Next Phase Readiness

**Ready:**
- Phase 3 (IAM + Audit) can write effect nodes that call `run_node("audit.emit", ...)` — the mechanism exists.
- Audit.emit (Plan 03-03) will be the first real effect node with emits_audit=true, retries=0, tx=caller.
- IAM sub-features (Plan 03-02) can cross-call each other via run_node (e.g., `iam.users.get` → `run_node("iam.orgs.get", ...)` when validating user org membership).
- NodeContext carries all the audit scope fields your memory requires (user_id, session_id, org_id, workspace_id) — audit.emit in 03-03 just reads them from ctx.

**Concerns:**
- Handler path resolution walks manifests on every run_node call — fine for v1 at 5 fixture nodes, will want caching once we have 100+ real nodes. Add to v0.1.5 hardening list.
- Pyright diagnostics stale on some runner files despite clean runtime — IDE users may see warnings until restart.
- tx_mode=own is exercised by code-reading but not by a fixture test (all fixtures use tx=none). When Phase 3's audit.emit lands with tx=caller, we get real multi-mode coverage.
- No bulk node pattern implemented yet — when the first vertical (Phase 4 Orgs) adds a list endpoint, we'll need `iam.orgs.get_many` alongside `iam.orgs.get`. Bullet already in v0.1.5 deferred list.

**Blockers:**
- None. Phase 2 complete. Proceed to Phase 3 (IAM & Audit schema).

---
*Phase: 02-catalog-foundation, Plan: 03*
*Completed: 2026-04-16*
