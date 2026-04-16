# ADR-024: MCP Integration Model — Generic Graph Tools, Not Per-Feature Tools

**Status:** Accepted
**Date:** 2026-04-13

---

## Context

TennetCTL integrates with Claude Code via an MCP (Model Context Protocol) server. The MCP server exposes tools that Claude can use to navigate, inspect, and scaffold the node graph.

The naive approach — one MCP tool per feature or sub-feature — creates a tool explosion problem:

```
iam_get_user, iam_list_roles, audit_query_events,
monitoring_get_metrics, vault_get_secret, flags_list... (×100+)
```

MCP tool lists are included in every request context. Too many tools:
1. Consume significant context window, leaving less room for actual work
2. Degrade Claude's tool selection accuracy (more tools = more selection noise)
3. Require constant maintenance as features are added

---

## Decision

**The TennetCTL MCP server exposes 5 generic graph-operation tools, not per-feature tools.**

---

## Tools

```
inspect(target: "node" | "flow" | "feature" | "sub_feature", id: str) → contract/graph
search(query: str, scope?: str) → list of matching nodes/features/flows
scaffold(type: "node" | "sub_feature" | "flow", spec: dict) → generated boilerplate
validate(workflow_id: str) → validation result against node contracts
run(node_key: str, input: dict) → execute a node in sandbox mode
```

### Tool responsibilities

**`inspect`** — Returns the full contract, graph, or metadata for any addressable entity. Claude calls `search` to find something, then `inspect` to get its full detail. The MCP server handles routing: `inspect("node", "iam.auth_required")` returns the node contract; `inspect("flow", "user.signup")` returns the full React Flow-compatible graph.

**`search`** — Full-text + semantic search across node registry, feature index, and flow definitions. Returns a short list of matches with IDs. Claude uses this as the entry point before `inspect`.

**`scaffold`** — Generates boilerplate code (node Python class, sub-feature directory structure, flow definition) from a spec dict. Returns file paths and content to write. Does not write files directly — returns content for Claude to review and apply.

**`validate`** — Validates a workflow graph against node contracts: checks that all node keys exist, edge types are valid, required config fields are present, and runtime class rules are respected. Returns a structured list of errors.

**`run`** — Executes a single node in a sandboxed context with synthetic input. Useful for testing node behavior during development. Requires explicit enablement; disabled in production deployments.

---

## Rationale

**The Filesystem MCP precedent:**
The Filesystem MCP server doesn't expose `read_python_file`, `read_json_file`, `read_md_file`. It exposes `read_file(path)`. Generic operations with smart internal dispatch is the correct pattern.

**Graph traversal, not feature API:**
Claude doesn't need to know which feature owns a node. It needs to find nodes, inspect their contracts, and scaffold new ones. The MCP server owns the routing — Claude just asks questions.

**Tool count discipline:**
5 tools. Not 5 per feature. Not one per node. 5 total. This stays constant regardless of how many features or nodes tennetctl grows to.

---

## Internal Architecture

The MCP server is a separate Python process that connects to tennetctl's node registry at startup. It does not expose the same HTTP API as the main backend — it has direct programmatic access to the registry.

```
Claude Code ──MCP─→ tennetctl-mcp-server
                          │
                          ├── node_registry (in-memory, loaded from backend)
                          ├── feature_index (from 03_docs/features/)
                          └── flow_store (from DB via read-only connection)
```

The MCP server is read-mostly. `scaffold` returns content but doesn't write. `run` is the only stateful operation and requires explicit configuration to enable.

---

## Consequences

- MCP server is a separate optional process (`mcp/` directory in the project root).
- Tool count stays at 5 regardless of feature growth — this is a hard constraint.
- Feature teams do not add MCP tools for their features. The generic tools cover all use cases.
- `inspect` is the workhorse — it must handle all entity types cleanly.
- `search` must be fast — it's the first call in most Claude sessions.
