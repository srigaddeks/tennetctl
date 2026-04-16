# TennetCTL

## What This Is

TennetCTL is a self-hostable, workflow-native developer platform that replaces the fragmented SaaS toolchain (PostHog, Unleash, GrowthBook, Windmill, and others) with a single unified system. Every product capability — auth, IAM, auditing, feature flags, monitoring, analytics — is modeled as a node graph. Developers define features as collections of sub-features, each with APIs, UI, and nodes in code. A visual canvas reads the live node registry and renders the flow so developers can trace exactly what happens at every step of every workflow (e.g. signup → assign group → create org → assign roles). Built to ship web and mobile SaaS products at scale.

## Core Value

Any team can self-host one platform that replaces PostHog, Unleash, GrowthBook, Windmill, and their entire SaaS toolchain — building and running products as visual node workflows with enterprise capabilities built in.

## Current State

| Attribute | Value |
|-----------|-------|
| Type | Application |
| Version | 0.1.0 |
| Status | Phases 1 + 2 complete — Phase 3 (IAM & Audit) starting |
| Last Updated | 2026-04-16 |

## Requirements

### Core Features

- **Node graph definition** — Developers define nodes in Python code; each node has a typed contract (key, config schema, input schema, output schema, kind); only stable keys are stored in DB
- **Visual flow viewer** — React Flow (XY Flow) canvas renders the live workflow from the node registry (read-only first, editor later); developers can trace any workflow path step-by-step
- **Enterprise capability nodes** — IAM, auditing, monitoring, feature flags, analytics shipped as first-class built-in nodes (not external tools)
- **Claude Code integration** — AI-assisted flow composition; Claude can read, navigate, and scaffold node graphs
- **Self-host with env-flag module gating** — TENNETCTL_MODULES env var enables/disables modules; single container for small teams, split for enterprise; core+iam+audit always on

### Validated (Shipped)
- ✓ Docker Compose local dev environment (Postgres 5434, Valkey) — Phase 1 Plan 01
- ✓ Custom SQL migrator (UP/DOWN, rollback, history table, ordered by filename) — Phase 1 Plan 01
- ✓ FastAPI backend scaffold with asyncpg pool, importlib conventions, UUID v7, response envelope, error handling, CORS — Phase 1 Plan 02
- ✓ Node registry skeleton — Phase 1 Plan 02
- ✓ Next.js frontend shell with Tailwind CSS, app router, shared TS types (api.ts), typed API client (apiFetch) — Phase 1 Plan 03
- ✓ Robot Framework + Playwright Browser E2E harness with first passing test suite — Phase 1 Plan 03
- ✓ **Node Catalog Protocol v1** — authoritative spec at `03_docs/00_main/protocols/001_node_catalog_protocol_v1.md` — Phase 2 Plan 01
- ✓ **ADR-027** Node Catalog + Runner — rationale + alternatives + escape hatches — Phase 2 Plan 01
- ✓ **`"01_catalog"` Postgres schema** (9 tables + 19 seeded dim rows; CHECK constraint enforces effect-must-emit-audit at DB layer) — Phase 2 Plan 01
- ✓ **`backend/01_catalog/` Python module** — manifest parser (Pydantic = schema), boot loader wired into FastAPI lifespan, cross-import linter (catches `from X` + `import_module("X")`) — Phase 2 Plan 02
- ✓ **`/tnt` Claude Code skill** — 44-line onboarding for the node catalog pattern — Phase 2 Plan 02
- ✓ **Node runner** — `run_node(pool, key, ctx, inputs)` dispatch with execution policy (timeout, retry on TransientError, tx modes caller/own/none), pluggable authz hook, NodeContext propagation (audit scope + distributed tracing) — Phase 2 Plan 03

### Active (In Progress)
None — ready for Phase 3.

### Planned (Next)
- Phase 3: IAM & Audit schema (dim/fct/dtl/lnk tables, EAV foundation, IAM feature.manifest.yaml — first real consumer of NCP v1, audit service, `emit_audit` node)
- Phase 4: Orgs & Workspaces vertical (repo → service → routes → nodes → UI → Playwright; all cross-sub-feature calls via `run_node`)
- Phase 5: Users & Account Types vertical
- Phase 6: Roles, Groups, Scopes & Applications vertical
- Phase 7: Auth Config & Feature Flags vertical

### Out of Scope
- Visual drag-and-drop editor (read-only viewer first; editor is future milestone)
- Mobile app output (future milestone — web first)
- Non-SQL databases (raw SQL + asyncpg for now; abstraction layer is future)

## Target Users

**Primary:** Developers building SaaS products
- Building internal tooling or external products on top of TennetCTL
- Comfortable with code; want visual clarity, not visual editing (initially)
- Need enterprise capabilities without assembling 30 separate tools

**Secondary:** Technical super admins / operators
- Managing deployments, enabling/disabling feature modules via env vars
- Monitoring running workflows across a self-hosted instance

## Context

**Business Context:**
Competing with PostHog, Unleash, GrowthBook, Windmill, and composable developer platform stacks. Target market: engineering teams building SaaS products who want a unified, self-hostable platform. AGPL-3 licensed. Commercial model: sell to external teams (web + mobile outputs planned).

**Technical Context:**
Codebase rebuilt from scratch. Previous tennetctl iteration deleted. Clean slate. Node behavior lives entirely in Python code — the DB stores only stable node keys and workflow graph definitions that reference those keys.

## Constraints

### Technical Constraints
- Python 3.13 backend (FastAPI + asyncpg — raw SQL, no ORM; PG-specific features used: RLS, advisory locks, CTEs)
- PostgreSQL primary — raw SQL via asyncpg; SQL portability deferred to future milestone
- Next.js + Tailwind CSS (latest) frontend
- React Flow (XY Flow) for visual canvas
- Docker-first — TENNETCTL_MODULES env var controls module activation at startup; runtime toggling requires restart
- NATS JetStream for high-volume ingest (monitoring, traces, logs); Postgres outbox for internal cross-module events
- Valkey optional cache (rate limiting, permission cache); system works without it via Postgres fallbacks

### Business Constraints
- Start with web output; mobile is a future milestone
- Prioritize developer experience over operator UX (Phase 1)
- Must be genuinely self-hostable — no forced cloud dependency
- AGPL-3 — prevents SaaS wrapping without contribution

### Compliance Constraints
- Auditing module must be separable (resource-intensive; enterprise can isolate it)
- AGPL-3 requires source disclosure for network-deployed forks

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Raw SQL (asyncpg), no ORM | PG-specific features needed (RLS, advisory locks, CTEs); non-standard naming convention; SQL portability deferred | 2026-04-12 | Active |
| Nodes in code, keys in DB | Node behavior is code; DB stores only stable key references + workflow graphs pointing to those keys; no behavior drift | 2026-04-12 | Active |
| TENNETCTL_MODULES env-flag gating | Same Docker image everywhere; env controls which modules start; core+iam+audit always on; restart required to change | 2026-04-12 | Active |
| Multi-tenant default; TENNETCTL_SINGLE_TENANT=true for single-tenant | Creates default org at boot; single-tenant deployments skip tenant selection UX | 2026-04-12 | Active |
| React Flow (XY Flow) for canvas | Industry standard for React node UIs; read-only mode trivial; MIT licensed; actively maintained by XY Flow org | 2026-04-12 | Active |
| AGPL-3 license | Open-core commercial model; prevents SaaS wrapping without contribution | 2026-04-12 | Active |
| Read-only visual viewer first | Code is source of truth; visual editor is future scope; avoids premature complexity | 2026-04-12 | Active |
| NATS JetStream for ingest; Postgres outbox for internal events | High-volume monitoring/trace/log ingest via NATS; transactional cross-module events via outbox | 2026-04-12 | Active |
| Valkey optional (not required) | Rate limiting + permission cache; Postgres fallbacks work without it | 2026-04-12 | Active |
| Apache APISIX as gateway execution plane | Compiles request-path nodes (auth, rate limit, feature flags) to gateway; business logic stays in backend | 2026-04-12 | Active |
| Minimum surface principle (ADR-026) | Fewer APIs and nodes; one node per concern with config for variants; presets for common combinations | 2026-04-13 | Active |
| 5 generic MCP tools (ADR-024) | inspect/search/scaffold/validate/run — never per-feature tools; constant tool count regardless of feature growth | 2026-04-13 | Active |
| Frontend port 51735 (non-standard) | Project convention: avoid default ports to prevent conflicts; all E2E tests and CORS config use 51735 | 2026-04-13 | Active |
| Custom SQL migrator over Alembic/ORM | asyncpg-only; UP/DOWN migrations; ordered by filename; rollback and history tracking | 2026-04-13 | Active |
| Frozen dataclass Config (not BaseSettings) | Simpler, no extra dependency, immutable at startup | 2026-04-13 | Active |
| Node Catalog Protocol v1 (NCP v1) — sub-features communicate only via `run_node` | Direct imports across sub-features make module gating impossible, produce spaghetti coupling, and lose audit scope propagation. NCP mandates catalog-dispatched calls with typed NodeContext | 2026-04-16 | Active |
| Catalog `fct_*` PKs use SMALLINT GENERATED IDENTITY (deviation from UUID v7 rule) | System-level entities seeded via manifest upsert, referenced by many rows; SMALLINT keeps index pages small and makes manifest upsert-by-key simpler | 2026-04-16 | Active |
| Effect-must-emit-audit enforced at DB + Pydantic + runner layer | Triple defense means no effect node can ever register with emits_audit=false regardless of which layer is bypassed | 2026-04-16 | Active |
| Idempotency check runs BEFORE Pydantic input validation in runner | If a node declares idempotency_key as required Input, Pydantic would mask the runner-level policy error; runner policy concerns should surface first | 2026-04-16 | Active |
| Pydantic models are the manifest schema (no separate JSON Schema file) | Single source of truth; Pydantic v2 `model_json_schema()` generates the schema when external tools need it | 2026-04-16 | Active |
| Cross-import linter parses both `from X` and `import_module("X")` | Numeric-prefix dirs require importlib; without Call-node detection the linter is a no-op on this project | 2026-04-16 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Single Docker container boots | All core modules run from 1 container | - | Not started |
| Workflow visualization | Any registered workflow renders as node graph in UI | - | Not started |
| Node contract test coverage | 80%+ on node execution layer | - | Not started |
| Module isolation | Any optional module disabled via env var without crashing others | - | Not started |
| Single-tenant mode | TENNETCTL_SINGLE_TENANT=true boots with default org, no tenant selection | - | Not started |

## Tech Stack / Tools

| Layer | Technology | Notes |
|-------|------------|-------|
| Backend | Python 3.13 + FastAPI | Async, typed |
| Database driver | asyncpg | Raw SQL; no ORM |
| Database | PostgreSQL | RLS, advisory locks, CTEs in use |
| Message bus | NATS JetStream | High-volume ingest; optional for non-monitoring modules |
| Cache | Valkey (optional) | Rate limiting + permission cache; Postgres fallback |
| Frontend | Next.js + Tailwind CSS (latest) | App shell, admin UI |
| Canvas | React Flow / XY Flow | Node graph visualization |
| Gateway | Apache APISIX | Compiles request-path nodes to gateway policy |
| License | AGPL-3 | — |
| Competitors / References | PostHog, Unleash, GrowthBook, Windmill, n8n, Activepieces | Study for feature parity |

## Links

| Resource | URL |
|----------|-----|
| Repository | /Users/sri/Documents/tennetctl |
| ADRs | 03_docs/00_main/08_decisions/ |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-16 after Phase 2 (Catalog Foundation) complete*
