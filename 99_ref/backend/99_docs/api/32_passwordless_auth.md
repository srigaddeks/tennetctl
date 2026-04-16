# Passwordless Authentication API Contract

Base URL: `/api/v1/auth/passwordless`

All endpoints are **public** (no JWT required) — analogous to `/login`, `/register`, `/forgot-password`.

Passwordless authentication allows users to sign in via a one-time magic link sent to their email. This works for both existing users (as an alternative to password login) and external collaborators who are assigned to tasks but don't have an account in the system.

---

## Concepts

### User Categories

Every user has a `user_category` on the `03_fct_users` table:

| Category | Description | How Created | License Pool |
|----------|-------------|-------------|--------------|
| `full` | Standard users with password, OAuth, or SSO accounts | Registration, admin creation | `max_users` |
| `external_collaborator` | Limited users who authenticate only via magic link | Auto-created on first magic link verify | `max_external_users` |

### Account Type: `magic_link`

New entry in `06_dim_account_types`. When a user authenticates via magic link:

- **Full users:** Get an additional `magic_link` account alongside their existing `local_password` / OAuth accounts
- **External collaborators:** Get `magic_link` as their only (and primary) account

### Challenge Types: `magic_link`, `magic_link_assignee`

Uses the existing `12_trx_auth_challenges` table with `challenge_type_code = 'magic_link'` (main login flow) or `challenge_type_code = 'magic_link_assignee'` (assignee-only portal flow). Token format: `{challenge_id}.{secret}` (same pattern as password reset).

### External Collaborator Access Model

External collaborators have **no org/workspace membership**. Their access is purely task-scoped:

- Can only see tasks they are assigned to (via `31_lnk_task_assignments` or `assignee_user_id`)
- Can upload attachments and add comments on those tasks
- Cannot browse orgs, workspaces, dashboards, or any other platform features
- Permissions enforced at query level in the task repository

### Token TTL

Platform-wide setting: `magic_link_default_ttl_hours` (default: 24 hours, range: 1-168 hours). Configurable by super admin only.

---

## POST /request

Request a magic link. Sends a one-time login link to the provided email address.

**Status Code:** `200 OK`

### Request Body

| Field   | Type   | Required | Constraints                |
|---------|--------|----------|----------------------------|
| `email` | string | yes      | Valid email address, 3-320 chars |

### Response Body

| Field             | Type   | Notes                                      |
|-------------------|--------|--------------------------------------------|
| `message`         | string | Always: "If this email is registered or eligible, a login link has been sent." |
| `magic_link_token`| string | **Dev/test only.** `null` in production    |

### Behavior

1. Email is normalized to lowercase
2. Looks up user by email (may not exist — that is OK for future external collaborators)
3. If user exists but is disabled/deleted/locked — returns success silently (no info leak)
4. Expires any unconsumed `magic_link` challenges for this email (prevents accumulation)
5. Creates a new challenge in `12_trx_auth_challenges` with configurable TTL
6. Sends email via notification system (template: `magic_link_login`)
7. Emits audit event: `magic_link_requested`

### Rate Limiting

5 requests per email per hour. Returns `429 Too Many Requests` if exceeded.

### Example

```bash
POST /api/v1/auth/passwordless/request
Content-Type: application/json

{
  "email": "contractor@external.com"
}
```

```json
// 200 OK
{
  "message": "If this email is registered or eligible, a login link has been sent.",
  "magic_link_token": null
}
```

### Error Codes

| Status | Condition                                    |
|--------|----------------------------------------------|
| 422    | Validation error (invalid email format)      |
| 429    | Rate limit exceeded for this email           |

---

## POST /request-assignee

Request an assignee-only magic link (for `/assignee/login` flow).

**Status Code:** `200 OK`

### Request Body

Same as `/request`:

| Field   | Type   | Required | Constraints                |
|---------|--------|----------|----------------------------|
| `email` | string | yes      | Valid email address, 3-320 chars |

### Response Body

Same generic anti-enumeration response as `/request`:

| Field             | Type   | Notes |
|-------------------|--------|-------|
| `message`         | string | Always: "If this email is registered or eligible, a login link has been sent." |
| `magic_link_token`| string | Dev/test only |

### Behavior

1. Email is normalized to lowercase.
2. Looks up an existing user by email.
3. Issues a `magic_link_assignee` challenge only when the user exists, is active, and has at least one assigned task (primary assignee or co-assignee).
4. Unknown/unassigned/blocked emails still return generic success (no account enumeration).
5. Sends assignee login email with assignee verify URL (`MAGIC_LINK_ASSIGNEE_FRONTEND_VERIFY_URL`).

---

## POST /verify

Verify a magic link token. Creates a session and returns JWT tokens.

**Status Code:** `200 OK`

### Query Parameters

| Param   | Type   | Required | Notes                                 |
|---------|--------|----------|---------------------------------------|
| `token` | string | yes      | Magic link token: `{challenge_id}.{secret}` |

### Response Body

Same as login: `TokenPairResponse`

| Field              | Type   | Notes                              |
|--------------------|--------|------------------------------------|
| `access_token`     | string | JWT access token                   |
| `token_type`       | string | Always `"Bearer"`                  |
| `expires_in`       | int    | Access token TTL in seconds        |
| `refresh_token`    | string | Refresh token for rotation         |
| `refresh_expires_in`| int   | Refresh token TTL in seconds       |
| `user`             | object | User info (see below)              |

**User object:**

| Field            | Type    |
|------------------|---------|
| `user_id`        | string  |
| `tenant_key`     | string  |
| `email`          | string  |
| `username`       | string  |
| `email_verified` | boolean |
| `account_status` | string  |
| `user_category`  | string  |
| `is_new_user`    | boolean |

### Behavior

**If user exists (email matches an existing user):**

1. Validates challenge: not consumed, not expired, secret hash matches (constant-time)
2. Creates `magic_link` account if user doesn't have one yet (first-time passwordless for a full user)
3. Creates session in `10_trx_auth_sessions`
4. Issues JWT access token + refresh token
5. Consumes the challenge (single-use)
6. Emits audit event: `magic_link_verified`

**If user does NOT exist (new external collaborator):**

1. Validates challenge (same as above)
2. Checks `max_external_users` license limit for the platform
3. Creates user with `user_category = 'external_collaborator'`, `account_status = 'active'`
4. Sets user properties: `email` (verified), `email_verified = 'true'`, `user_category_source = 'magic_link_auto_created'`
5. Creates `magic_link` account (is_primary = true)
6. Auto-enrolls user in `external_collaborators` system group
7. Creates session + issues tokens
8. Consumes the challenge
9. Emits audit events: `magic_link_verified` + `magic_link_external_user_created`

**If challenge type is `magic_link_assignee`:**

1. User must already exist and still have assigned tasks at verify time.
2. No auto-creation of external users is performed for this channel.
3. Session is created with `portal_mode = "assignee"`.
4. Access token includes optional claim `portal_mode = "assignee"`.
5. Downstream task/comment/attachment APIs enforce assignee-only scope at query level.

### Example

```bash
POST /api/v1/auth/passwordless/verify?token=550e8400-e29b-41d4-a716-446655440000.dGhpcyBpcyBhIHNlY3JldA
```

```json
// 200 OK
{
  "access_token": "eyJhbGciOi...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "session-id.refresh-secret",
  "refresh_expires_in": 2592000,
  "user": {
    "user_id": "uuid-user-1",
    "tenant_key": "default",
    "email": "contractor@external.com",
    "username": null,
    "email_verified": true,
    "account_status": "active",
    "user_category": "external_collaborator",
    "is_new_user": true
  }
}
```

### Error Codes

| Status | Condition                                           |
|--------|-----------------------------------------------------|
| 400    | Invalid token format                                |
| 401    | Token expired, already consumed, or invalid secret  |
| 403    | User is disabled, deleted, or locked                |
| 409    | External user license limit reached                 |
| 422    | Validation error                                    |

---

## Security

| Measure                     | Detail                                                           |
|-----------------------------|------------------------------------------------------------------|
| Token entropy               | `secrets.token_urlsafe(32)` — 256 bits                         |
| Hash comparison              | `hmac.compare_digest` (constant-time)                           |
| Single-use tokens            | Challenge consumed immediately on successful verify             |
| Email enumeration prevention | Same response regardless of whether email exists                |
| Rate limiting                | 5 requests per email per hour on `/request`                     |
| Category escalation          | `user_category` only changeable by platform admins              |
| Scope isolation              | Assignee-mode sessions can only access assigned tasks/comments/attachments |

---

## Audit Events

| Event Type                        | Entity Type | When                                  |
|-----------------------------------|-------------|---------------------------------------|
| `magic_link_requested`            | `challenge` | Magic link email sent                 |
| `magic_link_verified`             | `session`   | Token verified, session created       |
| `magic_link_external_user_created`| `user`      | New external collaborator auto-created|

---

## Email Template

Template code: `magic_link_login`

**Subject:** "Your login link for K-Control"

**Variables:**

| Variable             | Description                        |
|----------------------|------------------------------------|
| `{{magic_link_url}}` | Full verify URL with token         |
| `{{expires_in_hours}}`| TTL in hours                      |
| `{{email}}`          | Recipient email                    |

---

## Configuration

| Setting                          | Env Var                         | Default | Range   |
|----------------------------------|---------------------------------|---------|---------|
| `magic_link_enabled`             | `MAGIC_LINK_ENABLED`            | `true`  | boolean |
| `magic_link_default_ttl_hours`   | `MAGIC_LINK_DEFAULT_TTL_HOURS`  | `24`    | 1-168   |
| `magic_link_frontend_verify_url` | `MAGIC_LINK_FRONTEND_VERIFY_URL`| `""`    | URL     |
| `magic_link_assignee_frontend_verify_url` | `MAGIC_LINK_ASSIGNEE_FRONTEND_VERIFY_URL` | `""` | URL |

---

## License Enforcement

External collaborators are counted separately from full users:

| License Setting       | Pool                  | Enforced At                |
|-----------------------|-----------------------|----------------------------|
| `max_users`           | Full users only       | Registration               |
| `max_external_users`  | External collaborators| Magic link verify (auto-create) |

**Seeded defaults per profile:**

| Profile            | `max_external_users` |
|--------------------|----------------------|
| `free_default`     | `10`                 |
| `pro_default`      | `100`                |
| `enterprise_default`| `500`               |
| `internal_default` | *(no limit)*         |

---

## External Collaborator Permissions

System role: `external_collaborator` (scope: `workspace`, is_system: true)

| Permission Code       | Action   | Description                        |
|-----------------------|----------|------------------------------------|
| `tasks.view`          | `view`   | View tasks assigned to them        |
| `comments.view`       | `view`   | Read comments on visible tasks     |
| `comments.create`     | `create` | Add comments on visible tasks      |
| `attachments.view`    | `view`   | View attachments on visible tasks  |
| `attachments.create`  | `create` | Upload attachments to visible tasks|

System group: `external_collaborators` — auto-enrolled on user creation. Has `external_collaborator` role assigned.

**Query-level enforcement:** Task repository filters to only return tasks where `assignee_user_id = current_user_id` OR `user_id` exists in `31_lnk_task_assignments` for users with `user_category = 'external_collaborator'`.
