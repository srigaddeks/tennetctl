# Organizations API Contract

Base URL: `/api/v1/am`

All endpoints except `GET /org-types` require `Authorization: Bearer <access_token>`.

---

## GET /org-types

List all available organization types. **Public endpoint — no auth required.**

**Status Code:** `200 OK`

### Response Body

Array of org type objects:

| Field         | Type    |
|---------------|---------|
| `code`        | string  |
| `name`        | string  |
| `description` | string? |

Available types: `community`, `company`, `government`, `nonprofit`, `education`, `personal`, `other`

### Example

```bash
GET /api/v1/am/org-types
```

```json
// 200 OK — no auth required
[
  { "code": "community", "name": "Community", "description": null },
  { "code": "company", "name": "Company", "description": null },
  { "code": "government", "name": "Government", "description": null },
  { "code": "nonprofit", "name": "Nonprofit", "description": null },
  { "code": "education", "name": "Education", "description": null },
  { "code": "personal", "name": "Personal", "description": null },
  { "code": "other", "name": "Other", "description": null }
]
```

---

## GET /orgs

List organizations the user has access to.

**Status Code:** `200 OK`
**Permission:** `org_management.view`

### Response Body

```json
{
  "items": [ ... ],
  "total": 5
}
```

**Org object:**

| Field           | Type    |
|-----------------|---------|
| `id`            | string  |
| `tenant_key`    | string  |
| `org_type_code` | string  |
| `name`          | string  |
| `slug`          | string  |
| `description`   | string? |
| `is_active`     | boolean |
| `created_at`    | string  |
| `updated_at`    | string  |

### Example

```bash
GET /api/v1/am/orgs
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "items": [
    {
      "id": "uuid-org-1",
      "tenant_key": "default",
      "org_type_code": "community",
      "name": "Robot Org",
      "slug": "robot-org-1710000000",
      "description": "Org created by Robot Framework",
      "is_active": true,
      "created_at": "2026-03-14T01:00:00Z",
      "updated_at": "2026-03-14T01:00:00Z"
    }
  ],
  "total": 1
}
```

---

## POST /orgs

Create a new organization.

**Status Code:** `201 Created`
**Permission:** `org_management.create`

### Request Body

| Field           | Type   | Required | Constraints                                    |
|-----------------|--------|----------|------------------------------------------------|
| `name`          | string | yes      | 1–120 chars                                    |
| `slug`          | string | yes      | Pattern `^[a-z0-9][a-z0-9\-]{1,60}[a-z0-9]$`  |
| `org_type_code` | string | yes      | 1–50 chars, must match existing org type        |
| `description`   | string | no       |                                                 |

### Response Body

Created org object.

### Example

```bash
POST /api/v1/am/orgs
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "Robot Org",
  "slug": "robot-org-1710000000",
  "org_type_code": "community",
  "description": "Org created by Robot Framework"
}
```

```json
// 201 Created
{
  "id": "uuid-org-new",
  "tenant_key": "default",
  "org_type_code": "community",
  "name": "Robot Org",
  "slug": "robot-org-1710000000",
  "description": "Org created by Robot Framework",
  "is_active": true,
  "created_at": "2026-03-14T01:00:00Z",
  "updated_at": "2026-03-14T01:00:00Z"
}
```

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 409    | Slug already exists    |
| 422    | Validation error       |

---

## PATCH /orgs/{org_id}

Update an organization.

**Status Code:** `200 OK`
**Permission:** `org_management.update` (scoped to `org_id`)

### Path Parameters

| Param    | Type   |
|----------|--------|
| `org_id` | string |

### Request Body

| Field         | Type    | Required | Constraints |
|---------------|---------|----------|-------------|
| `name`        | string  | no       | 1–120 chars |
| `description` | string  | no       |             |
| `is_disabled` | boolean | no       |             |

### Example

```bash
PATCH /api/v1/am/orgs/{org_id}
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "Robot Org Updated",
  "description": "Updated by Robot Framework"
}
```

```json
// 200 OK — returns updated org object
{
  "id": "uuid-org-new",
  "name": "Robot Org Updated",
  "description": "Updated by Robot Framework",
  ...
}
```

---

## GET /orgs/{org_id}/members

List members of an organization.

**Status Code:** `200 OK`
**Permission:** `org_management.view` (scoped to `org_id`)

### Path Parameters

| Param    | Type   |
|----------|--------|
| `org_id` | string |

### Response Body

Array of member objects:

| Field        | Type    |
|--------------|---------|
| `id`         | string  |
| `org_id`     | string  |
| `user_id`    | string  |
| `role`       | string  |
| `is_active`  | boolean |
| `joined_at`  | string  |

### Example

```bash
GET /api/v1/am/orgs/{org_id}/members
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
[
  {
    "id": "uuid-membership",
    "org_id": "uuid-org-1",
    "user_id": "uuid-user-1",
    "role": "member",
    "is_active": true,
    "joined_at": "2026-03-14T01:00:00Z"
  }
]
```

---

## POST /orgs/{org_id}/members

Add a member to an organization.

**Status Code:** `201 Created`
**Permission:** `org_management.assign` (scoped to `org_id`)

### Path Parameters

| Param    | Type   |
|----------|--------|
| `org_id` | string |

### Request Body

| Field     | Type   | Required | Constraints                              |
|-----------|--------|----------|------------------------------------------|
| `user_id` | string | yes      | User UUID                                |
| `role`    | string | no       | Default `"member"`. Values: `owner`, `admin`, `member`, `viewer` |

### Response Body

Created member object.

### Example

```bash
POST /api/v1/am/orgs/{org_id}/members
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "member"
}
```

```json
// 201 Created
{
  "id": "uuid-membership",
  "org_id": "uuid-org-1",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "member",
  "is_active": true,
  "joined_at": "2026-03-14T01:00:00Z"
}
```

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 404    | Org or user not found  |
| 409    | User already a member  |

---

## DELETE /orgs/{org_id}/members/{target_user_id}

Remove a member from an organization.

**Status Code:** `204 No Content`
**Permission:** `org_management.revoke` (scoped to `org_id`)

### Path Parameters

| Param            | Type   |
|------------------|--------|
| `org_id`         | string |
| `target_user_id` | string |

### Example

```bash
DELETE /api/v1/am/orgs/{org_id}/members/{target_user_id}
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Response Body

None (empty).

---

## PATCH /orgs/{org_id}/members/{target_user_id}

Change a member's role within the organization.

**Status Code:** `200 OK`
**Permission:** `org_management.assign` (scoped to `org_id`)

### Path Parameters

| Param            | Type   |
|------------------|--------|
| `org_id`         | string |
| `target_user_id` | string |

### Request Body

| Field  | Type   | Required | Constraints                                          |
|--------|--------|----------|------------------------------------------------------|
| `role` | string | yes      | `owner`, `admin`, `member`, `viewer`, `billing`      |

### Example

```bash
PATCH /api/v1/am/orgs/{org_id}/members/{target_user_id}
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "role": "admin"
}
```

```json
// 200 OK — returns updated member object
{
  "id": "uuid-membership",
  "org_id": "uuid-org-1",
  "user_id": "a1b2c3d4-...",
  "role": "admin",
  "is_active": true,
  "joined_at": "2026-03-14T01:00:00Z"
}
```

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 404    | Membership not found   |
| 422    | Invalid role value     |

---

### DB Membership Type Constraint

Allowed values: `owner`, `admin`, `member`, `viewer`, `billing`
