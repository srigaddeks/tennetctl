# EAV (Entity-Attribute-Value) Architecture

Last updated: 2026-03-14

## Design Philosophy

kcontrol uses an **Entity-Attribute-Value (EAV)** pattern for extensible properties on core entities. The goal: adding new attributes to users, orgs, workspaces, or any entity should **never require API code changes or schema migrations**. The only change needed is an INSERT into the relevant dimension table.

This matters because:

- Frontend teams can request new fields without waiting for backend deployments
- Different tenants can collect different data without schema-per-tenant complexity
- Signup flows, onboarding wizards, and admin forms can be reconfigured by changing dimension data alone
- New requirements (e.g. "we now need phone number and company name") are a single SQL INSERT, not a feature branch

## The Three-Layer Pattern

Every extensible entity follows a three-layer structure:

```
┌──────────────────────────────┐
│  1. FACT TABLE               │  Core identity — columns used in JOINs, FKs, constraints
│     (e.g. 03_fct_users)     │  Fields: id, tenant_key, account_status, is_deleted...
└──────────────┬───────────────┘
               │ 1:N
┌──────────────▼───────────────┐
│  2. DETAIL TABLE (EAV)       │  Extensible key-value properties
│     (e.g. 05_dtl_user_props) │  Fields: entity_id, property_key (VARCHAR), property_value (TEXT)
│                              │  Unique constraint on (entity_id, property_key)
└──────────────┬───────────────┘
               │ FK on property_key
┌──────────────▼───────────────┐
│  3. DIMENSION TABLE          │  Controls which keys are valid
│     (e.g. 04_dim_user_keys)  │  Fields: code, name, description, data_type, is_pii, sort_order...
│                              │  Adding a row here = adding a new attribute
└──────────────────────────────┘
```

### Why TEXT for values?

All property values are stored as `TEXT`. This is intentional:

- Avoids needing separate columns or tables per data type
- The dimension table declares the `data_type` (string, email, boolean, url, phone, etc.) for frontend validation and display hints
- Backend validates via the dimension table metadata, not column types
- Frontend renders form fields based on `data_type` from the dimension table

### Why a dimension table?

Without a dimension table, any arbitrary key can be inserted — leading to typos (`emial` vs `email`), inconsistent naming, and no way for the frontend to discover available fields. The dimension table:

- Acts as a whitelist of valid property keys
- Provides metadata (display name, description, data type, PII flag, sort order) for frontend form generation
- Enables the frontend to dynamically render forms by querying the dimension table
- FK constraint on the detail table prevents invalid keys from being written

---

## Current Implementation Status

### Fully Implemented (EAV + dimension table + API)

| Entity | Fact Table | Detail Table | Dimension Table | API Endpoints |
|--------|-----------|-------------|-----------------|---------------|
| **Users** | `03_fct_users` | `05_dtl_user_properties` | `04_dim_user_property_keys` | `GET/PUT/DELETE /me/properties/{key}` |
| **User Accounts** | `08_dtl_user_accounts` | `09_dtl_user_account_properties` | `07_dim_account_property_keys` | `GET /me/accounts` (read-only, secrets filtered) |

### EAV Table Exists, Needs Dimension Table + API

| Entity | Fact Table | Detail Table | Dimension Table | API Endpoints |
|--------|-----------|-------------|-----------------|---------------|
| **Orgs** | `29_fct_orgs` | `30_dtl_org_settings` | needs creation | needs creation |
| **Workspaces** | `34_fct_workspaces` | `35_dtl_workspace_settings` | needs creation | needs creation |
| **Products** | `24_fct_products` | `25_dtl_product_settings` | needs creation | needs creation |

### No EAV Table Yet (fixed columns only)

| Entity | Fact Table | Detail Table | Dimension Table |
|--------|-----------|-------------|-----------------|
| **Feature Flags** | `14_dim_feature_flags` | needs creation | needs creation |
| **Roles** | `16_fct_roles` | needs creation | needs creation |
| **User Groups** | `17_fct_user_groups` | needs creation | needs creation |

---

## What Goes in Columns vs EAV

Not everything belongs in EAV. The rule:

| In Columns (fact table) | In EAV (detail table) |
|------------------------|----------------------|
| Used in JOINs or FKs | Display/metadata only |
| Used in WHERE clauses for core queries | Queried by specific key lookup |
| Part of identity or structural integrity | Varies per use case or tenant |
| Small fixed set that rarely changes | Grows as requirements evolve |
| Boolean flags (`is_active`, `is_deleted`) | Custom attributes |

**Examples:**

| Entity | Columns (structural) | EAV (extensible) |
|--------|---------------------|------------------|
| User | `id`, `tenant_key`, `account_status` | email, username, display_name, phone, bio, timezone, locale, avatar_url |
| Org | `id`, `name`, `org_type_code`, `tenant_key` | logo_url, industry, website, address, tax_id |
| Workspace | `id`, `name`, `workspace_type_code`, `org_id` | color, icon, description, max_members |
| Role | `id`, `code`, `name`, `role_level_code` | color, icon, priority, description_long |
| Feature Flag | `id`, `code`, `name`, `access_mode`, `lifecycle_state` | rollout_percentage, sunset_date, owner_team |

---

## User Properties — Reference Implementation

This is the working pattern that all other entities should follow.

### Database Tables

```sql
-- Dimension table: controls valid property keys
CREATE TABLE "03_auth_manage"."04_dim_user_property_keys" (
    id          UUID PRIMARY KEY,
    code        VARCHAR(80) NOT NULL UNIQUE,       -- 'email', 'display_name', 'phone', etc.
    name        VARCHAR(120) NOT NULL,              -- 'Email Address'
    description TEXT NOT NULL,                      -- 'Primary email identifier'
    data_type   VARCHAR(30) NOT NULL DEFAULT 'string', -- string, email, boolean, url, phone
    is_pii      BOOLEAN NOT NULL DEFAULT FALSE,     -- GDPR/privacy flag
    is_required BOOLEAN NOT NULL DEFAULT FALSE,     -- required during onboarding?
    sort_order  INTEGER NOT NULL,                   -- controls form field ordering
    created_at  TIMESTAMP NOT NULL,
    updated_at  TIMESTAMP NOT NULL
);

-- Detail table: stores actual property values
CREATE TABLE "03_auth_manage"."05_dtl_user_properties" (
    id             UUID PRIMARY KEY,
    user_id        UUID NOT NULL REFERENCES "03_auth_manage"."03_fct_users" (id),
    property_key   VARCHAR(80) NOT NULL REFERENCES "04_dim_user_property_keys" (code),
    property_value TEXT NOT NULL,
    created_at     TIMESTAMP NOT NULL,
    updated_at     TIMESTAMP NOT NULL,
    UNIQUE (user_id, property_key)  -- one value per user per key
);
```

### Currently Seeded Property Keys

| Code | Name | Data Type | PII | Required | Sort |
|------|------|-----------|-----|----------|------|
| `email` | Email Address | email | yes | yes | 10 |
| `username` | Username | string | no | no | 20 |
| `display_name` | Display Name | string | no | no | 30 |
| `email_verified` | Email Verified | boolean | no | no | 40 |
| `timezone` | Timezone | string | no | no | 50 |
| `locale` | Locale | string | no | no | 60 |
| `avatar_url` | Avatar URL | url | no | no | 70 |
| `phone` | Phone Number | phone | yes | no | 80 |
| `bio` | Biography | string | no | no | 90 |

### Adding a New User Property

To add `company_name` as a user property — **no API or schema changes needed**:

```sql
INSERT INTO "03_auth_manage"."04_dim_user_property_keys"
    (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'company_name', 'Company Name', 'User company or organization name',
     'string', FALSE, FALSE, 100, NOW(), NOW());
```

Frontend immediately calls:
```bash
PUT /api/v1/auth/local/me/properties/company_name
Content-Type: application/json
Authorization: Bearer <token>

{ "value": "Kreesalis" }
```

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/auth/local/me/properties` | List all properties for current user |
| `PUT` | `/auth/local/me/properties/{key}` | Set or update a single property |
| `DELETE` | `/auth/local/me/properties/{key}` | Remove a property |

**Set property request:** `{ "value": "some text" }` — value is always a string (1-2000 chars).

**Set property response:** `{ "key": "company_name", "value": "Kreesalis" }`.

**List properties response:**
```json
{
  "properties": [
    { "key": "email", "value": "sri@kreesalis.com" },
    { "key": "display_name", "value": "Sri" },
    { "key": "company_name", "value": "Kreesalis" }
  ]
}
```

### Service Layer Behavior

- **Validation**: Property key is checked against `04_dim_user_property_keys`. Unknown keys return `404`.
- **Upsert**: Uses `INSERT ... ON CONFLICT (user_id, property_key) DO UPDATE` — idempotent.
- **Audit**: Every set/delete writes to `40_aud_events` with `property_changed` or `property_removed` event type, including `previous_value` and `new_value` in audit properties.
- **Cache**: Invalidates `user:{id}:profile` and `user:{id}:properties` cache keys after mutation.
- **Impersonation guard**: `email` and `username` cannot be modified during impersonation.

---

## Typical Frontend Signup Flow

Using the EAV pattern, a multi-step signup requires zero backend changes:

```
Step 1: Registration
    POST /auth/local/register
    Body: { "email": "user@example.com", "password": "SecurePass123!" }
    Response: { "user_id": "...", "email": "user@example.com", ... }
    → User gets access_token

Step 2: Collect profile details (frontend decides which fields to show)
    PUT /auth/local/me/properties/display_name   → { "value": "Sri K" }
    PUT /auth/local/me/properties/company_name   → { "value": "Kreesalis" }
    PUT /auth/local/me/properties/timezone       → { "value": "Asia/Kolkata" }
    PUT /auth/local/me/properties/phone          → { "value": "+91-9876543210" }

Step 3: Complete onboarding (optional)
    PUT /auth/local/me/properties/bio            → { "value": "Platform engineer" }
    PUT /auth/local/me/properties/avatar_url     → { "value": "https://..." }
```

Each step is a simple `PUT` with `{ "value": "..." }`. The frontend can be reconfigured to show different fields per step without any backend changes.

### Future: Batch Property Endpoint

Currently properties are set one at a time. A planned batch endpoint will allow setting multiple properties in a single request:

```
PUT /auth/local/me/properties
{
  "properties": {
    "display_name": "Sri K",
    "timezone": "Asia/Kolkata",
    "company_name": "Kreesalis"
  }
}
```

This will validate all keys upfront, run all UPSERTs in a single transaction, and invalidate cache once.

---

## Extending the Pattern to Other Entities

### For Orgs (example)

The `30_dtl_org_settings` detail table already exists. To complete the pattern:

**1. Create dimension table:**
```sql
CREATE TABLE "03_auth_manage"."31_dim_org_setting_keys" (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code        VARCHAR(100) NOT NULL UNIQUE,
    name        VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    data_type   VARCHAR(30) NOT NULL DEFAULT 'string',
    is_pii      BOOLEAN NOT NULL DEFAULT FALSE,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL,
    updated_at  TIMESTAMP NOT NULL
);

-- Add FK constraint to existing settings table
ALTER TABLE "03_auth_manage"."30_dtl_org_settings"
    ADD CONSTRAINT fk_30_dtl_org_settings_key
        FOREIGN KEY (setting_key)
        REFERENCES "03_auth_manage"."31_dim_org_setting_keys" (code)
        ON DELETE RESTRICT;
```

**2. Seed initial keys:**
```sql
INSERT INTO "03_auth_manage"."31_dim_org_setting_keys"
    (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'logo_url', 'Logo URL', 'Organization logo image', 'url', FALSE, FALSE, 10, NOW(), NOW()),
    (gen_random_uuid(), 'website', 'Website', 'Organization website', 'url', FALSE, FALSE, 20, NOW(), NOW()),
    (gen_random_uuid(), 'industry', 'Industry', 'Industry sector', 'string', FALSE, FALSE, 30, NOW(), NOW()),
    (gen_random_uuid(), 'address', 'Address', 'Primary address', 'string', TRUE, FALSE, 40, NOW(), NOW());
```

**3. API endpoints (same pattern as user properties):**

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/am/orgs/{org_id}/settings` | List all settings |
| `PUT` | `/am/orgs/{org_id}/settings/{key}` | Set or update a setting |
| `PUT` | `/am/orgs/{org_id}/settings` | Batch set (future) |
| `DELETE` | `/am/orgs/{org_id}/settings/{key}` | Remove a setting |

The same pattern applies identically to workspaces, products, roles, user groups, and feature flags — only the entity ID column and table names change.

---

## Audit Event Properties

The audit system (`40_aud_events` + `41_dtl_audit_event_properties`) uses a similar but unconstrained EAV pattern:

- **No dimension table** — audit properties are flexible key-value pairs with no whitelist
- Uses `meta_key` / `meta_value` (both TEXT) instead of `property_key` / `property_value`
- This is intentional: audit properties capture context that varies per event type and should never be rejected

This is the one place where the EAV pattern deliberately skips the dimension table constraint because audit data must never fail to write due to an unknown key.

---

## Consistent API Pattern Across All Entities

Once fully implemented, every entity follows the same API shape:

| Entity | List Settings | Set Single | Set Batch | Delete |
|--------|--------------|------------|-----------|--------|
| Users | `GET /me/properties` | `PUT /me/properties/{key}` | `PUT /me/properties` | `DELETE /me/properties/{key}` |
| Orgs | `GET /am/orgs/{id}/settings` | `PUT /am/orgs/{id}/settings/{key}` | `PUT /am/orgs/{id}/settings` | `DELETE /am/orgs/{id}/settings/{key}` |
| Workspaces | `GET .../workspaces/{id}/settings` | `PUT .../settings/{key}` | `PUT .../settings` | `DELETE .../settings/{key}` |
| Products | `GET /am/products/{id}/settings` | `PUT .../settings/{key}` | `PUT .../settings` | `DELETE .../settings/{key}` |
| Roles | `GET /am/roles/{id}/settings` | `PUT .../settings/{key}` | `PUT .../settings` | `DELETE .../settings/{key}` |
| Groups | `GET /am/groups/{id}/settings` | `PUT .../settings/{key}` | `PUT .../settings` | `DELETE .../settings/{key}` |
| Feature Flags | `GET /am/features/{code}/settings` | `PUT .../settings/{key}` | `PUT .../settings` | `DELETE .../settings/{key}` |

**Request body is always the same:** `{ "value": "..." }` for single, `{ "properties": { "key": "value", ... } }` for batch.

**Adding a new attribute to any entity is always the same:** INSERT a row into the dimension table.

---

## Frontend Integration Guide

### Discovering Available Properties

The frontend can query dimension tables to dynamically build forms:

```
GET /am/property-keys/user       → returns 04_dim_user_property_keys rows
GET /am/property-keys/org        → returns 31_dim_org_setting_keys rows (future)
GET /am/property-keys/workspace  → returns dimension rows (future)
```

Each key includes metadata for rendering:

```json
{
  "keys": [
    {
      "code": "display_name",
      "name": "Display Name",
      "description": "User display name",
      "data_type": "string",
      "is_pii": false,
      "is_required": false,
      "sort_order": 30
    },
    {
      "code": "phone",
      "name": "Phone Number",
      "description": "Contact phone number",
      "data_type": "phone",
      "is_pii": true,
      "is_required": false,
      "sort_order": 80
    }
  ]
}
```

The frontend uses `data_type` to pick the right input component, `is_required` for validation, `sort_order` for field ordering, and `is_pii` for masking/privacy indicators.

### Adding a New Field Workflow

1. **Product/PM decides** a new field is needed (e.g. `job_title` for users)
2. **One SQL INSERT** into the dimension table (via migration or admin API)
3. **Frontend automatically** picks up the new field from the property-keys endpoint
4. **Users can set it** via `PUT /me/properties/job_title`
5. **No backend deployment, no API change, no schema migration**
