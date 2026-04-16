# User Groups API Contract

Base URL: `/api/v1/am/groups`

All endpoints require `Authorization: Bearer <access_token>`.

---

## GET /

List all user groups with members and assigned roles.

**Status Code:** `200 OK`
**Permission:** `group_access_assignment.view`

### Response Body

```json
{
  "groups": [ ... ]
}
```

**Group object:**

| Field             | Type    |
|-------------------|---------|
| `id`              | string  |
| `code`            | string  |
| `name`            | string  |
| `description`     | string  |
| `role_level_code` | string  |
| `tenant_key`      | string  |
| `is_active`       | boolean |
| `is_system`       | boolean |
| `members`         | array   |
| `roles`           | array   |
| `created_at`      | string  |
| `updated_at`      | string  |

**Member object (nested):**

| Field               | Type    |
|---------------------|---------|
| `id`                | string  |
| `user_id`           | string  |
| `membership_status` | string  |
| `effective_from`    | string  |
| `effective_to`      | string? |

**Role assignment object (nested):**

| Field               | Type   |
|---------------------|--------|
| `id`                | string |
| `role_id`           | string |
| `role_code`         | string |
| `role_name`         | string |
| `role_level_code`   | string |
| `assignment_status` | string |

### Example

```bash
GET /api/v1/am/groups
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "groups": [
    {
      "id": "uuid-1",
      "code": "platform_admins",
      "name": "Platform Admins",
      "description": "Platform administrators group",
      "role_level_code": "platform",
      "tenant_key": "default",
      "is_active": true,
      "is_system": true,
      "members": [
        {
          "id": "uuid-2",
          "user_id": "uuid-user-1",
          "membership_status": "active",
          "effective_from": "2026-03-14T01:00:00Z",
          "effective_to": null
        }
      ],
      "roles": [
        {
          "id": "uuid-3",
          "role_id": "uuid-role-1",
          "role_code": "platform_super_admin",
          "role_name": "Platform Super Admin",
          "role_level_code": "super_admin",
          "assignment_status": "active"
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

Create a new user group.

**Status Code:** `201 Created`
**Permission:** `group_access_assignment.assign`

### Request Body

| Field             | Type   | Required | Constraints                         |
|-------------------|--------|----------|-------------------------------------|
| `code`            | string | yes      | 2–80 chars, pattern `^[a-z0-9_]+$` |
| `name`            | string | yes      | 2–120 chars                         |
| `description`     | string | yes      | 1–500 chars                         |
| `role_level_code` | string | yes      | 1–30 chars, must match existing level (`super_admin`, `platform`, `org`, `workspace`) |
| `tenant_key`      | string | no       | Default `"default"`, 1–100 chars    |

### Response Body

Created group object.

### Example

```bash
POST /api/v1/am/groups
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "code": "robot_group_1710000000",
  "name": "Robot Group",
  "description": "Group created by Robot Framework",
  "role_level_code": "platform"
}
```

```json
// 201 Created
{
  "id": "uuid-new",
  "code": "robot_group_1710000000",
  "name": "Robot Group",
  "description": "Group created by Robot Framework",
  "role_level_code": "platform",
  "tenant_key": "default",
  "is_active": true,
  "is_system": false,
  "members": [],
  "roles": [],
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

## PATCH /{group_id}

Update a user group.

**Status Code:** `200 OK`
**Permission:** `group_access_assignment.assign`

### Path Parameters

| Param      | Type   |
|------------|--------|
| `group_id` | string |

### Request Body

| Field         | Type   | Required | Constraints |
|---------------|--------|----------|-------------|
| `name`        | string | no       | 2–120 chars |
| `description` | string | no       | 1–500 chars |

### Example

```bash
PATCH /api/v1/am/groups/{group_id}
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "name": "Robot Group Updated",
  "description": "Updated by Robot Framework"
}
```

```json
// 200 OK — returns updated group object
{
  "id": "uuid-new",
  "code": "robot_group_1710000000",
  "name": "Robot Group Updated",
  "description": "Updated by Robot Framework",
  ...
}
```

---

## POST /{group_id}/members

Add a user to the group.

**Status Code:** `201 Created`
**Permission:** `group_access_assignment.assign`

### Path Parameters

| Param      | Type   |
|------------|--------|
| `group_id` | string |

### Request Body

| Field     | Type   | Required | Constraints |
|-----------|--------|----------|-------------|
| `user_id` | string | yes      | 1–36 chars  |

### Response Body

Updated group object with new member.

### Example

```bash
POST /api/v1/am/groups/{group_id}/members
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

```json
// 201 Created — returns updated group with new member
{
  "id": "uuid-new",
  "members": [
    {
      "id": "uuid-membership",
      "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "membership_status": "active",
      "effective_from": "2026-03-14T01:00:00Z",
      "effective_to": null
    }
  ],
  ...
}
```

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 404    | Group or user not found |
| 409    | User already a member   |

---

## DELETE /{group_id}/members/{user_id}

Remove a user from the group.

**Status Code:** `204 No Content`
**Permission:** `group_access_assignment.revoke`

### Path Parameters

| Param      | Type   |
|------------|--------|
| `group_id` | string |
| `user_id`  | string |

### Example

```bash
DELETE /api/v1/am/groups/{group_id}/members/{user_id}
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Response Body

None (empty).

---

## POST /{group_id}/roles

Assign a role to the group. All group members inherit this role's permissions.

**Status Code:** `201 Created`
**Permission:** `group_access_assignment.assign`

### Path Parameters

| Param      | Type   |
|------------|--------|
| `group_id` | string |

### Request Body

| Field     | Type   | Required | Constraints |
|-----------|--------|----------|-------------|
| `role_id` | string | yes      | 1–36 chars  |

### Example

```bash
POST /api/v1/am/groups/{group_id}/roles
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "role_id": "uuid-role-1"
}
```

```json
// 201 Created — returns updated group with new role assignment
{
  "id": "uuid-new",
  "roles": [
    {
      "id": "uuid-assignment",
      "role_id": "uuid-role-1",
      "role_code": "platform_super_admin",
      "role_name": "Platform Super Admin",
      "role_level_code": "super_admin",
      "assignment_status": "active"
    }
  ],
  ...
}
```

---

## DELETE /{group_id}/roles/{role_id}

Revoke a role from the group.

**Status Code:** `204 No Content`
**Permission:** `group_access_assignment.revoke`

### Path Parameters

| Param      | Type   |
|------------|--------|
| `group_id` | string |
| `role_id`  | string |

### Example

```bash
DELETE /api/v1/am/groups/{group_id}/roles/{role_id}
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Response Body

None (empty).
