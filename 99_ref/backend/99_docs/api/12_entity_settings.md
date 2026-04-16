# Entity Settings API Contract

Entity settings follow a universal EAV pattern. A single set of 5 generic endpoints at `/api/v1/am/settings/{entity_type}/{entity_id}` serves all entity types: organizations, workspaces, roles, user groups, feature flags, and products.

---

## Supported Entity Types

| `entity_type` | Fact Table | Detail Table | Dimension Table | Permission Prefix |
|----------------|-----------|--------------|-----------------|-------------------|
| `org` | `29_fct_orgs` | `30_dtl_org_settings` | `31_dim_org_setting_keys` | `org_management` |
| `workspace` | `34_fct_workspaces` | `35_dtl_workspace_settings` | `36_dim_workspace_setting_keys` | `workspace_management` |
| `role` | `16_fct_roles` | `22_dtl_role_settings` | `22_dim_role_setting_keys` | `group_access_assignment` |
| `group` | `17_fct_user_groups` | `27_dtl_group_settings` | `27_dim_group_setting_keys` | `group_access_assignment` |
| `feature` | `14_dim_feature_flags` | `21_dtl_feature_flag_settings` | `21_dim_feature_flag_setting_keys` | `feature_flag_registry` |
| `product` | `24_fct_products` | `25_dtl_product_settings` | `26_dim_product_setting_keys` | `product_management` |

**Note:** For `feature`, the `entity_id` path parameter is the feature flag `code` (string), not a UUID. The API resolves it to a UUID internally.

---

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/am/settings/{entity_type}/{entity_id}` | List all settings for the entity |
| GET | `/api/v1/am/settings/{entity_type}/{entity_id}/keys` | List available setting keys |
| PUT | `/api/v1/am/settings/{entity_type}/{entity_id}/{key}` | Set or update a single setting |
| PUT | `/api/v1/am/settings/{entity_type}/{entity_id}` | Batch set multiple settings |
| DELETE | `/api/v1/am/settings/{entity_type}/{entity_id}/{key}` | Delete a single setting |

---

## GET /{entity_type}/{entity_id}

List all settings for an entity.

**Status Code:** `200 OK`
**Permission:** `{prefix}.view`

### Response Body

| Field | Type | Description |
|-------|------|-------------|
| `settings` | array | List of key-value setting objects |

**Setting object:**

| Field | Type |
|-------|------|
| `key` | string |
| `value` | string |

### Example

```bash
GET /api/v1/am/settings/org/uuid-org-1
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "settings": [
    { "key": "default_timezone", "value": "America/New_York" },
    { "key": "max_workspaces", "value": "10" },
    { "key": "billing_email", "value": "billing@example.com" }
  ]
}
```

---

## GET /{entity_type}/{entity_id}/keys

List all available setting keys for the entity type. Useful for building forms and validation on the client side.

**Status Code:** `200 OK`
**Permission:** `{prefix}.view`

### Response Body

| Field | Type | Description |
|-------|------|-------------|
| `keys` | array | List of setting key definitions |

**Setting key object:**

| Field | Type |
|-------|------|
| `code` | string |
| `name` | string |
| `description` | string? |
| `data_type` | string |
| `is_pii` | boolean |
| `is_required` | boolean |
| `sort_order` | integer |

### Example

```bash
GET /api/v1/am/settings/org/uuid-org-1/keys
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "keys": [
    {
      "code": "default_timezone",
      "name": "Default Timezone",
      "description": "Default timezone for the organization",
      "data_type": "text",
      "is_pii": false,
      "is_required": false,
      "sort_order": 1
    }
  ]
}
```

---

## PUT /{entity_type}/{entity_id}/{key}

Set or update a single setting.

**Status Code:** `200 OK`
**Permission:** `{prefix}.update`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `key` | string | Setting key code |

### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `value` | string | yes | 1-2000 chars |

### Response Body

| Field | Type |
|-------|------|
| `key` | string |
| `value` | string |

### Example

```bash
PUT /api/v1/am/settings/org/uuid-org-1/default_timezone
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "value": "Europe/London"
}
```

```json
// 200 OK
{
  "key": "default_timezone",
  "value": "Europe/London"
}
```

### Error Codes

| Status | Condition |
|--------|-----------|
| 400 | Invalid setting key |
| 401 | Missing/invalid token |
| 404 | Entity not found |

---

## PUT /{entity_type}/{entity_id} (batch)

Set multiple settings in a single transaction. All keys are validated upfront.

**Status Code:** `200 OK`
**Permission:** `{prefix}.update`

### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `settings` | object | yes | Key-value map of settings |

### Response Body

| Field | Type | Description |
|-------|------|-------------|
| `settings` | array | List of key-value setting objects |

### Example

```bash
PUT /api/v1/am/settings/org/uuid-org-1
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "settings": {
    "default_timezone": "Europe/London",
    "max_workspaces": "25"
  }
}
```

```json
// 200 OK
{
  "settings": [
    { "key": "default_timezone", "value": "Europe/London" },
    { "key": "max_workspaces", "value": "25" }
  ]
}
```

### Error Codes

| Status | Condition |
|--------|-----------|
| 400 | One or more invalid setting keys |
| 401 | Missing/invalid token |
| 404 | Entity not found |
| 422 | Validation error (empty values, etc.) |

---

## DELETE /{entity_type}/{entity_id}/{key}

Remove a setting from an entity.

**Status Code:** `204 No Content`
**Permission:** `{prefix}.update`

### Path Parameters

| Param | Type | Description |
|-------|------|-------------|
| `key` | string | Setting key code |

### Example

```bash
DELETE /api/v1/am/settings/org/uuid-org-1/billing_email
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Error Codes

| Status | Condition |
|--------|-----------|
| 401 | Missing/invalid token |
| 404 | Setting not found |

---

## Adding New Setting Keys

To add a new setting key for any entity type, insert a row into the corresponding dimension table. No schema changes or code changes are needed.

```sql
-- Example: add a new org setting key
INSERT INTO "03_auth_manage"."31_dim_org_setting_keys"
  (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
  (gen_random_uuid(), 'support_email', 'Support Email', 'Organization support contact',
   'string', FALSE, FALSE, 50, NOW(), NOW());
```

The new key becomes immediately available for `GET`, `PUT`, and `DELETE` operations on the settings endpoints.

---

## Cross-Service Cache Invalidation

When entity settings change for certain entity types, related caches in other services are also invalidated:

| Entity Type | Additional Cache Invalidated | Why |
|---|---|---|
| `feature` | `features:list` | Feature flag list includes `org_visibility` and `required_license` from settings |

This is configured in `_CROSS_CACHE_INVALIDATION` in `12_entity_settings/service.py`.

---

## Notable Setting Keys

### Org Setting Keys

| Key | Data Type | Description |
|---|---|---|
| `license_tier` | string | License tier: `free`, `pro`, `pro_trial`, `enterprise`, `partner`, `internal` |
| `license_profile` | string | Code of assigned license profile (determines tier + default limits) |
| `license_expires_at` | string | ISO 8601 date for pro_trial expiry |
| `max_users` | integer | Max users allowed in org |
| `max_workspaces` | integer | Max workspaces allowed in org |
| `max_frameworks` | integer | Max compliance frameworks allowed |
| `enabled_features` | json | JSON array of enabled feature flag codes (org-scoped flags only) |

### Feature Flag Setting Keys

| Key | Data Type | Description |
|---|---|---|
| `org_visibility` | string | `hidden` / `locked` / `unlocked` — controls org admin access to this flag |
| `required_license` | string | Minimum tier required: `free`, `pro`, `enterprise`, `internal` |
| `rollout_percentage` | integer | Percentage of users who see this flag |
| `sunset_date` | string | Planned removal date (ISO 8601) |
| `owner_team` | string | Team responsible for this flag |
| `jira_ticket` | string | Linked issue tracker ticket |
| `notes` | string | Internal notes |
