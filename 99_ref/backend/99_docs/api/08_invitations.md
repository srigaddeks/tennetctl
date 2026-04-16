# Invitations API Contract

Base URL: `/api/v1/am`

All endpoints require `Authorization: Bearer <access_token>` unless noted otherwise.

Permission: `invitation_management.{action}` (view, create, revoke).

---

## POST /invitations

Create a new invitation. The `invite_token` is returned **only on creation** and cannot be retrieved again.

**Status Code:** `201 Created`
**Permission:** `invitation_management.create`

### Request Body

| Field              | Type   | Required | Constraints                                                    |
|--------------------|--------|----------|----------------------------------------------------------------|
| `email`            | string | yes      | Valid email address (lowercased)                               |
| `scope`            | string | yes      | `platform`, `organization`, or `workspace`                    |
| `org_id`           | string | cond.    | Required when scope = `organization` or `workspace`           |
| `workspace_id`     | string | cond.    | Required when scope = `workspace`                             |
| `role`             | string | cond.    | Required when scope = `organization` or `workspace`           |
| `expires_in_hours` | int    | no       | Default `72`. Min `1`, max `720` (30 days)                    |

**Valid roles by scope:**

| Scope          | Allowed Roles                                        |
|----------------|------------------------------------------------------|
| `platform`     | *(none — role must be null)*                         |
| `organization` | `owner`, `admin`, `member`, `viewer`, `billing`      |
| `workspace`    | `owner`, `admin`, `contributor`, `viewer`, `readonly` |

### Response Body

| Field          | Type   | Notes                        |
|----------------|--------|------------------------------|
| `id`           | string | Invitation UUID              |
| `email`        | string |                              |
| `scope`        | string |                              |
| `org_id`       | string | null for platform scope      |
| `workspace_id` | string | null unless workspace scope  |
| `role`         | string | null for platform scope      |
| `status`       | string | Always `pending` on creation |
| `invite_token` | string | **Only returned on create**  |
| `expires_at`   | string | ISO 8601 datetime            |
| `created_at`   | string | ISO 8601 datetime            |

### Example

```bash
POST /api/v1/am/invitations
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "email": "newuser@example.com",
  "scope": "organization",
  "org_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "member",
  "expires_in_hours": 72
}
```

```json
// 201 Created
{
  "id": "uuid-invite-1",
  "email": "newuser@example.com",
  "scope": "organization",
  "org_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "workspace_id": null,
  "role": "member",
  "status": "pending",
  "invite_token": "uuid-invite-1.urlsafe-secret-32-chars",
  "expires_at": "2026-03-16T00:00:00Z",
  "created_at": "2026-03-13T00:00:00Z"
}
```

### Error Codes

| Status | Condition                                        |
|--------|--------------------------------------------------|
| 400    | Invalid scope/role combination                   |
| 409    | Duplicate pending invite for same email+scope    |
| 422    | Validation error (missing required fields, etc.) |

---

## GET /invitations

List invitations with optional filters and pagination.

**Status Code:** `200 OK`
**Permission:** `invitation_management.view`

### Query Parameters

| Param       | Type   | Default | Notes                              |
|-------------|--------|---------|------------------------------------|
| `scope`     | string | —       | Filter: `platform`, `organization`, `workspace` |
| `status`    | string | —       | Filter: `pending`, `accepted`, `revoked`, `expired`, `declined` |
| `email`     | string | —       | Partial match on invitee email     |
| `page`      | int    | `1`     | Min `1`                            |
| `page_size` | int    | `50`    | Min `1`, max `200`                 |

### Response Body

```json
{
  "items": [ ... ],
  "total": 45,
  "page": 1,
  "page_size": 50
}
```

**Invitation object:**

| Field          | Type   |
|----------------|--------|
| `id`           | string |
| `email`        | string |
| `scope`        | string |
| `org_id`       | string |
| `workspace_id` | string |
| `role`         | string |
| `status`       | string |
| `expires_at`   | string |
| `created_at`   | string |
| `updated_at`   | string |

### Example

```bash
GET /api/v1/am/invitations?status=pending&page=1&page_size=20
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "items": [
    {
      "id": "uuid-invite-1",
      "email": "newuser@example.com",
      "scope": "organization",
      "org_id": "uuid-org-1",
      "workspace_id": null,
      "role": "member",
      "status": "pending",
      "expires_at": "2026-03-16T00:00:00Z",
      "created_at": "2026-03-13T00:00:00Z",
      "updated_at": "2026-03-13T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

---

## GET /invitations/stats

Aggregate invitation counts by status for dashboard display.

**Status Code:** `200 OK`
**Permission:** `invitation_management.view`

### Response Body

| Field      | Type | Notes                     |
|------------|------|---------------------------|
| `total`    | int  | All invitations           |
| `pending`  | int  | Awaiting acceptance       |
| `accepted` | int  | Successfully accepted     |
| `expired`  | int  | Past deadline             |
| `revoked`  | int  | Manually revoked by admin |
| `declined` | int  | Declined by invitee       |

### Example

```bash
GET /api/v1/am/invitations/stats
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "total": 150,
  "pending": 45,
  "accepted": 80,
  "expired": 20,
  "revoked": 5,
  "declined": 0
}
```

---

## GET /invitations/{invitation_id}

Get details of a single invitation.

**Status Code:** `200 OK`
**Permission:** `invitation_management.view`

### Path Parameters

| Param           | Type   |
|-----------------|--------|
| `invitation_id` | string |

### Response Body

Single invitation object (same fields as list items).

### Example

```bash
GET /api/v1/am/invitations/{invitation_id}
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "id": "uuid-invite-1",
  "email": "newuser@example.com",
  "scope": "organization",
  "org_id": "uuid-org-1",
  "workspace_id": null,
  "role": "member",
  "status": "pending",
  "expires_at": "2026-03-16T00:00:00Z",
  "created_at": "2026-03-13T00:00:00Z",
  "updated_at": "2026-03-13T00:00:00Z"
}
```

### Error Codes

| Status | Condition          |
|--------|--------------------|
| 404    | Invitation not found |

---

## PATCH /invitations/{invitation_id}/revoke

Revoke a pending invitation. Only `pending` invitations can be revoked.

**Status Code:** `200 OK`
**Permission:** `invitation_management.revoke`

### Path Parameters

| Param           | Type   |
|-----------------|--------|
| `invitation_id` | string |

### Response Body

Updated invitation object with `status: "revoked"`.

### Example

```bash
PATCH /api/v1/am/invitations/{invitation_id}/revoke
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "id": "uuid-invite-1",
  "email": "newuser@example.com",
  "scope": "organization",
  "status": "revoked",
  ...
}
```

### Error Codes

| Status | Condition                          |
|--------|------------------------------------|
| 400    | Invitation is not in pending state |
| 404    | Invitation not found               |

---

## POST /invitations/accept

Accept an invitation using the invite token. **Public endpoint — no auth required.**

**Status Code:** `200 OK`

### Request Body

| Field          | Type   | Required | Notes                          |
|----------------|--------|----------|--------------------------------|
| `invite_token` | string | yes      | Token from invitation creation |

### Response Body

| Field          | Type   | Notes                                |
|----------------|--------|--------------------------------------|
| `message`      | string | `"Invitation accepted"`              |
| `scope`        | string | Scope of the invitation              |
| `org_id`       | string | null for platform scope              |
| `workspace_id` | string | null unless workspace scope          |
| `role`         | string | Role assigned (null for platform)    |

### Example

```bash
POST /api/v1/am/invitations/accept
Content-Type: application/json

{
  "invite_token": "uuid-invite-1.urlsafe-secret-32-chars"
}
```

```json
// 200 OK
{
  "message": "Invitation accepted",
  "scope": "organization",
  "org_id": "uuid-org-1",
  "workspace_id": null,
  "role": "member"
}
```

### Error Codes

| Status | Condition                              |
|--------|----------------------------------------|
| 400    | Invitation already accepted or revoked |
| 404    | Invalid or expired token               |

---

## Registration Auto-Accept

When a new user registers via `POST /auth/local/register`, the system automatically checks for pending invitations matching the user's email. For each matching invitation:

1. The invitation status is updated to `accepted`
2. If the invitation scope is `organization`, the user is added to the org with the specified role
3. If the invitation scope is `workspace`, the user is added to the workspace with the specified role

This happens transparently during registration — no additional API call is needed.
