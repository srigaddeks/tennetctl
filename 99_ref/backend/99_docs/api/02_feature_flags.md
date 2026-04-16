# Feature Flags API Contract

Base URL: `/api/v1/am/features`

All endpoints require `Authorization: Bearer <access_token>`.

---

## GET /

List all feature flag categories and flags with their permissions.

**Status Code:** `200 OK`
**Permission:** `feature_flag_registry.view`

### Response Body

```json
{
  "categories": [ ... ],
  "flags": [ ... ]
}
```

**Category object:**

| Field         | Type    |
|---------------|---------|
| `id`          | string  |
| `code`        | string  |
| `name`        | string  |
| `description` | string  |
| `sort_order`  | integer |

**Flag object:**

| Field              | Type    | Description                                        |
|--------------------|---------|----------------------------------------------------|
| `id`               | string  | UUID                                               |
| `code`             | string  | Unique code (snake_case)                           |
| `name`             | string  | Display name                                       |
| `description`      | string  | Description                                        |
| `category_code`    | string  | Parent category code                               |
| `feature_scope`    | string  | `platform` / `org` / `product`                     |
| `access_mode`      | string  | `public` / `authenticated` / `permissioned`        |
| `lifecycle_state`  | string  | `planned` / `active` / `deprecated` / `retired`    |
| `initial_audience` | string  | Target audience                                    |
| `env_dev`          | boolean | Enabled in development                             |
| `env_staging`      | boolean | Enabled in staging                                 |
| `env_prod`         | boolean | Enabled in production                              |
| `org_visibility`   | string? | For org-scoped flags: `hidden` / `locked` / `unlocked`. Null for platform/product flags. |
| `required_license` | string? | Minimum license tier required: `free` / `pro` / `enterprise` / `internal`. Null if no restriction. |
| `permissions`      | array   | Permission objects (see below)                     |
| `created_at`       | string  | ISO timestamp                                      |
| `updated_at`       | string  | ISO timestamp                                      |

**Permission object (nested in flag):**

| Field                    | Type   |
|--------------------------|--------|
| `id`                     | string |
| `code`                   | string |
| `feature_flag_code`      | string |
| `permission_action_code` | string |
| `name`                   | string |
| `description`            | string |

### Feature Scope

| Scope      | Description |
|------------|-------------|
| `platform` | Applies globally. Controlled only by super admins. |
| `org`      | Can be toggled per-organization by org admins (subject to `org_visibility` setting). |
| `product`  | Product-specific feature. Controlled by super admins. |

### Org Visibility (org-scoped flags only)

| Value      | Description |
|------------|-------------|
| `hidden`   | Org admins cannot see this flag. Default for new org-scoped flags. |
| `locked`   | Org admins can see the flag but cannot change it. System default applies. |
| `unlocked` | Org admins can see and toggle this flag for their organization. |

Managed via Entity Settings API: `PUT /api/v1/am/settings/feature/{code}/org_visibility`

### Required License

When set, the flag is only available to organizations on the specified license tier or higher. Tier hierarchy: `free < partner < pro_trial < pro < enterprise < internal`.

Managed via Entity Settings API: `PUT /api/v1/am/settings/feature/{code}/required_license`

### Example

```bash
GET /api/v1/am/features
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "categories": [
    {
      "id": "uuid-1",
      "code": "auth",
      "name": "Authentication",
      "description": "Authentication features",
      "sort_order": 1
    }
  ],
  "flags": [
    {
      "id": "uuid-2",
      "code": "feature_flag_registry",
      "name": "Feature Flag Registry",
      "description": "Manage feature flags",
      "category_code": "auth",
      "feature_scope": "platform",
      "access_mode": "permissioned",
      "lifecycle_state": "active",
      "initial_audience": "platform_super_admin",
      "env_dev": true,
      "env_staging": true,
      "env_prod": true,
      "org_visibility": null,
      "required_license": null,
      "permissions": [
        {
          "id": "uuid-3",
          "code": "feature_flag_registry.view",
          "feature_flag_code": "feature_flag_registry",
          "permission_action_code": "view",
          "name": "View Feature Flags",
          "description": "View feature flag registry"
        }
      ],
      "created_at": "2026-03-14T01:00:00Z",
      "updated_at": "2026-03-14T01:00:00Z"
    }
  ]
}
```

---

## GET /org-available

List org-scoped feature flags visible to org admins. **No platform-level permission required** — any authenticated user can call this endpoint.

Returns only flags where:
- `feature_scope = "org"`
- `org_visibility` is `"locked"` or `"unlocked"` (hidden flags are excluded)

**Status Code:** `200 OK`
**Permission:** Authenticated (no specific permission)

### Response Body

```json
{
  "categories": [ ... ],
  "flags": [ ... ]
}
```

**Flag object (org-available):**

| Field              | Type    | Description |
|--------------------|---------|-------------|
| `id`               | string  | UUID |
| `code`             | string  | Feature flag code |
| `name`             | string  | Display name |
| `description`      | string  | Description |
| `category_code`    | string  | Parent category |
| `feature_scope`    | string  | Always `"org"` |
| `lifecycle_state`  | string  | Lifecycle state |
| `env_dev`          | boolean | Enabled in dev |
| `env_staging`      | boolean | Enabled in staging |
| `env_prod`         | boolean | Enabled in prod |
| `org_visibility`   | string  | `"locked"` or `"unlocked"` |
| `required_license` | string? | Minimum tier required |
| `permissions`      | array   | Permission objects |

### Example

```bash
GET /api/v1/am/features/org-available
Authorization: Bearer eyJhbGciOi...
```

---

## POST /

Create a new feature flag.

**Status Code:** `201 Created`
**Permission:** `feature_flag_registry.create`

### Request Body

| Field              | Type    | Required | Constraints                                          |
|--------------------|---------|----------|------------------------------------------------------|
| `code`             | string  | yes      | 2-80 chars, pattern `^[a-z0-9_]+$`                  |
| `name`             | string  | yes      | 2-120 chars                                          |
| `description`      | string  | yes      | 1-500 chars                                          |
| `category_code`    | string  | yes      | 1-50 chars, must match existing category             |
| `feature_scope`    | string  | no       | Default `"platform"`. Values: `platform`, `org`, `product` |
| `access_mode`      | string  | yes      | `public` / `authenticated` / `permissioned`          |
| `lifecycle_state`  | string  | no       | Default `"planned"`. Values: `planned`, `active`, `deprecated`, `retired` |
| `initial_audience` | string  | no       | Default `"platform_super_admin"`, max 60 chars       |
| `env_dev`          | boolean | no       | Default `false`                                      |
| `env_staging`      | boolean | no       | Default `false`                                      |
| `env_prod`         | boolean | no       | Default `false`                                      |

### Response Body

Same as flag object in list response.

### Error Codes

| Status | Condition           |
|--------|---------------------|
| 409    | Code already exists |
| 422    | Validation error    |

---

## PATCH /{code}

Update an existing feature flag by code.

**Status Code:** `200 OK`
**Permission:** `feature_flag_registry.update`

### Path Parameters

| Param  | Type   | Description      |
|--------|--------|------------------|
| `code` | string | Feature flag code |

### Request Body

All fields are optional. Only provided fields are updated.

| Field             | Type    | Constraints                              |
|-------------------|---------|------------------------------------------|
| `name`            | string  | 2-120 chars                              |
| `description`     | string  | 1-500 chars                              |
| `category_code`   | string  | 1-50 chars, must match existing category |
| `feature_scope`   | string  | `platform` / `org` / `product`           |
| `access_mode`     | string  | `public` / `authenticated` / `permissioned` |
| `lifecycle_state` | string  | `planned` / `active` / `deprecated` / `retired` |
| `env_dev`         | boolean |                                          |
| `env_staging`     | boolean |                                          |
| `env_prod`        | boolean |                                          |

### Response Body

Updated flag object.

### Error Codes

| Status | Condition     |
|--------|---------------|
| 404    | Code not found |
| 422    | Validation error |
