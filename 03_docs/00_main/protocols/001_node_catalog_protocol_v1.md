# NCP v1 — Node Catalog Protocol

**Status:** Draft (approved for Phase 2 implementation)
**Version:** `tennetctl/v1`
**Date:** 2026-04-16

---

## Core Rule

> **Feature → Sub-feature → Node. Sub-features communicate with each other only via nodes, never via direct imports.**

- Inside a sub-feature: import freely.
- Across sub-features: only `run_node(key, ctx, inputs)`.
- The catalog DB is how a node finds another node's handler at runtime.

Everything else in this spec serves that rule.

---

## §1 — Entities & Identity

| Entity | Key grammar | Example | Max len |
|---|---|---|---|
| Module | `{word}` | `iam` | 32 |
| Feature | `{module}` (same key) | `iam` | 32 |
| Sub-feature | `{feature}.{word}` | `iam.orgs` | 64 |
| Node | `{sub_feature}.{word}` | `iam.orgs.create` | 128 |
| Flow *(v1 reserved)* | `{sub_feature}.flow.{word}` | `iam.orgs.flow.provision` | 160 |

**Rules:**
- Lowercase `a–z 0–9 _ .` only, regex `^[a-z][a-z0-9_]*(\.[a-z0-9_]+)*$`.
- Parent key must exist before child can register.
- Keys are **never reused** for 365 days after tombstone.

---

## §2 — Folder Structure

One feature = one directory. Self-contained.

```
backend/02_features/{nn}_{feature}/
├── feature.manifest.yaml                 # source of truth
├── sub_features/
│   └── {nn}_{sub}/
│       ├── __init__.py
│       ├── schemas.py                    # Pydantic API models
│       ├── repository.py                 # asyncpg raw SQL
│       ├── service.py                    # business logic
│       ├── routes.py                     # FastAPI APIRouter
│       └── nodes/
│           ├── __init__.py
│           └── {node_key}.py             # file name = node.key
└── 09_sql_migrations/
    ├── 02_in_progress/
    ├── 01_migrated/
    └── seeds/
```

**Hard rules:**
- Node file name MUST equal `{node.key}.py`. No aliasing.
- The 5-file sub-feature shape (`__init__`, `schemas`, `repository`, `service`, `routes` + `nodes/`) is enforced.
- No hidden agent directories, no `_index.yaml`, no recipes. Simplicity.

---

## §3 — Feature Manifest Grammar

Every feature has exactly one `feature.manifest.yaml`.

```yaml
apiVersion: tennetctl/v1
kind: Feature

metadata:
  key: iam
  number: 03
  module: iam                    # gates with TENNETCTL_MODULES
  always_on: true                # core, iam, audit only
  label: Identity & Access Management
  description: Users, orgs, workspaces, roles, groups
  manifest_version: 1

spec:
  depends_on_modules: []

  sub_features:
    - key: iam.orgs
      number: 01
      label: Organizations
      description: Tenant boundaries

      owns:
        schema: "03_iam"
        tables: ["10_fct_orgs", "40_lnk_user_orgs"]
        seeds:  ["./seeds/01_dim_account_types.yaml"]

      nodes:
        - key: iam.orgs.create
          kind: effect                    # request | effect | control
          handler: sub_features.01_orgs.nodes.iam_orgs_create.CreateOrg
          label: Create Organization
          description: Creates an org with slug and audit entry
          emits_audit: true               # required true for effect
          version: 1
          tags: [identity, write]
          execution:
            timeout_ms: 5000
            retries: 0                    # default 0, max 3
            tx: caller                    # caller | own | none

      routes:
        - method: POST
          path: /v1/orgs
          handler: sub_features.01_orgs.routes.create_org
          node_chain: [iam.auth_required, iam.orgs.create, audit.emit]

      ui_pages:
        - path: /iam/orgs
          component: app/iam/orgs/page.tsx
          label: Organizations
```

**Validation happens at boot.** Malformed manifest = boot fails in dev, logs warning + skips feature in prod.

---

## §4 — Node Contract (Python)

Every node class extends `Node` and declares Pydantic input/output classes on itself. Schemas live in Python — not separate JSON files.

```python
# backend/02_features/03_iam/sub_features/01_orgs/nodes/iam_orgs_create.py

from pydantic import BaseModel
from backend.01_catalog import Node, NodeContext


class CreateOrg(Node):
    key = "iam.orgs.create"              # MUST match manifest
    kind = "effect"

    class Input(BaseModel):
        slug: str
        display_name: str

    class Output(BaseModel):
        id: str
        slug: str

    async def run(self, ctx: NodeContext, inputs: "CreateOrg.Input") -> "CreateOrg.Output":
        # ctx.conn gives a DB connection inside the caller's tx (if tx=caller)
        org_id = await ctx.repo.insert_org(inputs.slug, inputs.display_name)
        return self.Output(id=org_id, slug=inputs.slug)
```

**Validator checks at boot:**
- `importlib` resolves the handler path
- Class inherits `Node`
- `key` attribute matches manifest
- `Input` and `Output` are `BaseModel` subclasses
- `run` is `async def`
- `kind` attribute matches manifest

---

## §5 — Catalog Database (schema `"01_catalog"`)

Strict dim/fct/dtl. Mirrors what's in manifests.

```
dim_modules            id, code, label                     -- core, iam, audit, ...
dim_node_kinds         id, code, label                     -- request, effect, control
dim_tx_modes           id, code                            -- caller, own, none
dim_entity_types       id, code                            -- feature, sub_feature, node

fct_features           id, key, number, module_id, deprecated_at, tombstoned_at
fct_sub_features       id, key, feature_id, number, deprecated_at, tombstoned_at
fct_nodes              id, key, sub_feature_id, kind_id, handler_path,
                       version, emits_audit, timeout_ms, retries, tx_mode_id,
                       deprecated_at, tombstoned_at

dtl_attr_defs          id, entity_type_id, code, value_type
dtl_attrs              id, entity_type_id, entity_id, attr_def_id,
                       key_text, key_jsonb, key_smallint
```

**Attributes via EAV:**
- `label`, `description`, `tags` → `dtl_attrs`
- No schemas-in-DB — the Python class is the source of truth; the catalog just points at the handler.

Flows (`fct_flows`, `fct_flow_nodes`, `lnk_flow_edges`) are **reserved** for v1 but not created until a sub-feature actually needs declarative flow composition (future phase).

---

## §6 — NodeContext

Carried through every `run_node` call. Required for audit scope, RLS, tracing.

```python
@dataclass(frozen=True)
class NodeContext:
    # Identity (audit scope)
    user_id: str | None              # actor; None = system
    session_id: str | None
    org_id: str | None               # tenant
    workspace_id: str | None

    # Tracing
    trace_id: str                    # UUID v7 per inbound request
    span_id: str                     # UUID v7 per node call
    parent_span_id: str | None

    # Runtime
    conn: asyncpg.Connection | None  # None when tx_mode=none
    request_id: str                  # inbound HTTP/event correlation
    audit_category: str              # system | user | integration | setup

    # Policy
    dry_run: bool = False
    timeout_override_ms: int | None = None
```

**Propagation rule:** `run_node` creates a child context with a new `span_id` and `parent_span_id = parent.span_id`. Everything else copies unchanged.

---

## §7 — Node Runner

The only sanctioned way to call across sub-features.

```python
# backend/01_catalog/runner.py

async def run_node(key: str, ctx: NodeContext, inputs: dict) -> dict:
    meta = await catalog.get_node(key)            # DB lookup
    if not meta:
        raise NodeNotFound(key)
    if meta.tombstoned_at:
        raise NodeTombstoned(key)

    # Authorization hook (pluggable — default: deny if no user_id and not system category)
    await authz.check_call(ctx, meta)

    # Resolve handler
    handler_cls = _resolve_handler(meta.handler_path)
    handler = handler_cls()
    validated_input = handler.Input(**inputs)

    # Start child span
    child_ctx = ctx.child_span(key)

    # Apply execution policy
    return await _execute_with_policy(handler, child_ctx, validated_input, meta)
```

**Public API used by sub-features:**
```python
from backend.01_catalog import run_node

org = await run_node("iam.orgs.get", ctx, {"id": org_id})
```

---

## §8 — Execution Policy

Each node declares its policy in the manifest; runner enforces.

| Field | Default | Meaning |
|---|---|---|
| `timeout_ms` | 5000 | Hard wall time before cancellation |
| `retries` | 0 | Auto-retry count on `TransientError` (max 3) |
| `tx` | `caller` | Transaction boundary — see below |

**Transaction modes:**
- `caller` — reuse caller's `ctx.conn` inside caller's open tx. (Default for effect nodes inside a request.)
- `own` — acquire new connection, wrap node in its own tx (commit or rollback independently).
- `none` — no DB connection passed (for pure computation, request-kind gateway nodes, async dispatchers).

**Retries only fire on subclasses of `TransientError`** (network timeout, deadlock detected, serialization failure). Never on `DomainError` or validation failures.

**Idempotency:** when retries > 0, the caller MUST pass an `idempotency_key` in inputs. Runner stores `(node_key, idempotency_key) → output` for 24h and returns cached result on retry.

---

## §9 — Authorization Hook

`authz.check_call(ctx, node_meta)` is called before every node execution.

**Default implementation (v1):**
- If `ctx.audit_category == "system"`: allow.
- If `ctx.user_id is None`: deny (`NodeAuthDenied`).
- Otherwise: allow. (Full RBAC lands in Phase 3 when IAM is seeded.)

**Pluggable:** implementations register via `backend.01_catalog.authz.register_checker()`. Runs in order; first denial wins.

---

## §10 — Cross-Import Rule (enforced)

Validator (in Phase 2 Plan 02-02) scans the tree and rejects any import matching:

```
from backend.02_features.<A>.sub_features.<B> import ...
```

…made from inside `backend/02_features/<X>/sub_features/<Y>` where `(A, B) ≠ (X, Y)`.

**Allowed imports:**
- From `backend.01_core.*` (shared infra)
- From `backend.01_catalog.*` (runner, context, node base)
- Within the same sub-feature's own modules
- `from backend.02_features.<X>.sub_features.<Y>.nodes.* import` — permitted so a route file can declare a `node_chain`, because the chain is compiled to `run_node` calls at wire time, not at import time.

**Enforcement:** validator + pre-commit hook. Violations block commit.

---

## §11 — Boot Sequence

```
1. Parse TENNETCTL_MODULES → enabled_modules set
2. Discover: scan backend/02_features/*/feature.manifest.yaml
3. Validate: each against tennetctl/v1 JSON Schema
4. Filter: drop features whose metadata.module ∉ enabled_modules
5. Resolve: for each node, import_module(handler) must succeed
6. Topsort: order features by depends_on_modules
7. Upsert (one tx per feature):
     fct_features → fct_sub_features → fct_nodes → dtl_attrs
8. Deprecation sweep: keys in DB but absent from manifests → deprecated_at = NOW()
9. Tombstone sweep: deprecated_at older than 180 days → tombstoned_at = NOW()
10. Barrier:
     TENNETCTL_ENV=dev → fail on any error
     TENNETCTL_ENV=prod → log warning, mark sub_feature inactive, continue
```

Boot is idempotent. Running twice produces the same catalog state.

---

## §12 — Lifecycle

```
undeclared ──(manifest entry)──▶ active
                                     │
                                     ▼
                              deprecated (still callable, warned)
                                     │
                                     ▼ (≥180 days)
                              tombstoned (not callable, key locked)
                                     │
                                     ▼ (≥365 days total lock)
                              key_reusable (rare; usually avoid)
```

- To deprecate: add `deprecated_at: 2026-05-01` to the manifest entry.
- To tombstone: remove from manifest; sweep step handles it.
- Calling a deprecated node: logs a warning, still executes.
- Calling a tombstoned node: `NodeTombstoned` exception.

---

## §13 — Versioning (v1 lite)

- Node has integer `version` in manifest.
- Bump version when Input or Output schema is a **breaking** change (new required field, type change, removed field).
- To run two versions in parallel: register as two distinct keys (`iam.orgs.create` and `iam.orgs.create_v2`) with the old one marked `deprecated_at` and `replaced_by: iam.orgs.create_v2`.
- Callers opt into v2 by calling the new key.
- Full semantic versioning (v2) deferred to NCP v2.

---

## §14 — Error Codes (stable)

| Code | Class | When |
|---|---|---|
| `CAT_MANIFEST_INVALID` | boot | YAML fails JSON Schema |
| `CAT_KEY_CONFLICT` | boot | Same key declared in two manifests |
| `CAT_PARENT_MISSING` | boot | Child key declared before parent exists |
| `CAT_HANDLER_UNRESOLVED` | boot | `importlib` fails on handler path |
| `CAT_HANDLER_CONTRACT_MISMATCH` | boot | Class `key`/`kind` ≠ manifest |
| `CAT_CROSS_IMPORT` | lint | Sub-feature imports another sub-feature's module |
| `CAT_NODE_NOT_FOUND` | runtime | `run_node(key)` with unknown key |
| `CAT_NODE_TOMBSTONED` | runtime | `run_node(key)` on tombstoned node |
| `CAT_AUTH_DENIED` | runtime | `authz.check_call` rejected |
| `CAT_TIMEOUT` | runtime | Node exceeded `timeout_ms` |
| `CAT_TRANSIENT` | runtime | Retryable failure class |
| `CAT_IDEMPOTENCY_REQUIRED` | runtime | Retries > 0 but no `idempotency_key` |

---

## §15 — What v1 Does NOT Specify

Explicit out-of-scope for v1, to prevent scope creep:

- Declarative flow execution (`fct_flows`, `lnk_flow_edges`) — reserved but unused
- Visual canvas rendering (React Flow layer)
- APISIX gateway sync for request nodes (separate ADR)
- MCP server integration (v0.2)
- Scaffolder CLI (skipped for simplicity; copy-existing pattern for now)
- `_index.yaml` auto-generation (skipped)
- Async effect dispatch via NATS JetStream (v0.1 hardening phase)
- Node marketplace / external node packages

Any of these lands as its own ADR + protocol revision.

---

## §16 — Consequences

- Every sub-feature is independently shippable (delete directory = feature gone)
- No circular imports possible across sub-features (linter enforces)
- Catalog DB is always a mirror of code — never hand-edited
- Adding a feature = write manifest + 5 files per sub-feature + node classes; restart
- Claude/coding agents operate at the manifest level — one file tells them the shape
- The 1000-node scale works because discovery is a DB query, not a grep

---

## Related Documents

- **CLAUDE.md** — root repo guide; summarizes this protocol
- **ADR-016** — node-first architecture (why nodes)
- **ADR-018** — node contract model (keys, kinds, handler refs)
- **ADR-019** — feature-local vs shared node ownership
- **ADR-021** — gateway compilation boundary
- **ADR-026** — minimum surface principle (API + node rules)
- **ADR-027** — Node Catalog + Runner (this protocol's decision record)
