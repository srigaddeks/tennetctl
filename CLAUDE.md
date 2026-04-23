# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# TennetCTL — Claude Code Guide

## What This Is

TennetCTL is a self-hostable, workflow-native developer platform. It replaces the fragmented SaaS toolchain (PostHog, Unleash, GrowthBook, Windmill, n8n) with a single unified system built on a **node graph model**.

Every product capability — IAM, auditing, feature flags, monitoring, analytics — is modeled as nodes. Developers define features → sub-features → nodes in Python code. A visual canvas (React Flow) reads the live node registry and renders the workflow so developers can trace exactly what happens at every step.

**License:** AGPL-3

---

## Commands

```bash
# Backend (from repo root)
.venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0 --reload

# Frontend
cd frontend && npm run dev        # port 51735
cd frontend && npm run build
cd frontend && npm run lint

# Tests — real Postgres, no mocks
.venv/bin/pytest tests/ -v
.venv/bin/pytest tests/test_iam_users.py -v          # single file
.venv/bin/pytest tests/test_iam_users.py::test_name  # single test
.venv/bin/pytest --cov=backend --cov-report=term-missing

# Migrations
.venv/bin/python -m backend.01_migrator.runner apply
.venv/bin/python -m backend.01_migrator.runner status
.venv/bin/python -m backend.01_migrator.runner new --name create-iam-schema --feature 03_iam --sub 00_bootstrap
.venv/bin/python -m backend.01_migrator.runner seed
```

Test DB (session-scoped, drops+recreates `tennetctl_test` on each run):
- Host: `localhost:5434`, user: `tennetctl`, pass: `tennetctl_dev`
- Override via env: `TENNETCTL_TEST_PG_HOST/PORT/USER/PASS/DB`

Dev DB (for the running server): `postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl`

---

## Core Architecture

### The Hierarchy

```
Feature
  └── Sub-feature
        └── Nodes (Python code)
              └── Flows (DAG of nodes with typed edges)
```

- **Feature** — a product domain (IAM, monitoring, vault). Has a `feature.manifest.yaml`.
- **Sub-feature** — a scoped unit of work within a feature. Has its own API, UI, and nodes.
- **Node** — a Python class with a typed contract (key, kind, config schema, input schema, output schema, handler). Node *behavior* lives entirely in code. Only the stable key is stored in the DB.
- **Flow** — a DAG of node instances with typed edges (`next / success / failure / true / false`). Stored as a workflow definition referencing node keys.

### Node Contract (source of truth: ADR-018)

```python
class NodeContract:
    key: str           # stable, namespaced — "iam.auth_required"
    kind: Literal["request", "effect", "control"]
    config_schema: dict   # JSON Schema
    input_schema: dict
    output_schema: dict
    handler: str       # "backend.02_features.iam.nodes.AuthRequired"
```

- `request` nodes — gateway-compiled to APISIX (auth, rate limit, feature flags)
- `effect` nodes — run in backend runtime (DB writes, notifications, scoring)
- `control` nodes — flow logic only (branch, parallel, merge)

### Module Gating

```bash
TENNETCTL_MODULES=core,iam,audit,monitoring   # controls which modules start
TENNETCTL_SINGLE_TENANT=true                  # creates default org on first boot
```

`core + iam + audit` are always on. All others are optional. Same Docker image everywhere.

---

## Tech Stack

| Layer | Choice | Notes |
|-------|--------|-------|
| Backend | Python 3.13 + FastAPI | asyncpg, raw SQL — no ORM |
| Database | PostgreSQL | PG-specific features used: RLS, advisory locks, CTEs, LISTEN/NOTIFY |
| Frontend | Next.js + Tailwind CSS | App router |
| Canvas | React Flow (XY Flow) | Read-only viewer first; editor is future scope |
| Streaming | NATS JetStream | Only required when monitoring/product_ops/llm_ops enabled |
| Cache | Valkey | Optional — system works via Postgres fallbacks |
| Gateway | Apache APISIX | Executes request-path nodes compiled from registry |
| IDs | UUID v7 | `uuid-utils` Python library |
| MCP | 5 generic tools | `inspect / search / scaffold / validate / run` — never per-feature tools |

---

## Simplicity First

This is the most important section. Complexity is the primary failure mode.

### API surface — minimum viable

The 5-endpoint shape is a **maximum**, not a target. Most sub-features need 3–4. Ask before adding any endpoint:

> "Can an existing endpoint handle this with a query param or a different request body?"

If yes, don't add a new endpoint.

**Rules:**
- One collection path, one item path: `/v1/orgs` and `/v1/orgs/{id}` — never `/v1/org-list` or `/v1/get-org`
- PATCH handles ALL state changes. Never `POST /activate`, `POST /suspend`, `POST /archive`. Send `{"status": "active"}` to `PATCH /v1/orgs/{id}` instead
- Filter params instead of separate list endpoints: `GET /v1/users?status=active&org_id=x` — not `GET /v1/active-users`
- Bulk operations via the same path with a body array — not a separate `/bulk` endpoint
- Before adding a new route file, check if this sub-feature truly needs its own API surface

**Violation examples (don't do these):**
```
POST /v1/orgs/{id}/activate      ← wrong. PATCH /v1/orgs/{id}
GET  /v1/active-orgs             ← wrong. GET /v1/orgs?status=active
POST /v1/orgs/{id}/add-member    ← wrong. POST /v1/org-members
GET  /v1/orgs/{id}/get-settings  ← wrong. GET /v1/orgs/{id} (include settings in response)
```

### Nodes — only when genuinely reusable

A node is a **platform-level building block**, not a wrapper for feature logic. Ask before creating a node:

> "Will at least 3 different sub-features or flows use this exact behavior?"

If not, it stays as a plain Python function inside the feature's `service.py`.

**Rules:**
- Feature-internal logic stays in `service.py` — not every function is a node
- Nodes for platform concerns only: auth, rate limiting, feature flags, audit emission, log/trace/metric hooks, notifications
- One node for each concern — not one per feature variant. `auth_required` is one node, not `iam_auth_required` + `vault_auth_required`
- Prefer **presets** (pre-wired flow templates) over creating new nodes. If you need `public_api` behavior, use the `public_api` preset — don't wire `auth_required → rate_limit → run_handler → emit_audit` from scratch every time
- Config schema is how a node varies per use case — not separate nodes with slightly different behavior

**Violation examples (don't do these):**
```
iam.check_user_active            ← wrong. Business logic, stays in service.py
monitoring.record_api_call       ← wrong. Use the generic emit_metric node
vault.require_vault_access       ← wrong. auth_required node + config handles this
notify.send_signup_email         ← wrong. send_notification node with template config
```

### Sub-features — one concern, shippable alone

A sub-feature must be independently shippable. If it can't be merged and used without another sub-feature, split differently. Each sub-feature should cover exactly one concern — not "users and groups" but either "users" or "groups".

---

## Critical Rules

### Immutability
ALWAYS return new objects. NEVER mutate Python dicts, TypeScript objects, or DB records.

### API Response Envelope
```json
{ "ok": true, "data": {...} }
{ "ok": false, "error": { "code": "NOT_FOUND", "message": "..." } }
```

### Python: importlib for numeric dirs
```python
from importlib import import_module
_db   = import_module("backend.01_core.database")
_resp = import_module("backend.01_core.response")
```
Never use relative imports with numeric-prefix directories.

### Python: conn not pool
Pass `conn` (connection) to service and repo functions. `pool.acquire()` belongs in routes only — never in service or repo.

### Python: UUID v7 always
```python
_core_id = import_module("backend.01_core.id")
new_uuid = _core_id.uuid7()   # NOT uuid4(), NOT new_id()
```

### Python: start command
```bash
cd tennetctl && .venv/bin/python -m uvicorn backend.main:app --port 51734 --host 0.0.0.0 --reload
```

Frontend dev server:
```bash
cd tennetctl/frontend && npm run dev   # starts on port 51735
```

### TypeScript: one types file
All shared TS types in `frontend/src/types/api.ts`. No scattered type files.

### TypeScript: no any
Use `unknown` and narrow. String literal unions over `enum`.

### TypeScript: API calls check ok
```typescript
const data = await res.json()
if (!data.ok) throw new Error(data.error?.message)
```

---

## Database Conventions

### Table Type System

| Prefix | # Range | Purpose | Notes |
|--------|---------|---------|-------|
| `dim_*` | 01–09 | Lookup enums — seeded, never mutated | SMALLINT PK |
| `fct_*` | 10–19 | Entity identity — UUID v7 + FK IDs only | No strings, no JSONB |
| `dtl_*` | 20–29 | EAV attributes or fixed detail schema | |
| `lnk_*` | 40–59 | Many-to-many, immutable rows | No updated_at |
| `evt_*` | 60–79 | Append-only events | No updated_at, no deleted_at |

**Critical:**
- NEVER add business columns to `fct_*` — use EAV `dtl_*` layer
- NEVER use Postgres ENUMs — use `dim_*` tables
- NEVER put JSONB or strings in `fct_*`
- `updated_at` set by app in every UPDATE (`updated_at = CURRENT_TIMESTAMP`) — no triggers
- Soft-delete only: `deleted_at TIMESTAMP`, not `is_deleted BOOLEAN`
- Reads → `v_{entity}` view. Writes → raw `fct_*` / `dtl_*` tables

### Naming

| Artifact | Pattern | Example |
|----------|---------|---------|
| DB schema | `"{nn}_{name}"` | `"03_iam"` |
| DB table | `{nn}_{type}_{name}` | `10_fct_users` |
| Migration | `YYYYMMDD_{NNN}_{desc}.sql` | `20260405_007_create-auth-tables.sql` |
| API path | `/v1/{kebab-plural}` | `/v1/feature-flags` |

### EAV Pattern
- `dtl_*` stores attributes as rows: `(entity_type_id, entity_id, attr_def_id, key_text|key_jsonb|key_smallint)`
- Register every attribute in `dim_attr_defs` before use
- asyncpg handles Python dicts as JSONB — never call `json.dumps()`

---

## Feature Numbers (permanent — never renumber)

| # | Feature | Schema | Backend | Frontend |
|---|---------|--------|---------|----------|
| 00 | Setup | `00_schema_migrations` | `scripts/setup/` | — |
| 01 | SQL Migrator | `00_schema_migrations` | `scripts/migrator/` | — |
| 02 | Vault | `02_vault` | `02_features/vault/` | `/vault` |
| 03 | IAM | `03_iam` | `02_features/iam/` | `/iam` |
| 04 | Audit | `04_audit` | `02_features/audit/` | `/audit` |
| 05 | Monitoring | `05_monitoring` | `02_features/monitoring/` | `/monitoring` |
| 06 | Notify | `06_notify` | `02_features/notify/` | `/notify` |
| 07 | Billing | `07_billing` | `02_features/billing/` | `/billing` |
| 08 | LLM Ops | `08_llmops` | `02_features/llm/` | `/llm` |

---

## Directory Layout

```
tennetctl/
├── 02_contributing_guidelines/   # How to build features/nodes
├── 03_docs/
│   ├── 00_main/                  # Vision, rules, ADRs
│   │   └── 08_decisions/         # Architecture Decision Records (ADR-001 to ADR-026)
│   ├── features/{nn}_{feature}/  # Feature manifests + sub-feature docs
│   └── nodes/                    # Shared node docs
├── backend/
│   ├── 01_core/                  # config, db, id, errors, response, middleware
│   └── 02_features/{feature}/{sub_feature}/
│       ├── schemas.py            # Pydantic v2
│       ├── repository.py         # asyncpg raw SQL, reads views
│       ├── service.py            # Business logic + audit
│       └── routes.py             # FastAPI APIRouter
├── frontend/src/
│   ├── app/{feature}/            # Next.js app router pages
│   ├── features/{feature}/       # components + hooks
│   │   └── hooks/use-{name}.ts  # TanStack Query hooks
│   └── types/api.ts              # ALL shared TS types
├── mcp/                          # MCP server (optional, 5 generic tools)
└── .paul/                        # PAUL project management
    ├── PROJECT.md                # Full project context
    ├── STATE.md                  # Current loop position
    └── ROADMAP.md                # Milestone + phase tracker
```

Backend sub-feature = exactly 5 files: `__init__.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`.

### Catalog Boot Sequence

On every startup, `backend.01_catalog` scans all `feature.manifest.yaml` files, validates node contracts, and upserts features/sub-features/nodes into the `01_catalog` DB schema. This is the live node registry — it runs before any module routers mount. Adding a new node requires a manifest entry; the catalog runner resolves `handler` strings to Python classes at boot and caches them. Hot-reload is active in DEBUG mode (`DEBUG=true` env var) and watches manifests for changes without restart.

Module routers are gated by `TENNETCTL_MODULES` — only listed modules mount their `routes.py`. `core + iam + audit` are always-on. The setup route (`/v1/setup/initial-admin`) is always mounted and bypasses auth via `SetupModeMiddleware`.

### Next.js Version Warning

Read `node_modules/next/dist/docs/` before writing any frontend code — this version has breaking changes from training data. Heed deprecation notices.

---

## Development Workflow

### TDD (mandatory)
1. Write failing test (RED)
2. Write minimal implementation (GREEN)
3. Refactor (IMPROVE)
4. 80%+ coverage

### Feature Workflow
0. Research — Context7 docs, `gh search`, npm/PyPI before writing anything
1. Plan — use planner agent, confirm before coding
2. TDD — tests first
3. Review — code-reviewer agent, fix CRITICAL and HIGH
4. Commit + PR

### Commit Format
```
feat|fix|refactor|docs|test|chore|perf|ci: description
```
Use `git add .` — stage all. Never file-by-file.

### API Design
- 5-endpoint shape is the maximum — `GET list`, `POST create`, `GET one`, `PATCH update`, `DELETE soft-delete`. Most sub-features need 3–4.
- PATCH handles ALL state changes — never action endpoints (`POST /activate`, `POST /suspend`)
- DELETE = soft-delete only (`deleted_at = NOW()`, returns 204)
- Filter params instead of separate list endpoints (`GET /orgs?status=active`)
- See **Simplicity First** section for full rules and violation examples

---

## Testing

- **Backend:** pytest (`tests/` dir, `test_*.py` files)
- **UI / E2E:** Playwright MCP — headed live browser, walk through the user flow before closing any plan. NEVER Robot Framework, NEVER `@playwright/test` or `.spec.ts`. No `.robot` files.

---

## Agents (use proactively)

| Trigger | Agent |
|---------|-------|
| Complex feature or refactor | planner |
| Architectural decision | architect |
| Code just written/modified | python-reviewer or typescript-reviewer |
| Security-sensitive code | security-reviewer |
| Build fails | build-error-resolver |
| Critical user flows | e2e-runner |

Launch independent agents in parallel.

---

## Key ADRs

| ADR | Decision |
|-----|----------|
| [016](03_docs/00_main/08_decisions/016_node_first_architecture.md) | Node-first: features → sub-features → nodes → flows |
| [017](03_docs/00_main/08_decisions/017_flow_execution_model.md) | Flow execution: DAG, edge types, retries, request vs effect paths |
| [018](03_docs/00_main/08_decisions/018_node_contract_model.md) | Node contract: key, kind, schemas, handler ref |
| [019](03_docs/00_main/08_decisions/019_feature_node_ownership.md) | Feature-local vs shared node ownership |
| [020](03_docs/00_main/08_decisions/020_workflow_versioning_and_publish.md) | Draft → publish → immutable versioning |
| [021](03_docs/00_main/08_decisions/021_gateway_compilation_boundary.md) | What compiles to APISIX vs stays in backend runtime |
| [022](03_docs/00_main/08_decisions/022_api_enhancement_model.md) | APIs stay code-first; tennetctl enhances via middleware + workflows |
| [023](03_docs/00_main/08_decisions/023_canvas_library.md) | React Flow (XY Flow) for visual canvas |
| [024](03_docs/00_main/08_decisions/024_mcp_integration_model.md) | 5 generic MCP tools — never per-feature tools |
| [025](03_docs/00_main/08_decisions/025_multi_tenant_model.md) | Multi-tenant default; TENNETCTL_SINGLE_TENANT for single-tenant |
| [026](03_docs/00_main/08_decisions/026_minimum_surface_principle.md) | Minimum surface: fewer APIs and nodes, maximum configurability |

Full ADR list: [03_docs/00_main/README.md](03_docs/00_main/README.md)

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

## gstack
Use /browse from gstack for all web browsing. Never use mcp__claude-in-chrome__* tools.
Available skills: /office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review,
/design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy,
/canary, /benchmark, /browse, /open-gstack-browser, /qa, /qa-only, /design-review,
/setup-browser-cookies, /setup-deploy, /retro, /investigate, /document-release, /codex,
/cso, /autoplan, /pair-agent, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn.