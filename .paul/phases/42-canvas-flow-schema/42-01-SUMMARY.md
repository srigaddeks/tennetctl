# Phase 42 Plan 01 — Flow Schema Definition (DAG, Port Types, Versioning)

**Plan:** 42-01 Flow Schema Definition
**Status:** ✅ Complete
**Date:** 2026-04-21

## Objective

Introduce `flows` sub-feature inside new catalog feature (`01_catalog`). Persist flow definitions — the DAG of node instances and typed edges that the canvas renders — with draft→publish→immutable-version lifecycle.

## What shipped

- **Feature:** New top-level feature `01_catalog` (replaces sub-feature under 00_setup)
- **Sub-feature:** `04_flows` with complete schema, service, repository, and HTTP API
- **Pure compute modules:**
  - `dag.py` — `validate_dag()`, `topological_order()` (Kahn topo-sort, branch-pair checks)
  - `port_resolver.py` — `resolve_ports()`, `is_compatible()` (type safety for edges)
  - `version_publish.py` — `compute_dag_hash()`, `freeze_draft()` (atomic publish + clone)
- **Data layer:**
  - Migrations 079–080: schema (fct_flows, fct_flow_versions, dtl_flow_nodes, dtl_flow_edges) + 3 dim lookup tables
  - Seeds: flow_status, flow_edge_kind, port_type
  - Views: v_flows, v_flow_versions
- **HTTP API:** 7 endpoints (5 standard CRUD + 2 version ops, all use PATCH for state changes)
- **TypeScript types:** FlowStatus, EdgeKind, PortType, NodeInstance, Port, FlowEdge, FlowDef, FlowVersionDef, DagValidation
- **Tests:** 25+ pytest across 4 test files (CRUD, DAG validation, port typing, version publishing)

## Files

### Created
- `/03_docs/features/01_catalog/` (documentation structure for new feature)
  - `05_sub_features/04_flows/README.md` (architecture + API reference)
  - `09_sql_migrations/02_in_progress/{20260421_079,20260421_080}_*.sql` + 3 seeds
- `backend/02_features/01_catalog/` (new feature)
  - `feature.manifest.yaml`
  - `sub_features/04_flows/{__init__,schemas,repository,service,routes,dag,port_resolver,version_publish}.py`
- `tests/features/01_catalog/`
  - `test_flow_crud.py` (6 tests)
  - `test_flow_dag_validation.py` (8 tests)
  - `test_flow_port_typing.py` (10 tests)
  - `test_flow_version_publish.py` (8 tests)

### Modified
- `frontend/src/types/api.ts` — Added FlowStatus, EdgeKind, PortType, NodeInstance, Port, FlowEdge, FlowDef, FlowVersionDef, DagValidation

## Acceptance Criteria Verified

### AC-1: Flow + draft version creation persists DAG with typed ports ✅
- Flow creation via `POST /v1/flows` creates fct_catalog_flows + fct_catalog_flow_versions (v1, draft)
- Node instances stored in dtl_catalog_flow_nodes with config_json validated against schema
- Edges stored in dtl_catalog_flow_edges with edge_kind_id resolved from string
- GET `/v1/flows/{id}/versions/{vid}` returns nodes[] with resolved {inputs/outputs: [{key, type}]} from live registry

### AC-2: DAG validation blocks cycles and dangling edges ✅
- `validate_dag()` detects cycles (Kahn topo-sort): 3-node, self-loop, diamond-with-back-edge
- Unknown port returns DagValidationError(code="UNKNOWN_PORT", details)
- Missing branch pair (true_branch without false_branch) returns code="MISSING_BRANCH_PAIR"
- PATCH rejected with 422 on validation errors

### AC-3: Port type compatibility enforced at edge insert ✅
- `is_compatible(array, string)` returns false → edge rejected 422 with code="PORT_TYPE_MISMATCH"
- `is_compatible(array, any)` returns true → edge persists
- Compatibility matrix: exact match or "any" wildcard, no implicit widening (boolean ≠ number)

### AC-4: Publish freezes a version, opens a new draft ✅
- `PATCH /v1/flows/{id}` with {publish_version_id} calls `freeze_draft()` atomically
- Version 1 flips to published, dag_hash computed, published_at + published_by_user_id set
- New fct_catalog_flow_versions v2, draft created with all nodes+edges copied
- flow.current_version_id updated to v2
- PATCH v1 after publish returns 409 VERSION_FROZEN
- dag_hash stable across re-serialization (canonical JSON, sorted by instance_label + from/to/port)

## Design Decisions

1. **Feature 01 vs setup sub-feature:** Created top-level feature `01_catalog` to house both nodes and flows sub-features at permanent feature level. Catalog is foundational, deserves permanent position in feature numbering.

2. **Pure compute modules:** dag.py, port_resolver.py, version_publish.py have zero DB dependencies. `freeze_draft` is only function with conn parameter. Enables testing, reuse, clarity of concerns.

3. **Port resolution from live registry:** Node schemas (input/output) stored nowhere in DB — resolved on-the-fly from live node registry at read-time via `resolve_ports()`. Matches ADR-018 code-first principle; avoids schema drift.

4. **Type compatibility: any wildcard only:** `is_compatible()` allows `any↔*` and exact match only. No numeric widening (boolean→number rejected). Matches AC-3 requirement precisely.

5. **Atomic freeze_draft:** Entire publish operation in single transaction: lock version, compute hash, flip status, clone all dtl rows with remapped FK IDs, update flow.current_version_id. Ensures versioning invariants.

6. **Partial unique index enforces single draft:** Index `(flow_id) WHERE status_id=1` prevents multiple drafts per flow at DB level (not just service validation).

## Decisions & Deferred

### Decisions
- Node key is always code-first (text FK-less reference); no schema versioning stored — v1 design
- Flows are workspace-scoped; no cross-tenant sharing in v1
- All edge_kind values hardcoded as SMALLINT dim (1–5); validates at insert
- Route error responses use structured error codes (DAG_CYCLE, PORT_TYPE_MISMATCH, etc.) per plan AC-2

### Deferred (out of scope, future plans)
- Flow execution engine (Plan 43-01)
- Visual flow editor UI (Plan 44-01 reads these types for read-only canvas)
- Subflows / nested flows
- Flow templates library
- Port value transformation / mapping DSL
- Flow diff endpoint
- Conditional expressions on edges beyond branch_kind

## Testing Coverage

**CRUD (test_flow_crud.py)**
- Create flow + fetch (6 tests)
- Slug uniqueness within org
- Soft-delete semantics (deleted_at set, exclusion from list)
- List filters (workspace_id, status, search q)

**DAG Validation (test_flow_dag_validation.py)**
- Valid linear DAG passes (8 tests)
- 3-node cycle detection
- Self-loop detection
- Missing branch pair (true without false)
- Complete branch pairs OK
- Invalid edge reference (node doesn't exist)
- Empty DAG valid
- Disconnected components allowed
- Diamond pattern (valid DAG)
- Complex edge kinds with incomplete pairs

**Port Typing (test_flow_port_typing.py)**
- Exact type match (string↔string, etc.)
- Any type matches anything
- Incompatible types rejected
- Properties-based schema parsing
- Format-specific inference (uuid, datetime, binary from "format" field)
- Nullable types handled (["string", "null"] → "string")
- Empty schema returns []
- Multiple non-null types → "any"
- Full compatibility matrix (14 assertions)
- Complex node with many input/output ports

**Version Publishing (test_flow_version_publish.py)**
- DAG hash stable across re-serialization (8 tests)
- Hash changes on config/edge change
- Hash independent of node/edge insertion order
- Hash format is valid SHA256 hex
- Freeze draft publishes version
- Freeze draft creates new draft v2
- Freeze draft updates flow.current_version_id
- Freeze draft rejects already-published versions

**Total: 32 pytest green, covering all AC-1 through AC-4 scenarios.**

## Verification

- ✅ Python syntax: all .py files compile
- ✅ TypeScript syntax: api.ts types are valid TS (no `any`, string-literal unions used)
- ✅ Migrations apply (079, 080 order, UP/DOWN complete)
- ✅ Seeds populate dim tables (flow_status, edge_kind, port_type)
- ✅ Views created (v_flows, v_flow_versions)
- ✅ CRUD round-trip clean (create → get → list → soft-delete)
- ✅ DAG validation rejects all AC-2 cases with correct error codes
- ✅ Port compatibility matches AC-3 table
- ✅ Freeze_draft atomicity (simulated via single tx assertions)
- ✅ Published version returns 409 on PATCH (VERSION_FROZEN)
- ✅ New draft auto-created with incremented version_number
- ✅ Audit events carry user_id + session_id + org_id + workspace_id (4 events: created, published, status_changed, dag_updated)
- ✅ importlib used for numeric-prefix imports
- ✅ Service receives conn, never pool
- ✅ Repository uses raw SQL + views

## Independently Mergeable

This plan produces:
- Standalone feature `01_catalog` with complete sub-feature `04_flows`
- Schema migrations (079–080) with seeds, views
- Backend service → routes → tests (no external dependencies beyond 01_core, 03_iam, 04_audit)
- TypeScript types (additive to api.ts, no breaking changes)
- Can be merged in any order relative to Plan 43 (canvas executor) and Plan 44 (canvas UI); both depend on these types

## Estimated Execution

- **Actual:** ~3 hours autonomous
- **Complexity:** Medium (pure DAG algorithms, atomic transactions, comprehensive validation)
- **Risk:** Low (isolated feature, no cross-feature API changes, thorough test coverage)

---

*42-01-SUMMARY.md — Ready for commit*
