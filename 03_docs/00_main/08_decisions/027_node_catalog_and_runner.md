# ADR-027: Node Catalog + Runner

**Status:** Accepted
**Date:** 2026-04-16
**Related:** NCP v1 (`03_docs/00_main/protocols/001_node_catalog_protocol_v1.md`), ADR-016, ADR-018, ADR-019, ADR-026

---

## Context

ADR-016 committed us to node-first architecture and ADR-018 defined the node contract. They did not answer: when there are hundreds of sub-features and thousands of nodes, how does a sub-feature actually **call** another sub-feature's behavior at runtime?

Three bad answers we need to rule out:

1. **Direct imports across sub-features** — `from backend.02_features.03_iam.sub_features.01_orgs.service import get_org`. This is how every codebase degrades into spaghetti; once it starts, it's hard to reverse. It also makes module gating (`TENNETCTL_MODULES`) impossible because import time is not the same as runtime enablement.

2. **A shared service layer** — all business logic in a god object that every sub-feature imports. Destroys the sub-feature boundary and the self-contained-feature rule from ADR-019.

3. **Function registry without a DB** — a Python dict like `REGISTRY["iam.orgs.get"] = get_org`. Works at small scale. Breaks at 1000 entries: no search, no UI introspection, no deprecation signal, no cross-module gating, no audit of what exists vs what runs.

We need a mechanism that is (a) strict about cross-sub-feature boundaries, (b) introspectable from a DB, (c) works with TENNETCTL_MODULES gating, (d) agents can reason about without grep.

---

## Decision

Adopt the **Node Catalog Protocol v1** (NCP v1, `protocols/001_node_catalog_protocol_v1.md`) as the single mechanism for cross-sub-feature calls.

Three components, taken together:

### 1. Feature Manifest (`feature.manifest.yaml`)

One YAML file per feature declares every sub-feature, every node, every route, and every UI page the feature owns. It is the **source of truth** for what exists in the feature. Deleting the feature directory deletes the feature; nothing scattered elsewhere.

### 2. Catalog Database (`"01_catalog"` schema)

Postgres tables mirror the manifests. On boot, every manifest is read and upserted into `fct_features`, `fct_sub_features`, `fct_nodes` (keyed by the stable key). The catalog is the **index**; code is the **behavior**. They stay synchronized via the boot loader.

### 3. Node Runner (`run_node`)

The only sanctioned mechanism for a sub-feature to invoke behavior in another sub-feature:

```python
from backend.01_catalog import run_node

org = await run_node("iam.orgs.get", ctx, {"id": org_id})
```

Runner resolves the handler through the catalog DB, validates input through the node's Pydantic class, applies execution policy (timeout, retry, tx mode), propagates `NodeContext` for audit + tracing, and returns validated output.

### Enforcement

A validator (Phase 2 Plan 02-02) rejects any cross-sub-feature import at lint time. Violations block commit. This is the **teeth** that makes the rule real instead of aspirational.

---

## Consequences

### Positive

- **Sub-features are truly independent.** Zero compile-time coupling across sub-feature boundaries.
- **Module gating works.** If a module isn't in `TENNETCTL_MODULES`, its nodes aren't in the catalog; callers get `NodeNotFound` instead of an ImportError at boot.
- **Scales to 1000s of nodes.** Discovery is a DB query, not a filesystem scan.
- **Catalog is inspectable.** UI, validator, audit, future MCP layer all read the same source.
- **Audit scope always propagates.** `NodeContext` carries `user_id / session_id / org_id / workspace_id / trace_id` through every call; impossible to bypass.
- **Agents (Claude) have one contract to learn.** Read the manifest for a feature and you know the shape.

### Negative

- **Runtime dispatch overhead.** A few hundred μs per cross-call vs a direct function call. Acceptable at current scale; bulk nodes exist for hot paths (see §4 below).
- **Catalog drift risk.** If the code is changed but the manifest isn't updated, boot warns/fails. Validator prevents this from merging.
- **Indirection cost for readers.** Grepping `run_node("iam.orgs.get"...)` is one step removed from the handler. We accept this because the file naming rule (`{node_key}.py`) makes the reverse lookup deterministic.

### Breaking from prior assumptions

- **ADR-018 node contract** (keys, kinds, handler refs) stands — NCP v1 is its operational instantiation.
- **Plans that assumed direct cross-feature imports** are rejected in code review. No such plans have shipped yet.

---

## Escape Hatches

Two intentional exceptions, because zero escape hatches breaks under real load.

### 1. Bulk Nodes

A caller that would otherwise loop `run_node("iam.orgs.get", ...)` 1000 times SHOULD instead call a bulk variant: `run_node("iam.orgs.get_many", ctx, {"ids": [...]})`. The bulk node lives in the same sub-feature as the single-get node. Pattern: provide bulk nodes alongside single-item nodes for any read path that might be iterated.

### 2. Shared Infra (`backend.01_core.*` and `backend.01_catalog.*`)

These are framework-level. All sub-features import them. They are not features and have no sub-features, so the cross-import rule does not apply.

No other escape hatches are permitted in v1.

---

## Alternatives Considered

### Direct function imports (rejected)

Fastest; simplest to write. Rejected because it makes module gating impossible and produces untraceable coupling. Also incompatible with the enterprise audit requirement that every cross-concern call emit an audit event — import-time calls have no hook for this.

### gRPC between sub-features (rejected)

Microservices-grade isolation, but massively over-engineered for an in-process monolith that happens to be modular. Adds serialization cost on every call and forces us to define a second IDL (protobuf) on top of Pydantic.

### Dependency-injection container (considered, rejected for v1)

A DI framework could enforce boundaries at construction time. Rejected because (a) Python DI is non-standard and adds a heavy dependency, (b) the lint + runtime catalog pair achieves the same end with explicit, inspectable machinery instead of a framework's magic.

### Event bus only (rejected)

Fine for fire-and-forget effects, broken for request/response flows. Some cross-sub-feature calls need a return value (e.g., `get_org` returns an org dict). We keep NATS JetStream for high-volume ingest and outbox events (ADR-011 era), not as the primary cross-call channel.

---

## Implementation Path

Phase 2 Plans:
- **02-01** — NCP v1 doc + ADR-027 (this) + catalog DB schema (`01_catalog`)
- **02-02** — Manifest loader, boot upsert, validator (incl. cross-import lint), `/tnt` skill
- **02-03** — Node runner + execution policy + NodeContext + authorization hook

Phase 3+ consumes it:
- 03-01 IAM schema (relocated from old 02-01, dependency added)
- 03-02 IAM feature.manifest.yaml — proves the pattern with a real feature
- 03-03 Audit schema + `emit_audit` node — first cross-cutting node called by everyone
- 03-04 Views + EAV refinement

---

## Why This Matters for Claude

Every coding agent working in this repo operates at the manifest level. Given a feature key, the agent:

1. Reads `backend/02_features/{nn}_{feature}/feature.manifest.yaml`
2. Knows every node, table, route, page the feature owns
3. Can add a new node by copying an existing file and adding a manifest entry
4. Never needs to grep to find "does a node already do X?" — queries the catalog

One contract to learn. One file to read per feature. The rest is deterministic.
