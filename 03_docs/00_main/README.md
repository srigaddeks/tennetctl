# tennetctl — Core Documentation

This directory contains the project-level documents that define what tennetctl is and how it is supposed to grow.

## Documents

| File | What it answers |
|------|----------------|
| [01_vision.md](01_vision.md) | What tennetctl is, how features/nodes/flows fit together, and what the product is not trying to become. |
| [02_ethos.md](02_ethos.md) | The principles behind design and implementation decisions. |
| [03_rules.md](03_rules.md) | Hard architectural and documentation rules. |
| [04_roadmap.md](04_roadmap.md) | Which features matter now and how planning is split between top-level roadmap and per-feature backlog. |
| [05_contributing.md](05_contributing.md) | High-level contribution expectations. |
| [06_setup.md](06_setup.md) | Local development setup. |
| [07_adding_a_feature.md](07_adding_a_feature.md) | Redirect to the contributor guides in `02_contributing_guidelines/`. |
| [08_decisions/](08_decisions/) | Cross-cutting architecture decisions. |

## Adjacent Documentation Areas

| Area | Purpose |
|------|---------|
| [Features](../features/README.md) | Canonical structure for feature and sub-feature docs. |
| [Nodes](../nodes/README.md) | Canonical structure for shared node docs. |
| [Contributor Guides](../../02_contributing_guidelines/00_README.md) | Practical workflow for building features and sub-features. |

## Architecture Decision Records

| ADR | Decision |
|-----|----------|
| [001](08_decisions/001_postgres_primary.md) | Postgres is the only required database |
| [002](08_decisions/002_nats_for_streams.md) | NATS JetStream for high-volume streaming workloads |
| [003](08_decisions/003_raw_sql_no_orm.md) | Raw SQL with asyncpg |
| [004](08_decisions/004_uuid7.md) | UUID v7 as primary keys |
| [005](08_decisions/005_clickhouse_later.md) | ClickHouse is optional and deferred |
| [006](08_decisions/006_database_conventions.md) | Database naming and structure conventions |
| [007](08_decisions/007_valkey_optional_cache.md) | Valkey remains optional |
| [008](08_decisions/008_monitoring_scope.md) | Monitoring-related scope boundaries |
| [009b](08_decisions/009b_license_agpl3.md) | AGPL-3 licensing decision |
| [010](08_decisions/010_alerting_notify_separation.md) | Alerting writes records; notify delivers |
| [011](08_decisions/011_monitoring_ui_architecture.md) | Monitoring UI structure |
| [015](08_decisions/015_feature_gating.md) | Selective module activation |
| [016](08_decisions/016_node_first_architecture.md) | Node-first architecture: features, nodes, flows, and gateway compilation |
| [017](08_decisions/017_flow_execution_model.md) | Flow execution semantics: edges, branching, retries, and request vs effect paths |
| [018](08_decisions/018_node_contract_model.md) | Canonical public node contract model |
| [019](08_decisions/019_feature_node_ownership.md) | Feature-local vs shared-node ownership rules |
| [020](08_decisions/020_workflow_versioning_and_publish.md) | Draft, publish, and immutable workflow versioning |
| [021](08_decisions/021_gateway_compilation_boundary.md) | What compiles to APISIX and what stays in backend runtime |
| [022](08_decisions/022_api_enhancement_model.md) | APIs stay code-first; tennetctl enhances them with middleware and workflows |
| [023](08_decisions/023_canvas_library.md) | React Flow (XY Flow) as the visual canvas library |
| [024](08_decisions/024_mcp_integration_model.md) | 5 generic MCP graph tools — not per-feature tools |
| [025](08_decisions/025_multi_tenant_model.md) | Multi-tenant by default; TENNETCTL_SINGLE_TENANT for single-tenant mode |
| [026](08_decisions/026_minimum_surface_principle.md) | Minimum surface: fewer APIs and nodes, maximum configurability |

## Reading Order

If you are starting fresh:

1. [01_vision.md](01_vision.md)
2. [02_ethos.md](02_ethos.md)
3. [03_rules.md](03_rules.md)
4. [04_roadmap.md](04_roadmap.md)
5. [../../02_contributing_guidelines/00_README.md](../../02_contributing_guidelines/00_README.md)

If you need a design decision, read the relevant ADR in `08_decisions/`.
