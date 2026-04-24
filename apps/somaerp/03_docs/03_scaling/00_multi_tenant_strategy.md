# Multi-Tenant Strategy

> How somaerp scales from one tenant (Soma Delights) to many on a single Postgres — and what the path to v1.0 sharding looks like.

## v0.9.0 stance: single Postgres, `tenant_id` as the natural shard key

somaerp v0.9.0 runs every tenant on one Postgres database (the tennetctl DB itself, under `somaerp_*` schemas). Tenant isolation is enforced in three layers:

1. **Column-level:** every `fct_*` and `evt_*` row carries `tenant_id UUID NOT NULL`, whose value is a tennetctl `workspace_id` (per ADR-001).
2. **Query-level:** the repo layer always injects `tenant_id = $ctx_workspace_id` from the authenticated session's workspace context. The repo layer never accepts `tenant_id` from request input.
3. **Index-level:** every composite index leads with `tenant_id` so that every hot-path query scan is physically scoped to one tenant's row range.

That is the entire multi-tenant implementation for v0.9.0. No separate schema per tenant, no separate database per tenant, no cross-tenant read paths.

## Optional defense-in-depth: per-workspace RLS

Postgres Row Level Security can be enabled per-tenant on the heaviest tables (`fct_production_batches`, `evt_inventory_movements`, `fct_customers`, `evt_delivery_stops`). Policy shape:

```text
CREATE POLICY tenant_isolation ON fct_production_batches
  USING (tenant_id = current_setting('somaerp.workspace_id')::uuid);
```

The somaerp connection wrapper calls `SET LOCAL somaerp.workspace_id = '<ws>'` on every checkout. RLS is OFF by default in v0.9.0; turn ON per deployment when the operator wants a hard DB-level backstop in addition to the app-level filter. Documented knob, not a code path change.

## The schema decisions v0.9.0 is making on purpose to enable later sharding

Every one of these is a choice made now so that a tenant→shard migration later is a data move, not a rewrite:

| Decision | How it helps a future shard | Where it lives |
| --- | --- | --- |
| UUID v7 primary keys on every `fct_*` | PKs are globally unique across shards without coordination | `backend.01_core.id.uuid7()` |
| `tenant_id` on every `fct_*` and `evt_*` | Natural shard key; never recompute membership | Every table |
| No cross-tenant FKs | A tenant's rows never reference another tenant's rows, so a shard move copies a closed graph | Schema migrations enforce via composite indexes |
| `tenant_id` leading every composite index | Shard-local queries stay shard-local after split | Schema migrations |
| Append-only `evt_*` (inventory movements, QC checks, delivery stops) | Shardable without reconciling mutable state | ADR-006, ADR-005 |
| Views (`v_*`) are thin | No cross-tenant joins buried in views | Every layer's data_model doc |
| `properties JSONB` extension instead of columns-per-tenant | Tenant-specific custom fields never require DDL | Every `fct_*` per the hybrid model |

## Path to v1.0 multi-tenant scale

v1.0 is explicitly out of this phase's scope. The documented intent:

### Stage A — Read replicas per region

- Configure Postgres logical replication from the primary to one read replica per serving region.
- somaerp backends in each region route read-only traffic to the local replica; writes always go to the primary.
- `v_*` views work unchanged. No schema change.

### Stage B — Tenant→shard routing (horizontal shard)

- Introduce a small `meta.tenant_shards (workspace_id, shard_id, cluster_dsn)` lookup, owned by tennetctl.
- somaerp boot resolves `workspace_id` via tennetctl `whoami`, then asks tennetctl `/v1/tenant-shards/{workspace_id}` for the cluster DSN for that tenant.
- somaerp opens its connection pool against the resolved cluster.
- No application code reads across shards. Cross-tenant analytics (if ever needed) are a separate warehouse concern, not a somaerp concern.

### Stage C — Per-tenant database for enterprise

- For an enterprise tenant demanding hard isolation, the shard-per-tenant shape is the same as Stage B with one tenant per cluster.
- Offered as a deployment topology, not a code path. The somaerp backend is identical; only the `tenant_shards` lookup differs.

### What does NOT happen at v1.0

- No two-phase commit across shards. Cross-tenant writes are impossible by construction (no cross-tenant FKs).
- No per-tenant schema migrations. Every tenant gets the same schema on every shard.
- No bespoke per-tenant branches of the code.

## What breaks if the v0.9.0 rules are violated

Every one of these would make later sharding an order of magnitude more expensive. These are the blast-radius lines that code reviews enforce now:

- A `fct_*` row without `tenant_id` → a tenant moving shards would orphan that row.
- A cross-tenant FK (e.g. "this kitchen references a raw material that belongs to another tenant") → shard moves break the FK.
- A query that filters by `kitchen_id` without also filtering by `tenant_id` → cross-tenant row leak via a colliding key.
- A background job that iterates across all tenants in one transaction → can't split.

Code review uses these as blocker-severity findings.

## Capacity envelope at v0.9.0

Soma Delights at Stage 1 (home kitchen): ~30 bottles/day, ~10 procurement events/week, ~40 QC events/day, ~30 delivery stops/day. Postgres handles this easily. Even at Stage 3 (production unit, ~250 bottles/day, ~150 QC events/day, ~200 delivery stops/day) the aggregate write rate across 50 Soma-Delights-sized tenants is under 10,000 events/day — trivially within one modest Postgres. Sharding is a capability question (per-region latency, per-tenant isolation demand), not a capacity question, until well past 1000 tenants at this shape.

## Related documents

- `../00_main/02_tenant_model.md` — the tenant_id = workspace_id decision
- `../00_main/08_decisions/001_tenant_boundary_org_vs_workspace.md`
- `01_multi_region_kitchen_topology.md` — intra-tenant multi-region model
- `03_data_residency_compliance.md` — residency enforced by deployment topology
- `.claude/rules/common/database.md` — project-wide DB conventions
