# ADR-026: Minimum Surface Principle — APIs and Nodes

**Status:** Accepted  
**Date:** 2026-04-13

---

## Context

As tennetctl grows in features and sub-features, two failure modes appear repeatedly:

1. **API proliferation** — a new endpoint for every action, a new path for every variant. Developers reach for `POST /activate` when `PATCH /{id}` would do. Lists get duplicated as `GET /active-users` alongside `GET /users?status=active`. The API surface grows faster than the actual behavior.

2. **Node proliferation** — platform concerns get wrapped into feature-specific nodes instead of staying as one configurable shared node. `iam_auth_required`, `vault_auth_required`, `monitoring_auth_required` appear as separate nodes when one `auth_required` node with config covers all three.

Both failures make the system harder to navigate, harder to test, and harder for Claude to reason about (more surface = more noise in every context window).

---

## Decision

**Minimum surface, maximum configurability.**

Every API endpoint and every node must justify its existence against what already exists. The default answer to "should I add a new endpoint/node?" is **no**. The correct pattern is to extend config or query params on what already exists.

---

## API Rules

### One collection path, one item path

```
GET  /v1/orgs          ← list
POST /v1/orgs          ← create
GET  /v1/orgs/{id}     ← get one
PATCH /v1/orgs/{id}    ← all state changes
DELETE /v1/orgs/{id}   ← soft-delete
```

This is the complete surface for a resource. Never add paths alongside these.

### PATCH handles all state changes

All status transitions, all field updates, all flags — `PATCH /{id}` with the field(s) to change.

```http
PATCH /v1/orgs/{id}
{"status": "suspended"}
```

Never: `POST /v1/orgs/{id}/suspend`, `POST /v1/orgs/{id}/activate`.

### Filter params replace list variants

```
GET /v1/users?status=active&org_id=x&role=admin
```

Never: `GET /v1/active-users`, `GET /v1/org-users`, `GET /v1/admin-users`.

### Relations use their own resource path

```
POST /v1/org-members        ← add member to org
DELETE /v1/org-members/{id} ← remove member
```

Never: `POST /v1/orgs/{id}/add-member`, `POST /v1/orgs/{id}/remove-member`.

### The test before adding an endpoint

> "Can an existing endpoint handle this with a query param, a different body field, or a new relation resource?"

If yes: don't add a new endpoint.

---

## Node Rules

### Nodes are platform-level building blocks

A node covers a **cross-cutting platform concern** that appears in flows across multiple features. Feature-specific business logic stays in `service.py` — it is not a node.

Platform concerns that become nodes:
- Auth and access policy enforcement
- Rate limiting
- Feature flag evaluation
- Audit event emission
- Log / trace / metric hooks
- Notification dispatch
- Branching and flow control

Feature logic that stays in service.py:
- Domain validation
- Business rule checks
- Application state writes
- Domain-specific computations

### The test before creating a node

> "Will at least 3 different sub-features or flows use this exact behavior?"

If not, it stays as a plain Python function in `service.py`.

Do not promote a function to a node because it "feels platform-like" or because you might reuse it later.

### One node per concern — config handles variants

Each platform concern is one node. Variation in behavior is expressed through the node's **config schema**, not through separate nodes.

```python
# One node:
auth_required(required_roles=["admin"], allow_api_key=True)

# Not three nodes:
auth_required_admin()
auth_required_with_api_key()
auth_required_strict()
```

### Prefer presets over manual wiring

When a common combination of nodes is used repeatedly, publish it as a **feature-owned preset** (a named, pre-wired flow template). Developers apply the preset instead of wiring nodes individually.

Standard presets:
- `public_api` — rate_limit → run_handler → emit_audit → emit_trace
- `internal_api` — auth_required → rate_limit → run_handler → emit_audit → emit_trace
- `admin_api` — auth_required(roles=["admin"]) → run_handler → emit_audit → emit_trace
- `webhook_endpoint` — verify_signature → run_handler → emit_audit

Presets reduce wiring noise while keeping the underlying flow visible and inspectable.

---

## Why This Matters for Claude

Claude reads the node registry and API surface to compose and scaffold. A bloated surface means:
- More tools in context → degraded tool selection
- More node variants → harder to pick the right one
- More endpoints → harder to find the right path

Minimum surface is not just good engineering — it is what makes the MCP layer and visual canvas useful.

---

## Consequences

- Every new endpoint requires a justification against the "could an existing endpoint handle this?" test
- Every new node requires the "3-feature" justification test
- Node variants are eliminated in favor of configurable nodes
- Presets become the primary composition mechanism for common flows
- CLAUDE.md enforces these rules in every coding session
