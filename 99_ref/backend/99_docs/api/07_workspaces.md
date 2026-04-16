# Workspaces API Contract

Base URL: `/api/v1/am`

All endpoints except `GET /workspace-types` require `Authorization: Bearer <access_token>`.

Workspaces belong to an organization. All workspace endpoints are nested under `/orgs/{org_id}/workspaces`.

---

## GET /workspace-types

List all available workspace types. **Public endpoint — no auth required.**

**Status Code:** `200 OK`

### Response Body

Array of workspace type objects:

| Field                   | Type    |
|-------------------------|---------|
| `code`                  | string  |
| `name`                  | string  |
| `description`           | string? |
| `is_infrastructure_type`| boolean |

### Example

```bash
GET /api/v1/am/workspace-types
```

```json
// 200 OK — no auth required
[
  { "code": "development", "name": "Development", "description": null, "is_infrastructure_type": false },
  { "code": "staging", "name": "Staging", "description": null, "is_infrastructure_type": false },
  { "code": "production", "name": "Production", "description": null, "is_infrastructure_type": false }
]
```

---

## GET /orgs/{org_id}/workspaces

List workspaces within an organization.

**Status Code:** `200 OK`
**Permission:** `workspace_management.view` (scoped to `org_id`)

### Path Parameters

| Param    | Type   |
|----------|--------|
| `org_id` | string |

### Response Body

```json
{
  "items": [ ... ],
  "total": 3
}
```

**Workspace object:**

| Field                 | Type    |
|-----------------------|---------|
| `id`                  | string  |
| `org_id`              | string  |
| `workspace_type_code` | string  |
| `product_id`          | string? |
| `name`                | string  |
| `slug`                | string  |
| `description`         | string? |
| `is_active`           | boolean |
| `created_at`          | string  |
| `updated_at`          | string  |

### Example

```bash
GET /api/v1/am/orgs/{org_id}/workspaces
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "items": [
    {
      "id": "uuid-ws-1",
      "org_id": "uuid-org-1",
      "workspace_type_code": "development",
      "product_id": null,
      "name": "Robot Workspace",
      "slug": "robot-ws-1710000000",
      "description": "Workspace created by Robot Framework",
      "is_active": true,
      "created_at": "2026-03-14T01:00:00Z",
      "updated_at": "2026-03-14T01:00:00Z"
    }
  ],
  "total": 1
}
```

---

## POST /orgs/{org_id}/workspaces

Create a new workspace within an organization.

**Status Code:** `201 Created`
**Permission:** `workspace_management.create` (scoped to `org_id`)

### Path Parameters

| Param    | Type   |
|----------|--------|
| `org_id` | string |

### Request Body

| Field                 | Type   | Required | Constraints                                   |
|-----------------------|--------|----------|-----------------------------------------------|
| `name`                | string | yes      | 1–120 chars                                   |
| `slug`                | string | yes      | Pattern `^[a-z0-9][a-z0-9\-]{1,60}[a-z0-9]$` |
| `workspace_type_code` | string | yes      | 1–50 chars, must match existing type          |
| `product_id`          | string | no       | Product UUID                                  |
| `description`         | string | no       |                                               |

### Response Body

Created workspace object.

### Example

```bash
POST /api/v1/am/orgs/{org_id}/workspaces
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "Robot Workspace",
  "slug": "robot-ws-1710000000",
  "workspace_type_code": "development",
  "description": "Workspace created by Robot Framework"
}
```

```json
// 201 Created
{
  "id": "uuid-ws-new",
  "org_id": "uuid-org-1",
  "workspace_type_code": "development",
  "product_id": null,
  "name": "Robot Workspace",
  "slug": "robot-ws-1710000000",
  "description": "Workspace created by Robot Framework",
  "is_active": true,
  "created_at": "2026-03-14T01:00:00Z",
  "updated_at": "2026-03-14T01:00:00Z"
}
```

### Error Codes

| Status | Condition           |
|--------|---------------------|
| 404    | Org not found       |
| 409    | Slug already exists |
| 422    | Validation error    |

---

## PATCH /orgs/{org_id}/workspaces/{workspace_id}

Update a workspace.

**Status Code:** `200 OK`
**Permission:** `workspace_management.update` (scoped to `workspace_id`)

### Path Parameters

| Param          | Type   |
|----------------|--------|
| `org_id`       | string |
| `workspace_id` | string |

### Request Body

| Field         | Type    | Required | Constraints |
|---------------|---------|----------|-------------|
| `name`        | string  | no       | 1–120 chars |
| `description` | string  | no       |             |
| `product_id`  | string  | no       | Product UUID |
| `is_disabled` | boolean | no       |             |

### Example

```bash
PATCH /api/v1/am/orgs/{org_id}/workspaces/{workspace_id}
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "Robot Workspace Updated",
  "description": "Updated by Robot Framework"
}
```

```json
// 200 OK — returns updated workspace object
{
  "id": "uuid-ws-new",
  "name": "Robot Workspace Updated",
  "description": "Updated by Robot Framework",
  ...
}
```

---

## GET /orgs/{org_id}/workspaces/{workspace_id}/members

List members of a workspace.

**Status Code:** `200 OK`
**Permission:** `workspace_management.view` (scoped to `workspace_id`)

### Path Parameters

| Param          | Type   |
|----------------|--------|
| `org_id`       | string |
| `workspace_id` | string |

### Response Body

Array of member objects:

| Field          | Type    |
|----------------|---------|
| `id`           | string  |
| `workspace_id` | string  |
| `user_id`      | string  |
| `role`         | string  |
| `is_active`    | boolean |
| `joined_at`    | string  |

### Example

```bash
GET /api/v1/am/orgs/{org_id}/workspaces/{workspace_id}/members
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
[
  {
    "id": "uuid-membership",
    "workspace_id": "uuid-ws-1",
    "user_id": "uuid-user-1",
    "role": "contributor",
    "is_active": true,
    "joined_at": "2026-03-14T01:00:00Z"
  }
]
```

---

## POST /orgs/{org_id}/workspaces/{workspace_id}/members

Add a member to a workspace.

**Status Code:** `201 Created`
**Permission:** `workspace_management.assign` (scoped to `org_id` + `workspace_id`)

### Path Parameters

| Param          | Type   |
|----------------|--------|
| `org_id`       | string |
| `workspace_id` | string |

### Request Body

| Field     | Type   | Required | Constraints                                                |
|-----------|--------|----------|------------------------------------------------------------|
| `user_id` | string | yes      | User UUID                                                  |
| `role`    | string | no       | Default `"contributor"`. Values: `owner`, `admin`, `contributor`, `viewer`, `readonly` |

### Response Body

Created member object.

### Example

```bash
POST /api/v1/am/orgs/{org_id}/workspaces/{workspace_id}/members
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "contributor"
}
```

```json
// 201 Created
{
  "id": "uuid-membership",
  "workspace_id": "uuid-ws-1",
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "role": "contributor",
  "is_active": true,
  "joined_at": "2026-03-14T01:00:00Z"
}
```

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 404    | Workspace not found    |
| 409    | User already a member  |

### DB Membership Type Constraint

Allowed values: `owner`, `admin`, `contributor`, `viewer`, `readonly`

> **Note:** Unlike org memberships which use `member`, workspace memberships use `contributor` as the standard role.

---

## PATCH /orgs/{org_id}/workspaces/{workspace_id}/members/{target_user_id}

Change a member's role within the workspace.

**Status Code:** `200 OK`
**Permission:** `workspace_management.assign` (scoped to `org_id` + `workspace_id`)

### Path Parameters

| Param            | Type   |
|------------------|--------|
| `org_id`         | string |
| `workspace_id`   | string |
| `target_user_id` | string |

### Request Body

| Field  | Type   | Required | Constraints                                                |
|--------|--------|----------|------------------------------------------------------------|
| `role` | string | yes      | `owner`, `admin`, `contributor`, `viewer`, `readonly`      |

### Example

```bash
PATCH /api/v1/am/orgs/{org_id}/workspaces/{workspace_id}/members/{target_user_id}
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
  "workspace_id": "uuid-ws-1",
  "user_id": "a1b2c3d4-...",
  "role": "admin",
  "is_active": true,
  "joined_at": "2026-03-14T01:00:00Z"
}
```

---

## DELETE /orgs/{org_id}/workspaces/{workspace_id}/members/{target_user_id}

Remove a member from a workspace.

**Status Code:** `204 No Content`
**Permission:** `workspace_management.revoke` (scoped to `org_id` + `workspace_id`)

### Path Parameters

| Param            | Type   |
|------------------|--------|
| `org_id`         | string |
| `workspace_id`   | string |
| `target_user_id` | string |

### Example

```bash
DELETE /api/v1/am/orgs/{org_id}/workspaces/{workspace_id}/members/{target_user_id}
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Response Body

None (empty).
