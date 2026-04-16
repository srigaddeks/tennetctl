# Access Context API Contract

Base URL: `/api/v1/am`

Requires `Authorization: Bearer <access_token>`.

---

## GET /access

Returns the authenticated user's full access context — what they can do at platform, org, and workspace level.

**Status Code:** `200 OK`

### Query Parameters

| Param          | Type   | Required | Description                              |
|----------------|--------|----------|------------------------------------------|
| `org_id`       | string | no       | Scope context to a specific organization |
| `workspace_id` | string | no       | Scope context to a specific workspace    |

### Response Body

| Field               | Type    | Description                              |
|---------------------|---------|------------------------------------------|
| `user_id`           | string  | Authenticated user's UUID                |
| `tenant_key`        | string  | Tenant identifier                        |
| `platform`          | object  | Platform-level access context            |
| `current_org`       | object? | Org-level context (if `org_id` provided) |
| `current_workspace` | object? | Workspace-level context (if `workspace_id` provided) |

**Platform object:**

| Field     | Type  | Description                 |
|-----------|-------|-----------------------------|
| `actions` | array | Available platform actions  |

**Action object (in `platform.actions`):**

| Field           | Type    |
|-----------------|---------|
| `feature_code`  | string  |
| `feature_name`  | string  |
| `action_code`   | string  |
| `category_code` | string  |
| `access_mode`   | string  |
| `env_dev`       | boolean |
| `env_staging`   | boolean |
| `env_prod`      | boolean |

**Org context object (when `org_id` is specified):**

| Field           | Type   |
|-----------------|--------|
| `org_id`        | string |
| `name`          | string |
| `slug`          | string |
| `org_type_code` | string |
| `actions`       | array  |

**Workspace context object (when `workspace_id` is specified):**

| Field                 | Type    |
|-----------------------|---------|
| `workspace_id`        | string  |
| `org_id`              | string  |
| `name`                | string  |
| `slug`                | string  |
| `workspace_type_code` | string  |
| `product_id`          | string? |
| `product_name`        | string? |
| `product_code`        | string? |
| `actions`             | array   |
| `product_actions`     | array   |

### How Permission Resolution Works

Actions are resolved through the permission chain:

```
user → group_membership → user_group → group_role_assignment → role → role_feature_permission → feature_permission
```

Scope inheritance (additive):
- **Platform scope** — only platform-level groups (no `scope_org_id` or `scope_workspace_id`)
- **Org scope** — platform groups + groups scoped to that org
- **Workspace scope** — platform groups + org groups + workspace groups

### Example — Platform Only

```bash
GET /api/v1/am/access
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tenant_key": "default",
  "platform": {
    "actions": [
      {
        "feature_code": "feature_flag_registry",
        "feature_name": "Feature Flag Registry",
        "action_code": "view",
        "category_code": "auth",
        "access_mode": "permissioned",
        "env_dev": true,
        "env_staging": true,
        "env_prod": true
      },
      {
        "feature_code": "access_governance_console",
        "feature_name": "Access Governance Console",
        "action_code": "view",
        "category_code": "auth",
        "access_mode": "permissioned",
        "env_dev": true,
        "env_staging": true,
        "env_prod": true
      }
    ]
  },
  "current_org": null,
  "current_workspace": null
}
```

### Example — With Org and Workspace Scope

```bash
GET /api/v1/am/access?org_id=uuid-org-1&workspace_id=uuid-ws-1
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK — includes org and workspace context with additive actions
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tenant_key": "default",
  "platform": { "actions": [ ... ] },
  "current_org": {
    "org_id": "uuid-org-1",
    "name": "My Organization",
    "slug": "my-org",
    "org_type_code": "company",
    "actions": [ ... ]
  },
  "current_workspace": {
    "workspace_id": "uuid-ws-1",
    "org_id": "uuid-org-1",
    "name": "Dev Workspace",
    "slug": "dev-ws",
    "workspace_type_code": "development",
    "product_id": null,
    "product_name": null,
    "product_code": null,
    "actions": [ ... ],
    "product_actions": []
  }
}
```

> **Note:** `org_id` and `workspace_id` come from API query parameters, NOT from JWT claims. The JWT only contains `user_id`. Users can switch org/workspace context freely in the UI.

### Error Codes

| Status | Condition              |
|--------|------------------------|
| 401    | Missing/invalid token  |
