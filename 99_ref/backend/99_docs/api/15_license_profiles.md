# License Profiles API Contract

Base URL: `/api/v1/am/license-profiles`

All endpoints require `Authorization: Bearer <access_token>`.

License profiles define default resource limits and feature entitlements per tier. Each profile belongs to a tier (free, pro, enterprise, etc.) and multiple profiles can exist per tier (e.g. "Pro Startup", "Pro Enterprise"). Organizations are assigned a profile and inherit its defaults, but can have custom overrides.

**Resolution order:** Org custom override > Profile default > No limit (if unset)

---

## GET /

List all license profiles with their settings and org counts.

**Status Code:** `200 OK`
**Permission:** `feature_flag_registry.view`

### Response Body

| Field | Type | Description |
|-------|------|-------------|
| `profiles` | array | List of profile objects |

**Profile object:**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | UUID |
| `code` | string | Unique code (snake_case) |
| `name` | string | Display name |
| `description` | string | Description |
| `tier` | string | License tier: `free`, `pro`, `pro_trial`, `enterprise`, `partner`, `internal` |
| `is_active` | boolean | Whether this profile can be assigned to new orgs |
| `sort_order` | integer | Display order |
| `settings` | array | Key-value setting objects (limits and entitlements) |
| `org_count` | integer | Number of orgs currently assigned to this profile |
| `created_at` | string | ISO timestamp |
| `updated_at` | string | ISO timestamp |

**Setting object:**

| Field | Type |
|-------|------|
| `key` | string |
| `value` | string |

### Example

```bash
GET /api/v1/am/license-profiles
Authorization: Bearer eyJhbGciOi...
```

```json
{
  "profiles": [
    {
      "id": "uuid-1",
      "code": "free_default",
      "name": "Free",
      "description": "Default free tier profile with basic limits.",
      "tier": "free",
      "is_active": true,
      "sort_order": 10,
      "settings": [
        { "key": "max_users", "value": "5" },
        { "key": "max_workspaces", "value": "2" },
        { "key": "max_frameworks", "value": "1" }
      ],
      "org_count": 42,
      "created_at": "2026-03-15T00:00:00Z",
      "updated_at": "2026-03-15T00:00:00Z"
    }
  ]
}
```

---

## POST /

Create a new license profile.

**Status Code:** `201 Created`
**Permission:** `feature_flag_registry.create`

### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `code` | string | yes | 2-50 chars, pattern `^[a-z0-9_]+$` |
| `name` | string | yes | 2-120 chars |
| `description` | string | no | Max 500 chars |
| `tier` | string | no | Default `"free"`. Values: `free`, `pro`, `pro_trial`, `enterprise`, `partner`, `internal` |
| `sort_order` | integer | no | Default 100, min 0 |

### Response Body

Profile object (without settings or org_count).

### Error Codes

| Status | Condition |
|--------|-----------|
| 409 | Code already exists |
| 422 | Validation error |

---

## PATCH /{code}

Update a license profile.

**Status Code:** `200 OK`
**Permission:** `feature_flag_registry.update`

### Request Body

All fields optional. Only provided fields are updated.

| Field | Type | Constraints |
|-------|------|-------------|
| `name` | string | 2-120 chars |
| `description` | string | Max 500 chars |
| `tier` | string | `free`, `pro`, `pro_trial`, `enterprise`, `partner`, `internal` |
| `is_active` | boolean | |
| `sort_order` | integer | Min 0 |

### Error Codes

| Status | Condition |
|--------|-----------|
| 404 | Profile not found |

---

## PUT /{code}/settings/{key}

Set or update a single profile setting.

**Status Code:** `200 OK`
**Permission:** `feature_flag_registry.update`

### Request Body

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `value` | string | yes | 1-2000 chars |

### Response Body

| Field | Type |
|-------|------|
| `key` | string |
| `value` | string |

### Common Setting Keys

| Key | Type | Description |
|-----|------|-------------|
| `max_users` | integer | Maximum users per org |
| `max_workspaces` | integer | Maximum workspaces per org |
| `max_frameworks` | integer | Maximum compliance frameworks per org |

Setting keys are free-form strings. Add any key you need for future limits.

---

## DELETE /{code}/settings/{key}

Remove a setting from a profile.

**Status Code:** `204 No Content`
**Permission:** `feature_flag_registry.update`

### Error Codes

| Status | Condition |
|--------|-----------|
| 404 | Profile or setting not found |

---

## Assigning Profiles to Organizations

Profiles are assigned to orgs via the Entity Settings API:

```bash
PUT /api/v1/am/settings/org/{org_id}/license_profile
Content-Type: application/json

{ "value": "pro_default" }
```

This sets the org's `license_profile` setting. The org inherits the profile's defaults for any settings it doesn't override.

To also set the tier (which should match the profile's tier):

```bash
PUT /api/v1/am/settings/org/{org_id}/license_tier
Content-Type: application/json

{ "value": "pro" }
```

The frontend admin UI handles both operations automatically when assigning a profile.

---

## Seeded Profiles

The migration seeds 6 default profiles:

| Code | Name | Tier | Default Limits |
|------|------|------|----------------|
| `free_default` | Free | free | 5 users, 2 workspaces, 1 framework |
| `pro_default` | Pro | pro | 50 users, 20 workspaces, 10 frameworks |
| `pro_trial_default` | Pro Trial | pro_trial | (inherit from pro, set expiry per org) |
| `enterprise_default` | Enterprise | enterprise | (custom per org) |
| `partner_default` | Partner | partner | (custom per org) |
| `internal_default` | Internal | internal | No limits |
