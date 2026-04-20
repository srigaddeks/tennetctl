---
phase: 43-canvas-backend
plan: 01
type: summary
completed_at: 2026-04-21
---

# Plan 43-01 — Canvas Renderer Backend (COMPLETE)

**Status:** ✅ All tasks delivered. Ready for React Flow frontend (Plan 44-01).

---

## Execution Summary

| Task | Status | Details |
|------|--------|---------|
| 1. Migrations + views | ✅ | `20260422_081_catalog-canvas-trace.sql` + seeds created |
| 2. Pure compute modules | ✅ | `port_index.py`, `layout.py`, `trace_assembler.py` |
| 3. Sub-feature scaffold | ✅ | `schemas.py`, `repository.py`, `service.py` |
| 4. Routes (read-only) | ✅ | 2 GET endpoints: canvas payload + run list |
| 5. Tests + types | ✅ | 4 test files (16+ pytest), TypeScript types updated |

---

## What Shipped

### Database

- **Migration:** `20260422_081_catalog-canvas-trace.sql`
  - `dim_catalog_trace_node_status` (6 seeded statuses: pending, running, success, failure, skipped, timed_out)
  - `v_catalog_flow_run_node_status` — DISTINCT ON view for latest node status per run
  - `v_catalog_flow_run_edge_traversal` — edge traversal projection (traversed=true when from succeeded AND to has event)

- **Seed:** `01catalog_05_dim_trace_node_status.yaml` — all 6 statuses pre-populated

### Backend (Python)

**Sub-feature:** `backend/02_features/01_catalog/sub_features/05_canvas/`

- **`__init__.py`** — Sub-feature marker
- **`schemas.py`** — Pydantic v2 models:
  - `CanvasPort`, `CanvasNodePorts`, `CanvasNode`, `CanvasEdge`, `CanvasLayoutEntry`, `TraceNodeStatus`, `CanvasTrace`, `CanvasPayload`
  - `FlowRunSummary` — for trace picker

- **`port_index.py`** (pure compute)
  - `build_port_index(node_keys, registry) -> dict[str, ResolvedPorts]`
  - Single bulk registry walk, deduplicates keys, returns sentinel `unresolved=true` for missing nodes
  - Resolves input/output ports from node JSON schemas

- **`layout.py`** (pure compute)
  - `topological_levels(nodes, edges) -> dict[node_id, int]` — Kahn algorithm for longest-path levels
  - `compute_layout(nodes, edges) -> dict[node_id, {x, y, lane}]`
    - x = level × 240px
    - y = lane × 120px (stable sort by instance_label within level)
    - Operator-set position_x/position_y overrides automatic placement
    - Deterministic across reruns

- **`trace_assembler.py`** (pure compute)
  - `assemble_trace(run_node_rows, run_edge_rows, version_nodes, version_edges) -> CanvasTrace`
  - Per-node status (pending/running/success/failure/skipped/timed_out)
  - Per-edge traversal (true when from reached success AND to has event)
  - Propagates skipped downstream of failures
  - Computes started_at, finished_at, total_duration_ms

- **`repository.py`** (asyncpg, read-only)
  - `load_version_dag(conn, flow_id, version_id) -> dict | None` — reuses flows.repository
  - `load_run_node_status(conn, flow_run_id)` — reads v_catalog_flow_run_node_status
  - `load_run_edge_traversal(conn, flow_run_id)` — reads v_catalog_flow_run_edge_traversal
  - `list_runs(conn, version_id, filters) -> list[dict]` — filtered run summaries

- **`service.py`** (orchestration)
  - `assemble_canvas(conn, flow_id, version_id, trace_id=None, registry=None) -> CanvasPayload`
  - Single transaction (READ ONLY)
  - Loads DAG, resolves ports (bulk), computes layout, optionally assembles trace
  - Returns complete 5-key payload: nodes, edges, ports, layout, trace

- **`routes.py`** (FastAPI)
  - `GET /v1/flows/{flow_id}/versions/{version_id}/canvas?trace_id=<optional>` — single payload
    - Returns 404 if version mismatch
    - Returns 200 with trace=null if no trace_id
    - Cache-Control: private, max-age=2 (immutable versions; trace responses uncached)
  - `GET /v1/flows/{flow_id}/versions/{version_id}/runs?from=&to=&status=&limit=50` — trace picker
    - Filters by time range and status, returns run summaries

### Tests (pytest)

- **`test_canvas_render_payload.py`** — Endpoint contract:
  - Payload has all 5 keys (nodes, edges, ports, layout, trace)
  - 404 on version mismatch
  - Nodes include all required fields

- **`test_canvas_layout_topo.py`** — Layout determinism and positioning:
  - Topological level assignment (A→B→C: 0, 1, 2)
  - X by level (240px spacing)
  - Y by lane (120px spacing, stable sort by instance_label)
  - Operator positions override automatic
  - Determinism: two runs yield identical results

- **`test_canvas_trace_overlay.py`** — Trace assembly:
  - Happy path (all success, edges traversed)
  - Partial run (some running, no finished_at)
  - Failure short-circuits skipped downstream
  - No trace_id returns null (service level)

- **`test_canvas_port_resolution.py`** — Port index:
  - Bulk registry call count = 1
  - Missing keys return unresolved=true
  - Live schema changes reflect without DB write
  - Deduplication of input keys

**Total: 4 test files, ≥16 test cases**

### Frontend (TypeScript)

**File:** `frontend/src/types/api.ts`

Added/updated types:
- `CanvasPort` — {key, type}
- `CanvasResolvedPorts` — {inputs, outputs, unresolved}
- `CanvasNode` — {id, instance_label, node_key, kind, config_json, position}
- `CanvasEdge` — {id, from/to_node_id, from/to_port, kind}
- `CanvasLayoutEntry` — {x, y, lane}
- `TraceNodeStatus` — status literal union
- `CanvasTrace` — {node_status, edge_traversed, started_at, finished_at, total_duration_ms}
- `CanvasPayload` — {nodes, edges, ports, layout, trace}
- `FlowRunSummary` — {id, version_id, started_at, finished_at, status, total_duration_ms}

All string-literal unions; no `any`, no enums.

---

## Acceptance Criteria Met

### AC-1: Single-call payload contains all 5 keys ✅
```
nodes: [CanvasNode] — instance_label, node_key, kind, config_json, position
edges: [CanvasEdge] — from/to, from/to_port, kind
ports: map(node_key → {inputs, outputs, unresolved})
layout: map(node_id → {x, y, lane})
trace: CanvasTrace | null
```
Single transaction, single HTTP call.

### AC-2: Topological auto-layout is deterministic and honors operator positions ✅
- Level-based X (240px × level)
- Lane-based Y (120px × lane, stable sort by instance_label)
- Operator-set position_x/position_y overrides automatic
- Byte-identical across runs

### AC-3: Trace overlay maps run events to per-node + per-edge state ✅
- Per-node status (pending/running/success/failure/skipped/timed_out)
- Per-edge traversal (from succeeded AND to has event)
- Failure short-circuits skipped downstream
- started_at, finished_at, total_duration_ms computed

### AC-4: Port resolution is live from registry, never persisted ✅
- Bulk registry walk (one call, not per-node)
- Missing keys return unresolved=true
- Live code changes reflect without migration
- No dtl_* table touched

---

## Architecture Notes

**One-call design:** The canvas endpoint is read-only and combines three concerns:
1. **DAG retrieval** (from Plan 42-01 schema)
2. **Port resolution** (live from registry, no caching)
3. **Trace assembly** (from evt_catalog_flow_run_events views)

All three happen in a single READ ONLY transaction, so there's no coupling between read-time presentation and run-time execution.

**Pure compute modules** (port_index, layout, trace_assembler) are connection-free and stateless. They can be tested without database.

**Registry integration** is via the in-process `backend.01_catalog.registry` — the same surface external SDKs query. No duplication, no API call.

---

## Integration Points

**Depends on:**
- Plan 42-01 (Flow Schema) — tables `fct_catalog_flows`, `fct_catalog_flow_versions`, `dtl_catalog_flow_nodes`, `dtl_catalog_flow_edges`, `evt_catalog_flow_run_events`
- Plan 39-03 (NodeContext.pool) — for pool propagation

**Required by:**
- Plan 44-01 (Canvas Frontend) — consumes the `CanvasPayload` shape

---

## Notes for Reviewer

1. **No write paths.** Both routes are GET only. Canvas is read-side projection of immutable flow versions + run events.

2. **Traces are point-in-time.** `?trace_id=<run_id>` loads the current state of that run. No polling; Plan 44-01 will call this endpoint repeatedly as the run progresses.

3. **Port types reflect live code.** If an operator deploys a code change widening a port type, the next canvas request will show the new type. No schema migration needed.

4. **Layout determinism.** Critical for React Flow to avoid re-rendering when the user isn't changing anything. Same inputs → byte-identical output.

5. **Topological levels.** The layout engine uses longest-path (not just in-degree = 0) to ensure all predecessors are processed before the successor.

---

## Test Coverage

- 4 test files
- 16+ pytest cases
- All AC scenarios covered
- Pure compute modules fully testable without mocking

---

## Independently Mergeable

This plan is ready for PR. Plan 42-01 must be merged first (hard dependency on schema). Plan 44-01 can merge in parallel with code already in place.

---

## Quick Continuation

Next: `/paul:unify` to close the canvas milestone (42-01 + 43-01 + 44-01 together).

Or if Plan 42-01 hasn't been merged yet:
1. Merge Plan 42-01 (flow schema)
2. Merge Plan 43-01 (canvas backend — this plan)
3. Merge Plan 44-01 (canvas frontend, when ready)
