# API Key Management

Enterprise API key system for programmatic/machine-to-machine access. API keys authenticate as Bearer tokens using the `kctl_` prefix format.

---

## Authentication with API Keys

API keys are used as Bearer tokens in the `Authorization` header, identical to JWTs:

```
Authorization: Bearer kctl_a1b2c3d4_<random_secret>
```

The backend detects the `kctl_` prefix and routes to API key authentication instead of JWT validation.

### Allowed vs Blocked Endpoints

| Category | Endpoints | API Key Access |
|----------|-----------|---------------|
| Feature flags, roles, groups, orgs, workspaces, entity settings, admin | All GET/POST/PATCH/DELETE | Allowed |
| GET /me, GET /me/properties, GET /me/accounts | Read profile | Allowed |
| Invitations | All endpoints | Allowed |
| Auth lifecycle | login, register, refresh, forgot-password, reset-password | N/A (public) |
| Logout | POST /auth/local/logout | Blocked |
| Password | PUT /me/password | Blocked |
| Email verification | verify-email/request, verify-email | Blocked |
| Impersonation | start, end, status | Blocked |
| API key management | All 6 endpoints | Blocked |

### Scopes

API keys optionally restrict permissions via scopes. When scopes are set, the effective permission = intersection of the user's permissions AND the key's scopes. When scopes are NULL, the full user permission set applies.

### Response Headers

API-key-authenticated responses include:

```
X-Auth-Type: api_key
X-Api-Key-Id: <uuid>
```

---

## Management Endpoints

All 6 management endpoints require **JWT authentication only** (API keys are blocked) and cannot be used during impersonation.

| Method | Path | Description | Permission |
|--------|------|-------------|------------|
| POST | `/am/api-keys` | Create API key | `api_key_management.create` |
| GET | `/am/api-keys` | List user's API keys | `api_key_management.view` |
| GET | `/am/api-keys/{key_id}` | Get key details | `api_key_management.view` |
| POST | `/am/api-keys/{key_id}/rotate` | Rotate (revoke old + create new) | `api_key_management.update` |
| PATCH | `/am/api-keys/{key_id}/revoke` | Revoke a key | `api_key_management.revoke` |
| DELETE | `/am/api-keys/{key_id}` | Soft-delete a key | `api_key_management.revoke` |

---

## POST /am/api-keys

Create a new API key. The full key is returned **only once** in the response.

**Status Code:** `201 Created`

### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `name` | string | yes | 1-255 chars |
| `scopes` | string[] | no | Permission codes to restrict access |
| `expires_in_days` | integer | no | 1-365 days |

### Response Body

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | API key UUID |
| `name` | string | Display name |
| `key_prefix` | string | Visible prefix (e.g., `kctl_a1b2c3d4`) |
| `api_key` | string | **Full key — save this, never shown again** |
| `scopes` | string[]? | Restricted scopes, or null for full access |
| `expires_at` | string? | ISO 8601 expiry, or null |
| `created_at` | string | ISO 8601 |

### Example

```bash
POST /api/v1/am/api-keys
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "CI/CD Pipeline",
  "scopes": ["feature_flag_registry.view", "org_management.view"],
  "expires_in_days": 90
}
```

```json
// 201 Created
{
  "id": "uuid-key-1",
  "name": "CI/CD Pipeline",
  "key_prefix": "kctl_a1b2c3d4",
  "api_key": "kctl_a1b2c3d4_xYz...<full_secret>",
  "scopes": ["feature_flag_registry.view", "org_management.view"],
  "expires_at": "2026-06-13T00:00:00",
  "created_at": "2026-03-15T00:00:00"
}
```

---

## GET /am/api-keys

List all API keys for the authenticated user (masked — no full key).

**Status Code:** `200 OK`

### Response Body

| Field | Type |
|-------|------|
| `items` | ApiKeyResponse[] |
| `total` | integer |

---

## GET /am/api-keys/{key_id}

Get details of a specific API key.

**Status Code:** `200 OK`

### Response Body (ApiKeyResponse)

| Field | Type |
|-------|------|
| `id` | string |
| `name` | string |
| `key_prefix` | string |
| `status` | string (`active`, `revoked`, `expired`) |
| `scopes` | string[]? |
| `expires_at` | string? |
| `last_used_at` | string? |
| `last_used_ip` | string? |
| `revoked_at` | string? |
| `revoke_reason` | string? |
| `created_at` | string |

---

## POST /am/api-keys/{key_id}/rotate

Revoke the current key and create a new one with the same name, scopes, and expiry. Returns the new full key.

**Status Code:** `200 OK`

### Response Body

Same as POST create response (includes `api_key` field with full new key).

### Error Codes

| Status | Condition |
|--------|-----------|
| 404 | Key not found |
| 422 | Key is not active |

---

## PATCH /am/api-keys/{key_id}/revoke

Revoke an active API key.

**Status Code:** `200 OK`

### Request Body

| Field | Type | Required |
|-------|------|----------|
| `reason` | string | no (max 500 chars) |

### Response Body

ApiKeyResponse with `status: "revoked"`.

---

## DELETE /am/api-keys/{key_id}

Soft-delete an API key. The key is no longer listed or usable.

**Status Code:** `204 No Content`

---

## Token Format

```
kctl_{id_prefix_8}_{random_secret_54}
```

- `kctl_` — identifiable prefix for log scanning and code detection
- `id_prefix_8` — first 8 hex chars of the key UUID for fast DB lookup
- `random_secret_54` — `secrets.token_urlsafe(40)` random part

The full token is SHA-256 hashed for storage. The DB never stores the raw key.

---

## Audit Events

| Event Type | When | Properties |
|------------|------|------------|
| `api_key_created` | Key created | name, key_prefix, scopes, expires_at |
| `api_key_rotated` | Key rotated | old_key_id, old_key_prefix, new_key_prefix |
| `api_key_revoked` | Key revoked | key_prefix, reason |
| `api_key_deleted` | Key soft-deleted | — |

During API-key-authenticated requests, all downstream audit entries have `session_id = "apikey:{key_id}"`, making every action traceable to the specific key.

---

## Database Tables

| Table | Type | Description |
|-------|------|-------------|
| `45_dim_api_key_statuses` | Dimension | active, revoked, expired |
| `46_fct_api_keys` | Fact | API key records |
