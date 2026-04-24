# API Design: Conventions

## What this section covers

The 9 layer-specific API specs (`01_geography.md` through `09_delivery.md`) all assume the conventions in this file. Read this first. Every layer doc only documents what's specific to that layer — the response envelope, pagination, error taxonomy, audit emission contract, and RBAC integration are all defined here once.

## Root path

All somaerp endpoints are rooted at `/v1/somaerp/{layer}/...`.

```
/v1/somaerp/geography/...
/v1/somaerp/catalog/...
/v1/somaerp/recipes/...
/v1/somaerp/quality/...
/v1/somaerp/raw-materials/...
/v1/somaerp/procurement/...
/v1/somaerp/production/...
/v1/somaerp/customers/...
/v1/somaerp/delivery/...
```

Multi-word path segments use kebab-case. Plural nouns for collections.

## Response envelope

Every response is wrapped:

```jsonc
// success
{ "ok": true, "data": { ... } }

// error
{ "ok": false, "error": { "code": "NOT_FOUND", "message": "Kitchen abc-123 not found" } }
```

## 5-endpoint shape per sub-feature

The maximum endpoint surface per entity:

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/v1/somaerp/{layer}/{plural}` | List with filters |
| `POST` | `/v1/somaerp/{layer}/{plural}` | Create |
| `GET` | `/v1/somaerp/{layer}/{plural}/{id}` | Read one |
| `PATCH` | `/v1/somaerp/{layer}/{plural}/{id}` | Update (any field, including status) |
| `DELETE` | `/v1/somaerp/{layer}/{plural}/{id}` | Soft-delete (sets `deleted_at`); returns 204 |

Most sub-features need 3-4 endpoints, not all 5.

## State transitions = PATCH

Never action endpoints. State changes ride the `PATCH` request body:

```http
PATCH /v1/somaerp/production/batches/{id}
{ "status": "in_progress" }
```

Forbidden examples:
- `POST /v1/somaerp/production/batches/{id}/start` — wrong; PATCH instead
- `POST /v1/somaerp/customers/subscriptions/{id}/pause` — wrong; PATCH `{"status":"paused"}` plus a separate `POST /pauses` for the pause window record
- `POST /v1/somaerp/recipes/recipes/{id}/publish` — wrong; PATCH `{"status":"active"}`

The service layer enforces allowed transitions; PATCH returns 409 `INVALID_STATE_TRANSITION` if disallowed.

## Filter via query params

No separate `/list-by-status` or `/search` endpoints. Filter the canonical list:

```
GET /v1/somaerp/customers/customers?status=active&service_zone_id=zone-1&q=sri
GET /v1/somaerp/production/batches?kitchen_id=k1&run_date_from=2026-04-01&run_date_to=2026-04-30&status=completed
```

Common filter param names (consistent across layers):
- `status` (single value or comma-separated)
- `q` (free-text search; service-defined fields per entity)
- `{fk}_id` (e.g. `kitchen_id`, `product_id`, `supplier_id`)
- `{date}_from` / `{date}_to` (inclusive ISO date)
- `created_after` / `created_before` (ISO timestamp)
- `include_deleted=true` (admin/audit-only; default false)

Sort: `sort=field` or `sort=-field` (descending). Default sort is `-created_at`.

## Pagination (cursor on UUID v7 ordering)

UUID v7 is time-ordered, so cursor pagination is by `id`:

```
GET /v1/somaerp/{layer}/{plural}?limit=50&cursor=01J9X...
```

Response:
```jsonc
{
  "ok": true,
  "data": {
    "items": [ ... ],
    "page": { "limit": 50, "next_cursor": "01J9X...", "has_more": true }
  }
}
```

`limit` capped at 200. `next_cursor` omitted when `has_more=false`.

## Bulk operations (same path, body array)

POST and PATCH accept a body array for bulk:

```http
POST /v1/somaerp/raw-materials/materials
[
  { "name": "Spinach", ... },
  { "name": "Beetroot", ... }
]
```

Response items are in the same order; per-item failures use a per-item `{ok, data|error}` shape inside `data.items`.

No separate `/bulk` endpoint.

## Tenant scoping (auto-injected)

`tenant_id` is **never accepted from request input**. It is derived server-side from the authenticated session's workspace context (per `02_tenant_model.md`). Attempts to send `tenant_id` in body or query are silently ignored (or 400 in strict mode).

## Authentication

Every endpoint requires:
- a valid tennetctl session bearer token (forwarded by the somaerp frontend), OR
- a service API key for system-to-system calls (workers, schedulers)

Auth handled by middleware that calls `tennetctl_client.resolve_session(...)` and injects `(user_id, session_id, org_id, workspace_id)` into the request context. See `04_integration/01_auth_iam_consumption.md`.

## RBAC

Each endpoint declares one or more required scopes. Scope syntax: `somaerp.{layer}.{action}` where action is `read` / `write` / `admin`. Examples:
- `somaerp.geography.read`
- `somaerp.production.write`
- `somaerp.qc.sign_off`
- `somaerp.procurement.admin`

The middleware checks the resolved roles against the required scope via the tennetctl IAM `/v1/roles?application_id=somaerp&workspace_id=...` lookup.

## Audit emission (mandatory on every mutation)

Every POST / PATCH / DELETE service-layer call emits an audit event before returning, via `tennetctl_client.emit_audit(...)`. The audit envelope carries the four-tuple scope (`user_id`, `session_id`, `org_id`, `workspace_id`) per the project-wide audit-scope-mandatory rule (memory: `feedback_audit_scope_mandatory`).

Audit event keys are namespaced `somaerp.{layer}.{entity}.{action}` and listed per layer in each layer doc's "Audit emission keys" section. Keys mirror the data_model audit list exactly.

Failure outcomes also emit, with `outcome=failure` and the partial scope available.

## Error code taxonomy

| Code | HTTP | When |
|---|---|---|
| `VALIDATION_ERROR` | 400 | request body fails Pydantic validation; details in `error.fields` |
| `MISSING_FIELD` | 400 | required field absent (when not Pydantic) |
| `UNAUTHORIZED` | 401 | no/invalid session token |
| `FORBIDDEN` | 403 | authenticated but lacks required scope |
| `NOT_FOUND` | 404 | entity not found in tenant scope |
| `CONFLICT` | 409 | unique constraint violation (slug taken, dup link row) |
| `INVALID_STATE_TRANSITION` | 409 | state machine rejected (e.g. completed → in_progress) |
| `IMMUTABLE_FIELD` | 409 | attempted to mutate a pinned field (e.g. `recipe_id` on a batch) |
| `CROSS_TENANT_REFERENCE` | 422 | FK pointed at an entity in a different tenant |
| `DEPENDENCY_VIOLATION` | 422 | e.g. trying to archive a recipe currently used by an in_progress batch |
| `RATE_LIMITED` | 429 | tennetctl gateway rate limit |
| `UPSTREAM_ERROR` | 502 | tennetctl primitive call failed (audit emit, vault put, notify dispatch) |
| `INTERNAL_ERROR` | 500 | unexpected |

Error body shape:
```jsonc
{ "ok": false, "error": { "code": "VALIDATION_ERROR", "message": "...", "fields": { "name": "required" } } }
```

## Soft-delete contract

`DELETE` is always soft (sets `deleted_at = now()`) and returns 204. Soft-deleted rows are excluded from default list queries; pass `include_deleted=true` (admin-only scope) to surface them. There is no hard-delete endpoint.

`evt_*` rows are append-only and are never deletable via the API.

## Idempotency

Mutating endpoints accept an optional `Idempotency-Key` header (UUID). The service layer keys on `(tenant_id, route, idempotency_key)` for 24 hours and replays the prior response on duplicate calls. Required for: procurement run creation, production batch creation, delivery run completion (any endpoint that triggers an inventory or money side effect).

## Common response shapes

- Single entity: `data: { ...entity row from v_* view... }`
- List: `data: { items: [...], page: {limit, next_cursor, has_more} }`
- Bulk: `data: { items: [{ok, data|error}, ...] }`
- 204 No Content for soft-delete success and PATCH with no body diff

## API design rule of thumb

Before adding a new route file, ask:
1. Can this fit as a query param on an existing list?
2. Can this fit as a PATCH on an existing entity?
3. Is this a brand-new entity or a relationship that genuinely deserves its own surface?

If the answer to (1) or (2) is yes, do not add a new route.
