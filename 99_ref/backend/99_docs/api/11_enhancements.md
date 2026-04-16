# Auth Enhancements API Contract

Base URL: `/api/v1/auth/local`

These endpoints extend the core auth module with batch property updates, property key discovery, password changes, and email verification.

---

## PUT /me/properties (batch)

Set multiple user properties in a single request. All keys are validated upfront and changes are applied in a single transaction.

**Status Code:** `200 OK`
**Requires:** `Authorization: Bearer <access_token>`

### Request Body

| Field        | Type   | Required | Description                                |
|--------------|--------|----------|--------------------------------------------|
| `properties` | object | yes      | Key-value map of properties to set         |

Each key must be a valid property key defined in `04_dim_user_property_keys`. Values are strings (1-2000 chars).

### Response Body

| Field        | Type  | Description                       |
|--------------|-------|-----------------------------------|
| `properties` | array | List of key-value property objects |

**Property object:**

| Field   | Type   |
|---------|--------|
| `key`   | string |
| `value` | string |

### Example

```bash
PUT /api/v1/auth/local/me/properties
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "properties": {
    "display_name": "Jane Doe",
    "timezone": "America/New_York",
    "locale": "en-US"
  }
}
```

```json
// 200 OK
{
  "properties": [
    { "key": "display_name", "value": "Jane Doe" },
    { "key": "timezone", "value": "America/New_York" },
    { "key": "locale", "value": "en-US" }
  ]
}
```

### Error Codes

| Status | Condition                                         |
|--------|---------------------------------------------------|
| 400    | One or more invalid property keys                 |
| 401    | Missing/invalid token                             |
| 422    | Validation error (empty values, etc.)             |

---

## GET /me/property-keys

List all available user property keys with metadata. **Public endpoint -- no auth required.**

**Status Code:** `200 OK`

### Response Body

| Field  | Type  | Description                           |
|--------|-------|---------------------------------------|
| `keys` | array | List of property key definition objects |

**Property key object:**

| Field         | Type    | Description                                      |
|---------------|---------|--------------------------------------------------|
| `code`        | string  | Property key code (e.g., `email`, `timezone`)    |
| `name`        | string  | Human-readable name                              |
| `description` | string? | Description of the property                      |
| `data_type`   | string  | Expected data type (e.g., `text`, `boolean`)     |
| `is_pii`      | boolean | Whether the property contains personal data      |
| `is_required` | boolean | Whether the property is required at registration |
| `sort_order`  | integer | Display ordering hint                            |

### Example

```bash
GET /api/v1/auth/local/me/property-keys
```

```json
// 200 OK — no auth required
{
  "keys": [
    {
      "code": "email",
      "name": "Email Address",
      "description": "Primary email address",
      "data_type": "text",
      "is_pii": true,
      "is_required": true,
      "sort_order": 1
    },
    {
      "code": "username",
      "name": "Username",
      "description": "Unique username for login",
      "data_type": "text",
      "is_pii": false,
      "is_required": false,
      "sort_order": 2
    },
    {
      "code": "timezone",
      "name": "Timezone",
      "description": "User timezone (IANA format)",
      "data_type": "text",
      "is_pii": false,
      "is_required": false,
      "sort_order": 5
    }
  ]
}
```

---

## PUT /me/password

Change the password for the currently authenticated user. Requires the current password for verification.

**Status Code:** `200 OK`
**Requires:** `Authorization: Bearer <access_token>`

### Request Body

| Field              | Type   | Required | Constraints  |
|--------------------|--------|----------|--------------|
| `current_password` | string | yes      | 12-256 chars |
| `new_password`     | string | yes      | 12-256 chars |

### Response Body

| Field     | Type   |
|-----------|--------|
| `message` | string |

### Example

```bash
PUT /api/v1/auth/local/me/password
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "current_password": "OldSecurePassword123!",
  "new_password": "NewSecurePassword456!"
}
```

```json
// 200 OK
{
  "message": "Password changed successfully."
}
```

### Error Codes

| Status | Condition                                     |
|--------|-----------------------------------------------|
| 401    | Missing/invalid token or wrong current password |
| 403    | Blocked during impersonation                  |
| 422    | Validation error                              |

### Restrictions

- **Blocked during impersonation.** An impersonating admin cannot change the target user's password. Returns `403 Forbidden`.

---

## POST /me/verify-email/request

Request an email verification challenge for the authenticated user. Generates a verification token and (in production) sends it via email.

**Status Code:** `200 OK`
**Requires:** `Authorization: Bearer <access_token>`

### Response Body

| Field                | Type    | Description                              |
|----------------------|---------|------------------------------------------|
| `message`            | string  | Confirmation message                     |
| `verification_token` | string? | Verification token (dev mode only)       |

### Example

```bash
POST /api/v1/auth/local/me/verify-email/request
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "message": "Verification email sent.",
  "verification_token": "eyJhbGciOi..."
}
```

> **Note:** `verification_token` is only returned in dev mode. In production, the token is delivered via email.

### Error Codes

| Status | Condition                      |
|--------|--------------------------------|
| 401    | Missing/invalid token          |
| 409    | Email already verified         |

---

## POST /me/verify-email

Verify the user's email address using a verification token. **Public endpoint -- no auth required** (user clicks link from email).

**Status Code:** `200 OK`

### Request Body

| Field                | Type   | Required | Constraints  |
|----------------------|--------|----------|--------------|
| `verification_token` | string | yes      | 10-512 chars |

### Response Body

| Field     | Type   |
|-----------|--------|
| `message` | string |

### Example

```bash
POST /api/v1/auth/local/me/verify-email
Content-Type: application/json

{
  "verification_token": "eyJhbGciOi..."
}
```

```json
// 200 OK
{
  "message": "Email verified successfully."
}
```

### Error Codes

| Status | Condition                    |
|--------|------------------------------|
| 401    | Invalid or expired token     |
| 409    | Email already verified       |
| 422    | Validation error             |
