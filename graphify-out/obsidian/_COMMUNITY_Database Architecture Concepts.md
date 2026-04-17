---
type: community
cohesion: 0.04
members: 60
---

# Database Architecture Concepts

**Cohesion:** 0.04 - loosely connected
**Members:** 60 nodes

## Members
- [[01_coreid.py — centralised UUID v7 generation (new_id())]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[ADR-001 Postgres as the Primary and Only Required Database]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[ADR-004 UUID v7 as Primary Keys]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[ADR-007 Valkey as Optional Caching and Rate-Limiting Backend]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[ADR-008 Monitoring Scope and Feature Boundary]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[ADR-016 Node-First Architecture]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Apache APISIX — first gateway target for HTTP and API policy execution]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Cache invalidation on iam.role.assigned, iam.permission.updated, iam.group.membership.changed]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[CacheBackend Protocol — abstract cache interface with getsetdeleteset_if_not_exists]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[ClickHouse — optional backend for high-cardinality metrics (never required)]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[Control Node — branch, fan-out, merge, or control graph structure]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Core Rule Sub-features communicate only via run_node(key, ctx, inputs), never direct imports]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[Effect Node — runs as side effect afteraround a decision]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Feature — bounded domain owning behavior, contracts, dashboards]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Flow — visual composition of nodes validated and executedcompiled by backend]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Idempotency keys — Valkey SET NX EX or Postgres table + cleanup job]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[LLM Ops (Phase 8) — LLM call traces, prompt versioning, evals, cost attribution for ML teams]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[Monitoring (Phase 5) — OTEL traceslogsmetrics, dashboards, alerting, status page for engineers]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[NATS JetStream — streaming buffer decoupling ingest rate from write rate]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[NCP v1 — Node Catalog Protocol (tennetctlv1)]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §1 Entity Identity — key grammar for ModuleFeatureSub-featureNodeFlow]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §10 Cross-Import Rule — validator blocks sub-feature→sub-feature imports; enforced at pre-commit]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §11 Boot Sequence — parse modules, discover manifests, validate, filter, resolve handlers, upsert catalog]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §12 Lifecycle — undeclared → active → deprecated (180d) → tombstoned → key_reusable (365d)]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §13 Versioning — integer version, separate keys for parallel versions, deprecated_at + replaced_by]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §14 Error Codes — CAT_MANIFEST_INVALID, CAT_NODE_NOT_FOUND, CAT_NODE_TOMBSTONED, CAT_AUTH_DENIED, etc.]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §15 Out of Scope — declarative flow execution, React Flow canvas, APISIX gateway sync, MCP server]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §2 Folder Structure — feature.manifest.yaml + 5-file sub-feature shape + nodes]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §3 Feature Manifest Grammar — apiVersion tennetctlv1, kind Feature, spec with nodesroutesui_pages]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §4 Node Contract (Python) — Node class with InputOutput BaseModel + async run(ctx, inputs)]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §5 Catalog DB Schema — schema 01_catalog with dim_modules, fct_features, fct_nodes, dtl_attrs]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §6 NodeContext — frozen dataclass carrying user_id, session_id, org_id, trace_id, span_id, conn]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §7 Node Runner — run_node(key, ctx, inputs) catalog lookup, authz, resolve handler, execute]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §8 Execution Policy — timeout_ms, retries (TransientError only), tx modes (callerownnone)]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[NCP §9 Authorization Hook — authz.check_call(ctx, node_meta), pluggable via register_checker()]] - document - 03_docs/00_main/protocols/001_node_catalog_protocol_v1.md
- [[Node — registered backend building block with typed config, inputs, outputs, metadata]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[OpenTelemetry (OTLPHTTP JSON) — only ingest protocol for Phase 5 Monitoring]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[Permission caching — Valkey TTL cache (default 60s) for recursive CTE permission queries]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[PostgreSQL 16 — only required external database for tennetctl]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[Postgres-specific features used RLS, advisory locks, CTEs, LISTENNOTIFY]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[Product Ops (Phase 7) — Segment-compatible events, analytics, funnels, feature flags for PMs]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[RateLimiter Protocol — abstract rate limiter with check_and_increment]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[Rationale BIGSERIAL rejected — sequential integers in URLs leak entity counts]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[Rationale No durable state in Valkey — loss must be safe, system recovers in one request]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[Rationale Redis 2024 SSPL license incompatible with open-source projects; Valkey is BSD 3-Clause]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[Rationale Redis rejected — Postgres advisory locks + LISTENNOTIFY outbox covers use cases]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[Rationale SQLite rejected — lacks RLS, LISTENNOTIFY, uuid_generate_v7, advisory locks]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[Rationale ULID rejected — UUID is native Postgres type; ULID requires text storage]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[Rationale UUID in URLs is safe — no sequential enumeration, no business intelligence leak]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[Rationale ad hoc concerns in handlers makes system hard to reason about]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Rationale different data models, delivery timelines, and open-source positioning prevent merging]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[Rationale single docker compose up with one Postgres instance for local dev]] - document - 03_docs/00_main/08_decisions/001_postgres_primary.md
- [[Rationale time-ordered keys prevent B-tree index fragmentation vs UUID v4]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[Rationale visual layer without backend authority causes UI drift from reality]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Request Node — runs in live request path, influences response]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[Shared layer NATS JetStream ingest transport (01_corenats_client.py)]] - document - 03_docs/00_main/08_decisions/008_monitoring_scope.md
- [[Sub-feature — smallest independently shippable capability inside a feature]] - document - 03_docs/00_main/08_decisions/016_node_first_architecture.md
- [[UUID v7 — time-ordered 128-bit identifier, monotonically increasing (RFC 9562, 2024)]] - document - 03_docs/00_main/08_decisions/004_uuid7.md
- [[Valkey — BSD 3-Clause community fork of Redis 7.2 (Linux Foundation)]] - document - 03_docs/00_main/08_decisions/007_valkey_optional_cache.md
- [[uuid-utils Python library — generates UUID v7 via uuid_utils.uuid7()]] - document - 03_docs/00_main/08_decisions/004_uuid7.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Database_Architecture_Concepts
SORT file.name ASC
```
