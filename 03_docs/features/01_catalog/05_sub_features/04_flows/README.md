# Flows Sub-feature — DAG Definitions and Versioning

Persist flow definitions (DAGs of node instances with typed edges) and manage their lifecycle: draft → publish → immutable-version.

## Overview

A **flow** is a DAG (directed acyclic graph) of node instances connected by typed edges. Flows are stored as mutable drafts that can be published into immutable versions, enabling versioning and audit trails.

## Architecture

### Schema (migrations 079–080)
- `dim_catalog_flow_status` — draft | published | archived
- `dim_catalog_flow_edge_kind` — next | success | failure | true_branch | false_branch
- `dim_catalog_port_type` — type system for edges (any, string, number, boolean, object, array, uuid, datetime, binary, error)
- `fct_catalog_flows` — flow identity (UUID, slug, org/workspace scoped)
- `fct_catalog_flow_versions` — immutable snapshots with draft→published lifecycle
- `dtl_catalog_flow_nodes` — node instances per version
- `dtl_catalog_flow_edges` — typed edges per version

### Pure Compute Modules
- **dag.py** — `validate_dag()` (Kahn topo-sort, branch-pair checks), `topological_order()` (for layout)
- **port_resolver.py** — `resolve_ports()` (translate JSON Schema to ports), `is_compatible()` (type safety)
- **version_publish.py** — `compute_dag_hash()` (SHA256), `freeze_draft()` (atomic publish + clone)

### Database Operations
- **repository.py** — Raw asyncpg, reads views, writes fct/dtl tables
- **service.py** — Business logic, orchestrates validation, emits audit
- **routes.py** — 7 HTTP endpoints (CRUD + version ops)

## API

### Flows (5 + 2 endpoints)
```
GET    /v1/flows                    → list flows (filters: status, q, workspace_id)
POST   /v1/flows                    → create flow + initial draft v1
GET    /v1/flows/{id}               → get flow + current version summary
PATCH  /v1/flows/{id}               → rename | archive | publish version
DELETE /v1/flows/{id}               → soft-delete

GET    /v1/flows/{id}/versions/{version_id}       → full DAG (nodes + edges + ports)
PATCH  /v1/flows/{id}/versions/{version_id}       → mutate draft DAG
```

## Lifecycle

1. **Create** — `POST /flows` creates flow + version v1 in draft status
2. **Edit** — `PATCH /flows/{id}/versions/{v1}` mutates draft DAG (validate, persist)
3. **Publish** — `PATCH /flows/{id}` with `{publish_version_id}` freezes v1, creates new draft v2
4. **Archive** — `PATCH /flows/{id}` with `{status:"archived"}` hides flow from lists

## Validation

All DAG operations validate:
- **Acyclicity** (Kahn topological sort)
- **Port compatibility** (from_port_type → to_port_type, type any matches all)
- **Branch pairs** (true_branch always has sibling false_branch)
- **Reachability** (all nodes reachable from entry — future scope)

## Immutability

- Draft versions are mutable; published versions are frozen
- `freeze_draft()` is atomic: publish v1, compute dag_hash, clone all dtl rows → v2, update flow.current_version_id
- Partial unique index enforces at most one draft per flow

## Testing

- **test_flow_crud.py** — CRUD, slug uniqueness, soft-delete, list filters (6 tests)
- **test_flow_dag_validation.py** — cycles, self-loops, branch pairs, invalid edges (8 tests)
- **test_flow_port_typing.py** — type compatibility, schema parsing, format inference (7+ tests)
- **test_flow_version_publish.py** — hash stability, freeze_draft atomicity, version_number monotonic (6+ tests)

Total: ≥20 pytest, 80%+ coverage.

## Future Scope

- Flow editor UI (read-only canvas in Plan 44-01, write via API/MCP)
- Flow execution engine (Plan 43-01)
- Subflows / nested flows
- Flow templates library
- Conditional expressions on edges
- Port value transformations / mapping DSL
- Multi-tenant flow sharing
- Flow diff endpoint

## Conventions

- Node registry is code-first (ADR-018); node_key references live registry, no FK to fct_nodes
- Flows are workspace-scoped; no cross-tenant sharing in v1
- All audit events carry user_id + session_id + org_id + workspace_id (Memory: audit scope mandatory)
- PATCH is the only state-change verb (per CLAUDE.md simplicity rules)
