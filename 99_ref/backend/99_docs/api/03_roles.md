# Roles API Contract

Base URL: `/api/v1/am/roles`

All endpoints require `Authorization: Bearer <access_token>`.

---

## GET /

List all roles with their levels and assigned permissions.

**Status Code:** `200 OK`
**Permission:** `access_governance_console.view`

### Response Body

```json
{
  "levels": [ ... ],
  "roles": [ ... ]
}
```

**Level object:**

| Field         | Type    |
|---------------|---------|
| `id`          | string  |
| `code`        | string  |
| `name`        | string  |
| `description` | string  |
| `sort_order`  | integer |

Available level codes: `super_admin`, `platform`, `org`, `workspace`

**Role object:**

| Field             | Type    |
|-------------------|---------|
| `id`              | string  |
| `code`            | string  |
| `name`            | string  |
| `description`     | string  |
| `role_level_code` | string  |
| `tenant_key`      | string  |
| `is_active`       | boolean |
| `is_disabled`     | boolean |
| `is_system`       | boolean |
| `permissions`     | array   |
| `created_at`      | string  |
| `updated_at`      | string  |

**Permission object (nested in role):**

| Field                    | Type   |
|--------------------------|--------|
| `id`                     | string |
| `feature_permission_id`  | string |
| `feature_permission_code`| string |
| `feature_flag_code`      | string |
| `permission_action_code` | string |
| `permission_name`        | string |

### Example

```bash
GET /api/v1/am/roles
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "levels": [
    { "id": "uuid-1", "code": "super_admin", "name": "Super Admin", "description": "...", "sort_order": 1 },
    { "id": "uuid-2", "code": "platform", "name": "Platform", "description": "...", "sort_order": 2 },
    { "id": "uuid-3", "code": "org", "name": "Organization", "description": "...", "sort_order": 3 },
    { "id": "uuid-4", "code": "workspace", "name": "Workspace", "description": "...", "sort_order": 4 }
  ],
  "roles": [
    {
      "id": "uuid-5",
      "code": "platform_super_admin",
      "name": "Platform Super Admin",
      "description": "Full platform access",
      "role_level_code": "super_admin",
      "tenant_key": "default",
      "is_active": true,
      "is_disabled": false,
      "is_system": true,
      "permissions": [
        {
          "id": "uuid-6",
          "feature_permission_id": "uuid-7",
          "feature_permission_code": "feature_flag_registry.view",
          "feature_flag_code": "feature_flag_registry",
          "permission_action_code": "view",
          "permission_name": "View Feature Flags"
        }
      ],
      "created_at": "2026-03-14T01:00:00Z",
      "updated_at": "2026-03-14T01:00:00Z"
    }
  ]
}
```

---

## POST /

Create a new role.

**Status Code:** `201 Created`
**Permission:** `group_access_assignment.assign`

### Request Body

| Field             | Type   | Required | Constraints                     |
|-------------------|--------|----------|---------------------------------|
| `code`            | string | yes      | 2–80 chars, pattern `^[a-z0-9_]+$` |
| `name`            | string | yes      | 2–120 chars                     |
| `description`     | string | yes      | 1–500 chars                     |
| `role_level_code` | string | yes      | 1–30 chars, must match existing level |
| `tenant_key`      | string | no       | Default `"default"`, 1–100 chars |

### Response Body

Created role object.

### Example

```bash
POST /api/v1/am/roles
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "code": "robot_role_1710000000",
  "name": "Robot Role",
  "description": "Role created by Robot Framework",
  "role_level_code": "platform"
}
```

```json
// 201 Created
{
  "id": "uuid-new",
  "code": "robot_role_1710000000",
  "name": "Robot Role",
  "description": "Role created by Robot Framework",
  "role_level_code": "platform",
  "tenant_key": "default",
  "is_active": true,
  "is_disabled": false,
  "is_system": false,
  "permissions": [],
  "created_at": "2026-03-14T01:00:00Z",
  "updated_at": "2026-03-14T01:00:00Z"
}
```

### Error Codes

| Status | Condition           |
|--------|---------------------|
| 409    | Code already exists |
| 422    | Validation error    |

---

## PATCH /{role_id}

Update an existing role.

**Status Code:** `200 OK`
**Permission:** `group_access_assignment.assign`

### Path Parameters

| Param     | Type   | Description  |
|-----------|--------|--------------|
| `role_id` | string | Role UUID    |

### Request Body

| Field         | Type    | Required | Constraints |
|---------------|---------|----------|-------------|
| `name`        | string  | no       | 2–120 chars |
| `description` | string  | no       | 1–500 chars |
| `is_disabled` | boolean | no       |             |

### Example

```bash
PATCH /api/v1/am/roles/{role_id}
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "Robot Role Updated",
  "description": "Updated by Robot Framework"
}
```

```json
// 200 OK — returns updated role object
{
  "id": "uuid-new",
  "code": "robot_role_1710000000",
  "name": "Robot Role Updated",
  "description": "Updated by Robot Framework",
  "role_level_code": "platform",
  "tenant_key": "default",
  "is_active": true,
  "is_disabled": false,
  "is_system": false,
  "permissions": [],
  "created_at": "2026-03-14T01:00:00Z",
  "updated_at": "2026-03-14T01:00:00Z"
}
```

---

## POST /{role_id}/permissions

Assign a feature permission to a role.

**Status Code:** `201 Created`
**Permission:** `access_governance_console.assign`

### Path Parameters

| Param     | Type   | Description |
|-----------|--------|-------------|
| `role_id` | string | Role UUID   |

### Request Body

| Field                   | Type   | Required | Constraints |
|-------------------------|--------|----------|-------------|
| `feature_permission_id` | string | yes      | 1–36 chars  |

### Response Body

Updated role object with new permission included.

### Example

```bash
POST /api/v1/am/roles/{role_id}/permissions
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "feature_permission_id": "uuid-perm-1"
}
```

```json
// 201 Created — returns updated role with new permission included
{
  "id": "uuid-new",
  "code": "robot_role_1710000000",
  "permissions": [
    {
      "id": "uuid-link",
      "feature_permission_id": "uuid-perm-1",
      "feature_permission_code": "feature_flag_registry.view",
      "feature_flag_code": "feature_flag_registry",
      "permission_action_code": "view",
      "permission_name": "View Feature Flags"
    }
  ],
  ...
}
```

### Error Codes

| Status | Condition                  |
|--------|----------------------------|
| 404    | Role or permission not found |
| 409    | Permission already assigned  |

---

## DELETE /{role_id}/permissions/{permission_id}

Revoke a feature permission from a role.

**Status Code:** `204 No Content`
**Permission:** `access_governance_console.assign`

### Path Parameters

| Param           | Type   | Description              |
|-----------------|--------|--------------------------|
| `role_id`       | string | Role UUID                |
| `permission_id` | string | Role-permission link UUID |

### Example

```bash
DELETE /api/v1/am/roles/{role_id}/permissions/{permission_id}
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Response Body

None (empty).
