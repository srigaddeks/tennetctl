# Impersonation API Contract

Base URL: `/api/v1/am/impersonation`

All endpoints require `Authorization: Bearer <access_token>`.

Permission: `user_impersonation.enable` (to start impersonation).

**Prerequisites:** The `IMPERSONATION_ENABLED` environment variable must be set to `true`.

---

## POST /impersonation/start

Start impersonating a target user. Creates a short-lived impersonation session with tokens that operate as the target user.

**Status Code:** `200 OK`
**Permission:** `user_impersonation.enable`

### Request Body

| Field            | Type   | Required | Constraints                      |
|------------------|--------|----------|----------------------------------|
| `target_user_id` | string | yes      | UUID of the user to impersonate  |
| `reason`         | string | yes      | Min 5 chars, max 500 chars       |

### Response Body

| Field                       | Type   | Notes                                  |
|-----------------------------|--------|----------------------------------------|
| `access_token`              | string | JWT with impersonation claims          |
| `token_type`                | string | Always `Bearer`                        |
| `expires_in`                | int    | Access token TTL (default 900s)        |
| `refresh_token`             | string | Short-lived refresh token              |
| `refresh_expires_in`        | int    | Refresh token TTL (default 1800s)      |
| `target_user`               | object | Target user profile (AuthUserResponse) |
| `impersonation_session_id`  | string | UUID of the impersonation session      |

### Impersonation JWT Claims

The access token contains additional claims:

| Claim     | Value             | Purpose                     |
|-----------|-------------------|-----------------------------|
| `sub`     | target user's ID  | Token acts as target user   |
| `imp`     | `true`            | Impersonation flag          |
| `imp_sub` | admin's user ID   | Real actor identity         |
| `imp_sid` | admin's session   | Admin's original session ID |

### Example

```bash
POST /api/v1/am/impersonation/start
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "target_user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "reason": "Investigating issue #1234 reported by user"
}
```

```json
// 200 OK
{
  "access_token": "eyJhbGciOi...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "session-id.secret",
  "refresh_expires_in": 1800,
  "target_user": {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "tenant_key": "default",
    "email": "targetuser@example.com",
    "username": "targetuser",
    "email_verified": true,
    "account_status": "pending_verification"
  },
  "impersonation_session_id": "uuid-session-1"
}
```

### Error Codes

| Status | Condition                                                   |
|--------|-------------------------------------------------------------|
| 403    | Impersonation not enabled, missing permission, or target has elevated role |
| 403    | Already impersonating (nested impersonation blocked)        |
| 404    | Target user not found                                       |
| 409    | Admin already has an active impersonation session           |
| 422    | Validation error (reason too short, etc.)                   |

### Safety Guardrails

- Cannot impersonate users with `super_admin` or `platform` role levels
- Cannot start impersonation while already impersonating (no nesting)
- Only one active impersonation session per admin at a time
- Reason is mandatory and recorded in the audit trail
- Tokens have shorter TTL than normal sessions

---

## POST /impersonation/end

End the current impersonation session. Revokes the impersonation session and returns the admin's user ID so the client can switch back.

**Status Code:** `200 OK`
**Auth:** Must be called with an impersonation token

### Response Body

| Field                  | Type   | Notes                           |
|------------------------|--------|---------------------------------|
| `message`              | string | `"Impersonation session ended."` |
| `impersonator_user_id` | string | Admin's user ID to switch back  |

### Example

```bash
POST /api/v1/am/impersonation/end
Authorization: Bearer eyJhbGciOi...  # impersonation token
```

```json
// 200 OK
{
  "message": "Impersonation session ended.",
  "impersonator_user_id": "admin-user-uuid"
}
```

### Error Codes

| Status | Condition                              |
|--------|----------------------------------------|
| 403    | Current session is not impersonation   |

---

## GET /impersonation/status

Check whether the current session is an impersonation session.

**Status Code:** `200 OK`

### Response Body

| Field              | Type    | Notes                                        |
|--------------------|---------|----------------------------------------------|
| `is_impersonating` | boolean | `true` if current token is impersonation     |
| `impersonator_id`  | string  | Admin's user ID (null if not impersonating)  |
| `target_user_id`   | string  | Target user ID (null if not impersonating)   |
| `session_id`       | string  | Impersonation session ID (null if not)       |
| `expires_at`       | string  | Token expiration ISO 8601 (null if not)      |

### Example (impersonating)

```bash
GET /api/v1/am/impersonation/status
Authorization: Bearer eyJhbGciOi...  # impersonation token
```

```json
// 200 OK
{
  "is_impersonating": true,
  "impersonator_id": "admin-user-uuid",
  "target_user_id": "target-user-uuid",
  "session_id": "impersonation-session-uuid",
  "expires_at": "2026-03-14T12:15:00+00:00"
}
```

### Example (normal session)

```json
// 200 OK
{
  "is_impersonating": false,
  "impersonator_id": null,
  "target_user_id": null,
  "session_id": null,
  "expires_at": null
}
```

---

## Response Headers

Every API response made with an impersonation token includes:

| Header                   | Value            | Notes                            |
|--------------------------|------------------|----------------------------------|
| `X-Impersonation-Active` | `true`           | Present only during impersonation |
| `X-Impersonator-Id`      | admin's user ID  | Present only during impersonation |

---

## Restrictions During Impersonation

The following actions are blocked while impersonating:

| Action                    | Endpoint                              | Error  |
|---------------------------|---------------------------------------|--------|
| Change email              | `PUT /auth/local/me/properties/email` | 403    |
| Change username           | `PUT /auth/local/me/properties/username` | 403 |
| Delete email              | `DELETE /auth/local/me/properties/email` | 403  |
| Delete username           | `DELETE /auth/local/me/properties/username` | 403 |
| Start nested impersonation | `POST /am/impersonation/start`       | 403    |

All other endpoints work normally, with the impersonating admin seeing the target user's permissions and data.

---

## Audit Trail

All actions during impersonation are recorded in `40_aud_events` with:

- `actor_type` = `"impersonated_user"` (distinguishes from normal `"user"`)
- Audit properties include `impersonator_id` and `impersonation_session_id`

Impersonation lifecycle events:

| Event Type               | When                    | Entity Type |
|--------------------------|-------------------------|-------------|
| `impersonation_started`  | Admin starts session    | `session`   |
| `impersonation_ended`    | Admin ends session      | `session`   |

---

## Configuration

| Environment Variable                       | Default | Description                    |
|--------------------------------------------|---------|--------------------------------|
| `IMPERSONATION_ENABLED`                    | `false` | Kill switch for the feature    |
| `IMPERSONATION_ACCESS_TOKEN_TTL_SECONDS`   | `900`   | Access token TTL (15 min)      |
| `IMPERSONATION_REFRESH_TOKEN_TTL_SECONDS`  | `1800`  | Refresh token TTL (30 min)     |
