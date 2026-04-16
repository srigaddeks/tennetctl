# Auth API Contract

Base URL: `/api/v1/auth/local`

All auth endpoints are **public** (no Bearer token required) except `/me`, `/logout`, and `/me/*` endpoints.

---

## POST /register

Register a new user with email and password.

**Status Code:** `201 Created`

### Request Body

| Field      | Type   | Required | Constraints                          |
|------------|--------|----------|--------------------------------------|
| `email`    | string | yes      | 5–320 chars, must contain `@`, normalized to lowercase |
| `password` | string | yes      | 12–256 chars                         |
| `username` | string | no       | 3–32 chars, pattern `^[a-z0-9_.-]+$`, no `@`, lowercase |

### Response Body

| Field            | Type    | Description                 |
|------------------|---------|-----------------------------|
| `user_id`        | string  | UUID of the created user    |
| `email`          | string  | Normalized email            |
| `username`       | string? | Username if provided        |
| `tenant_key`     | string  | Tenant identifier           |
| `email_verified` | boolean | Always `false` on register  |

### Example

```bash
POST /api/v1/auth/local/register
Content-Type: application/json

{
  "email": "jane.doe@example.com",
  "password": "RobotPass123!"
}
```

```json
// 201 Created
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "email": "jane.doe@example.com",
  "username": null,
  "tenant_key": "default",
  "email_verified": false
}
```

### Error Codes

| Status | Condition                       |
|--------|---------------------------------|
| 409    | Email or username already taken |
| 422    | Validation error                |

---

## POST /login

Authenticate and receive access + refresh tokens.

**Status Code:** `200 OK`

### Request Body

| Field      | Type   | Required | Constraints  |
|------------|--------|----------|--------------|
| `login`    | string | yes      | 3–320 chars (email or username) |
| `password` | string | yes      | 12–256 chars |

### Response Body

| Field                | Type    | Description                     |
|----------------------|---------|---------------------------------|
| `access_token`       | string  | JWT access token                |
| `token_type`         | string  | `"Bearer"`                      |
| `expires_in`         | integer | Access token TTL in seconds     |
| `refresh_token`      | string  | JWT refresh token               |
| `refresh_expires_in` | integer | Refresh token TTL in seconds    |
| `user`               | object? | AuthUserResponse (see below)    |

**AuthUserResponse:**

| Field            | Type    |
|------------------|---------|
| `user_id`        | string  |
| `tenant_key`     | string  |
| `email`          | string  |
| `username`       | string? |
| `email_verified` | boolean |
| `account_status` | string  |

### Example

```bash
POST /api/v1/auth/local/login
Content-Type: application/json

{
  "login": "jane.doe@example.com",
  "password": "RobotPass123!"
}
```

```json
// 200 OK
{
  "access_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6IjEifQ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "refresh_expires_in": 604800,
  "user": {
    "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "tenant_key": "default",
    "email": "jane.doe@example.com",
    "username": null,
    "email_verified": false,
    "account_status": "active"
  }
}
```

### Error Codes

| Status | Condition                        |
|--------|----------------------------------|
| 401    | Invalid credentials              |
| 403    | Account locked or disabled       |
| 422    | Validation error                 |

---

## POST /refresh

Exchange a refresh token for a new token pair. Implements rotation — the old refresh token is invalidated.

**Status Code:** `200 OK`

### Request Body

| Field           | Type   | Required | Constraints    |
|-----------------|--------|----------|----------------|
| `refresh_token` | string | yes      | 10–512 chars   |

### Response Body

Same as `/login` response (`TokenPairResponse`).

### Example

```bash
POST /api/v1/auth/local/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."
}
```

```json
// 200 OK — new token pair (old refresh token is invalidated)
{
  "access_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6IjEifQ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9...",
  "refresh_expires_in": 604800,
  "user": { ... }
}
```

### Error Codes

| Status | Condition                                  |
|--------|--------------------------------------------|
| 401    | Token expired, revoked, or reuse detected  |

---

## POST /forgot-password

Request a password reset. Always returns success to prevent user enumeration.

**Status Code:** `200 OK`

### Request Body

| Field   | Type   | Required | Constraints  |
|---------|--------|----------|--------------|
| `login` | string | yes      | 3–320 chars  |

### Response Body

| Field         | Type    | Description                        |
|---------------|---------|------------------------------------|
| `message`     | string  | Confirmation message               |
| `reset_token` | string? | Reset token (dev mode only)        |

### Example

```bash
POST /api/v1/auth/local/forgot-password
Content-Type: application/json

{
  "login": "jane.doe@example.com"
}
```

```json
// 200 OK — always returns success (prevents user enumeration)
{
  "message": "If the account exists, a reset link has been sent.",
  "reset_token": "eyJhbGciOi..."
}
```

> **Note:** `reset_token` is only returned in dev mode. In production, the token is sent via email.

---

## POST /reset-password

Reset password using a reset token.

**Status Code:** `200 OK`

### Request Body

| Field          | Type   | Required | Constraints  |
|----------------|--------|----------|--------------|
| `reset_token`  | string | yes      | 10–512 chars |
| `new_password` | string | yes      | 12–256 chars |

### Response Body

| Field     | Type   |
|-----------|--------|
| `message` | string |

### Example

```bash
POST /api/v1/auth/local/reset-password
Content-Type: application/json

{
  "reset_token": "eyJhbGciOi...",
  "new_password": "NewSecurePassword456!"
}
```

```json
// 200 OK
{
  "message": "Password has been reset successfully."
}
```

### Error Codes

| Status | Condition                    |
|--------|------------------------------|
| 401    | Invalid or expired token     |
| 422    | Validation error             |

---

## POST /logout

**Requires:** `Authorization: Bearer <access_token>`

Invalidate the refresh token.

**Status Code:** `200 OK`

### Request Body

| Field           | Type   | Required | Constraints  |
|-----------------|--------|----------|--------------|
| `refresh_token` | string | yes      | 10–512 chars |

### Response Body

| Field     | Type   |
|-----------|--------|
| `message` | string |

### Example

```bash
POST /api/v1/auth/local/logout
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9..."
}
```

```json
// 200 OK
{
  "message": "Logged out successfully."
}
```

---

## GET /me

**Requires:** `Authorization: Bearer <access_token>`

Returns the authenticated user's profile.

**Status Code:** `200 OK`

### Response Body

| Field            | Type    |
|------------------|---------|
| `user_id`        | string  |
| `tenant_key`     | string  |
| `email`          | string  |
| `username`       | string? |
| `email_verified` | boolean |
| `account_status` | string  |

### Example

```bash
GET /api/v1/auth/local/me
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "tenant_key": "default",
  "email": "jane.doe@example.com",
  "username": null,
  "email_verified": false,
  "account_status": "active"
}
```

### Error Codes

| Status | Condition         |
|--------|-------------------|
| 401    | Missing/invalid token |

---

## GET /me/properties

**Requires:** `Authorization: Bearer <access_token>`

List all EAV properties for the authenticated user.

**Status Code:** `200 OK`

### Response Body

```json
{
  "properties": [
    { "key": "email", "value": "user@example.com" },
    { "key": "username", "value": "johndoe" },
    { "key": "email_verified", "value": "false" },
    { "key": "timezone", "value": "America/New_York" }
  ]
}
```

| Field        | Type  | Description                    |
|--------------|-------|--------------------------------|
| `properties` | array | List of key-value property objects |

**Property object:**

| Field   | Type   | Description    |
|---------|--------|----------------|
| `key`   | string | Property key   |
| `value` | string | Property value |

### Example

```bash
GET /api/v1/auth/local/me/properties
Authorization: Bearer eyJhbGciOi...
```

```json
// 200 OK
{
  "properties": [
    { "key": "email", "value": "jane.doe@example.com" },
    { "key": "email_verified", "value": "false" }
  ]
}
```

---

## PUT /me/properties/{key}

**Requires:** `Authorization: Bearer <access_token>`

Set or update a user property. The key must be a valid property key defined in the dimension table (`04_dim_user_property_keys`).

**Status Code:** `200 OK`

### Path Parameters

| Param | Type   | Description              |
|-------|--------|--------------------------|
| `key` | string | Property key to set      |

### Request Body

| Field   | Type   | Required | Constraints    |
|---------|--------|----------|----------------|
| `value` | string | yes      | 1–2000 chars   |

### Response Body

| Field   | Type   |
|---------|--------|
| `key`   | string |
| `value` | string |

### Example

```bash
PUT /api/v1/auth/local/me/properties/timezone
Authorization: Bearer eyJhbGciOi...
Content-Type: application/json

{
  "value": "Asia/Kolkata"
}
```

```json
// 200 OK
{
  "key": "timezone",
  "value": "Asia/Kolkata"
}
```

### Error Codes

| Status | Condition                         |
|--------|-----------------------------------|
| 400    | Invalid property key              |
| 401    | Missing/invalid token             |

---

## DELETE /me/properties/{key}

**Requires:** `Authorization: Bearer <access_token>`

Remove a user property.

**Status Code:** `204 No Content`

### Path Parameters

| Param | Type   | Description              |
|-------|--------|--------------------------|
| `key` | string | Property key to remove   |

### Example

```bash
DELETE /api/v1/auth/local/me/properties/timezone
Authorization: Bearer eyJhbGciOi...
```

```
// 204 No Content (empty body)
```

### Error Codes

| Status | Condition                         |
|--------|-----------------------------------|
| 401    | Missing/invalid token             |
| 404    | Property not found                |

---

## GET /me/accounts

**Requires:** `Authorization: Bearer <access_token>`

List all linked account types for the authenticated user. Secret properties (e.g., `password_hash`) are excluded.

**Status Code:** `200 OK`

### Response Body

```json
{
  "accounts": [
    {
      "account_type": "local_password",
      "is_primary": true,
      "is_active": true,
      "properties": {
        "password_version": "1",
        "password_changed_at": "2026-03-14 01:15:00"
      }
    }
  ]
}
```

| Field      | Type  | Description                    |
|------------|-------|--------------------------------|
| `accounts` | array | List of account objects         |

**Account object:**

| Field          | Type    | Description                                |
|----------------|---------|--------------------------------------------|
| `account_type` | string  | Account type code (e.g., `local_password`) |
| `is_primary`   | boolean | Whether this is the primary account        |
| `is_active`    | boolean | Whether the account is active              |
| `properties`   | object  | Non-secret key-value properties            |
