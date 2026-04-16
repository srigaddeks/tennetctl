# Admin API Contract

Base URL: `/api/v1/am/admin`

All endpoints require `Authorization: Bearer <access_token>`.

---

## GET /admin/users

List users with pagination and optional search.

**Status Code:** `200 OK`
**Permission:** `admin_console.view`

### Query Parameters

| Param    | Type    | Required | Default | Description                               |
|----------|---------|----------|---------|-------------------------------------------|
| `limit`  | integer | no       | 50      | Max results to return                     |
| `offset` | integer | no       | 0       | Number of results to skip                 |
| `search` | string  | no       | —       | Filter by email or username (ILIKE match) |

### Response Body

| Field   | Type    | Description            |
|---------|---------|------------------------|
| `users` | array   | List of user objects   |
| `total` | integer | Total matching count   |

**User object:**

| Field            | Type    |
|------------------|---------|
| `user_id`        | string  |
| `tenant_key`     | string  |
| `email`          | string  |
| `username`       | string? |
| `email_verified` | boolean |
| `account_status` | string  |

### Example

```bash
GET /api/v1/am/admin/users?limit=10&offset=0&search=jane
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "users": [
    {
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "tenant_key": "default",
      "email": "jane.doe@example.com",
      "username": "janedoe",
      "email_verified": true,
      "account_status": "active"
    }
  ],
  "total": 1
}
```

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 403    | Missing permission     |
| 422    | Validation error       |

---

## GET /admin/users/{user_id}/sessions

List sessions for a specific user.

**Status Code:** `200 OK`
**Permission:** `admin_console.view`

### Path Parameters

| Param     | Type   |
|-----------|--------|
| `user_id` | string |

### Query Parameters

| Param             | Type    | Required | Default | Description                     |
|-------------------|---------|----------|---------|---------------------------------|
| `include_revoked` | boolean | no       | false   | Include revoked sessions        |

### Response Body

Array of session objects:

| Field        | Type    |
|--------------|---------|
| `session_id` | string  |
| `user_id`    | string  |
| `client_ip`  | string? |
| `user_agent` | string? |
| `is_active`  | boolean |
| `created_at` | string  |
| `revoked_at` | string? |

### Example

```bash
GET /api/v1/am/admin/users/a1b2c3d4-e5f6-7890-abcd-ef1234567890/sessions?include_revoked=true
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
[
  {
    "session_id": "uuid-session-1",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "client_ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0 ...",
    "is_active": true,
    "created_at": "2026-03-14T01:00:00Z",
    "revoked_at": null
  },
  {
    "session_id": "uuid-session-2",
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "client_ip": "10.0.0.5",
    "user_agent": "curl/7.88.1",
    "is_active": false,
    "created_at": "2026-03-13T12:00:00Z",
    "revoked_at": "2026-03-13T18:00:00Z"
  }
]
```

---

## DELETE /admin/users/{user_id}/sessions/{session_id}

Revoke a specific session for a user.

**Status Code:** `204 No Content`
**Permission:** `admin_console.update`

### Path Parameters

| Param        | Type   |
|--------------|--------|
| `user_id`    | string |
| `session_id` | string |

### Example

```bash
DELETE /api/v1/am/admin/users/a1b2c3d4-e5f6-7890-abcd-ef1234567890/sessions/uuid-session-1
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Error Codes

| Status | Condition                         |
|--------|-----------------------------------|
| 403    | Missing permission                |
| 404    | User or session not found         |

---

## GET /admin/audit

Query the unified audit log with filters.

**Status Code:** `200 OK`
**Permission:** `admin_console.view`

### Query Parameters

| Param         | Type    | Required | Default | Description                          |
|---------------|---------|----------|---------|--------------------------------------|
| `entity_type` | string  | no       | —       | Filter by entity type (e.g., `user`, `session`, `role`) |
| `actor_id`    | string  | no       | —       | Filter by actor UUID                 |
| `event_type`  | string  | no       | —       | Filter by event type (e.g., `login_succeeded`) |
| `limit`       | integer | no       | 50      | Max results to return                |
| `offset`      | integer | no       | 0       | Number of results to skip            |

### Response Body

| Field    | Type    | Description            |
|----------|---------|------------------------|
| `events` | array   | List of audit events   |
| `total`  | integer | Total matching count   |

**Audit event object:**

| Field            | Type    |
|------------------|---------|
| `event_id`       | string  |
| `entity_type`    | string  |
| `entity_id`      | string  |
| `event_type`     | string  |
| `event_category` | string  |
| `actor_id`       | string? |
| `actor_type`     | string  |
| `created_at`     | string  |
| `properties`     | object  |

### Example

```bash
GET /api/v1/am/admin/audit?entity_type=session&event_type=login_succeeded&limit=5
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "events": [
    {
      "event_id": "uuid-event-1",
      "entity_type": "session",
      "entity_id": "uuid-session-1",
      "event_type": "login_succeeded",
      "event_category": "auth",
      "actor_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "actor_type": "user",
      "created_at": "2026-03-14T01:00:00Z",
      "properties": {
        "client_ip": "192.168.1.100",
        "user_agent": "Mozilla/5.0 ..."
      }
    }
  ],
  "total": 1
}
```

---

## GET /admin/impersonation/history

List impersonation sessions with pagination.

**Status Code:** `200 OK`
**Permission:** `admin_console.view`

### Query Parameters

| Param    | Type    | Required | Default | Description              |
|----------|---------|----------|---------|--------------------------|
| `limit`  | integer | no       | 50      | Max results to return    |
| `offset` | integer | no       | 0       | Number of results to skip |

### Response Body

| Field      | Type    | Description                       |
|------------|---------|-----------------------------------|
| `sessions` | array   | List of impersonation sessions    |
| `total`    | integer | Total count                       |

**Impersonation session object:**

| Field              | Type    |
|--------------------|---------|
| `session_id`       | string  |
| `impersonator_id`  | string  |
| `target_user_id`   | string  |
| `reason`           | string  |
| `is_active`        | boolean |
| `started_at`       | string  |
| `ended_at`         | string? |

### Example

```bash
GET /api/v1/am/admin/impersonation/history?limit=10
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "sessions": [
    {
      "session_id": "uuid-imp-session-1",
      "impersonator_id": "admin-user-uuid",
      "target_user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "reason": "Investigating issue #1234 reported by user",
      "is_active": false,
      "started_at": "2026-03-14T01:00:00Z",
      "ended_at": "2026-03-14T01:15:00Z"
    }
  ],
  "total": 1
}
```

---

## GET /admin/me/features

Evaluate feature flags for the current authenticated user. Returns all feature flags with their resolved state based on the user's roles and permissions.

**Status Code:** `200 OK`
**Auth:** Bearer token required (no extra permission — evaluates own features)

### Response Body

| Field      | Type  | Description                     |
|------------|-------|---------------------------------|
| `features` | array | List of evaluated feature flags |

**Feature object:**

| Field       | Type    |
|-------------|---------|
| `code`      | string  |
| `name`      | string  |
| `is_active` | boolean |
| `category`  | string  |

### Example

```bash
GET /api/v1/am/admin/me/features
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "features": [
    {
      "code": "admin_console",
      "name": "Admin Console",
      "is_active": true,
      "category": "platform"
    },
    {
      "code": "user_impersonation",
      "name": "User Impersonation",
      "is_active": true,
      "category": "platform"
    },
    {
      "code": "org_management",
      "name": "Organization Management",
      "is_active": false,
      "category": "platform"
    }
  ]
}
```
