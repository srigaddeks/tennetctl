# Passwordless Authentication — Technical Breakdown

Last updated: 2026-03-17

## 1. Problem Statement

Tasks in K-Control can be assigned to external people (contractors, auditors, vendors) who don't have accounts. Currently, there's no way for these people to access the system to upload evidence, add comments, or interact with their assigned tasks. We need:

1. A magic-link login flow that works for anyone with an email
2. Auto-creation of limited "external collaborator" users on first magic-link verify
3. Full users should also be able to use magic link as an alternative to password login
4. External collaborators must be counted separately for licensing/pricing

---

## 2. Database Changes

### 2a. Schema: `03_auth_manage`

**ALTER — `03_fct_users`** (add `user_category` column):

```sql
ALTER TABLE "03_auth_manage"."03_fct_users"
  ADD COLUMN IF NOT EXISTS user_category VARCHAR(50) NOT NULL DEFAULT 'full';

-- CHECK constraint
ALTER TABLE "03_auth_manage"."03_fct_users"
  ADD CONSTRAINT ck_03_fct_users_user_category
  CHECK (user_category IN ('full', 'external_collaborator'));

-- Index for license counting queries
CREATE INDEX IF NOT EXISTS idx_03_fct_users_user_category
  ON "03_auth_manage"."03_fct_users" (tenant_key, user_category)
  WHERE is_deleted = FALSE AND is_active = TRUE;
```

**Rationale:** `user_category` is a first-class structural field (not EAV) because it drives license counting, permission scoping, and query filtering across every domain. Joining through `05_dtl_user_properties` for every query that needs user type would be expensive and error-prone.

---

**SEED — `06_dim_account_types`** (new account type):

```sql
INSERT INTO "03_auth_manage"."06_dim_account_types"
  (id, code, name, description, sort_order, created_at, updated_at)
VALUES
  (gen_random_uuid(), 'magic_link', 'Magic Link',
   'Passwordless email magic link authentication', 70, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

---

**SEED — `02_dim_challenge_types`** (new challenge type):

```sql
INSERT INTO "03_auth_manage"."02_dim_challenge_types"
  (id, code, name, description, sort_order, created_at, updated_at)
VALUES
  (gen_random_uuid(), 'magic_link', 'Magic Link',
   'One-time passwordless login challenge', 30, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

---

**SEED — `04_dim_user_property_keys`** (new property key):

```sql
INSERT INTO "03_auth_manage"."04_dim_user_property_keys"
  (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
  (gen_random_uuid(), 'user_category_source', 'User Category Source',
   'How the user was created: registration, magic_link_auto_created, admin_created',
   'string', FALSE, FALSE, 200, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

---

**SEED — `16_fct_roles`** (system role for external collaborators):

```sql
INSERT INTO "03_auth_manage"."16_fct_roles"
  (id, tenant_key, role_level_code, code, name, description,
   is_active, is_system, is_locked, is_disabled, is_deleted, is_test,
   created_at, updated_at)
VALUES
  (gen_random_uuid(), 'default', 'platform', 'external_collaborator',
   'External Collaborator',
   'Limited access for passwordless external users — can view assigned tasks, upload attachments, and comment',
   TRUE, TRUE, TRUE, FALSE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (tenant_key, role_level_code, code) DO NOTHING;
```

---

**SEED — `17_fct_user_groups`** (system group):

```sql
INSERT INTO "03_auth_manage"."17_fct_user_groups"
  (id, tenant_key, role_level_code, code, name, description,
   is_active, is_system, is_locked, is_disabled, is_deleted, is_test,
   created_at, updated_at)
VALUES
  (gen_random_uuid(), 'default', 'platform', 'external_collaborators',
   'External Collaborators',
   'System group for external collaborator users. Auto-enrolled on magic link account creation.',
   TRUE, TRUE, TRUE, FALSE, FALSE, FALSE, NOW(), NOW())
ON CONFLICT (tenant_key, role_level_code, code) DO NOTHING;
```

---

**SEED — Role-to-group assignment + role permissions:**

```sql
-- Assign external_collaborator role to external_collaborators group
INSERT INTO "03_auth_manage"."19_lnk_group_role_assignments"
  (id, group_id, role_id, is_active, is_system, created_at, updated_at)
SELECT
  gen_random_uuid(),
  g.id,
  r.id,
  TRUE, TRUE, NOW(), NOW()
FROM "03_auth_manage"."17_fct_user_groups" g,
     "03_auth_manage"."16_fct_roles" r
WHERE g.code = 'external_collaborators'
  AND r.code = 'external_collaborator'
ON CONFLICT DO NOTHING;

-- Assign feature permissions to external_collaborator role
-- (tasks.view, comments.view, comments.create, attachments.view, attachments.create)
INSERT INTO "03_auth_manage"."20_lnk_role_feature_permissions"
  (id, role_id, feature_permission_id, is_active, is_system, created_at, updated_at)
SELECT
  gen_random_uuid(),
  r.id,
  fp.id,
  TRUE, TRUE, NOW(), NOW()
FROM "03_auth_manage"."16_fct_roles" r,
     "03_auth_manage"."15_dim_feature_permissions" fp
WHERE r.code = 'external_collaborator'
  AND fp.code IN (
    'tasks.view',
    'comments.view', 'comments.create',
    'attachments.view', 'attachments.create'
  )
ON CONFLICT (role_id, feature_permission_id) DO NOTHING;
```

---

**SEED — License profile settings:**

```sql
-- Add max_external_users to existing profiles
INSERT INTO "03_auth_manage"."38_dtl_license_profile_settings"
  (id, profile_id, setting_key, setting_value, created_at, updated_at)
SELECT gen_random_uuid(), p.id, 'max_external_users', v.limit_value, NOW(), NOW()
FROM "03_auth_manage"."37_fct_license_profiles" p
JOIN (VALUES
  ('free_default',       '10'),
  ('pro_default',        '100'),
  ('pro_trial_default',  '100'),
  ('enterprise_default', '500'),
  ('partner_default',    '50'),
  ('internal_default',   '999999')
) AS v(profile_code, limit_value) ON p.code = v.profile_code
ON CONFLICT (profile_id, setting_key) DO NOTHING;
```

---

**ALTER — `42_vw_auth_users`** (add `user_category` to view):

```sql
CREATE OR REPLACE VIEW "03_auth_manage"."42_vw_auth_users" AS
SELECT
    u.id AS user_id,
    u.tenant_key AS tenant_key,
    u.user_category AS user_category,
    email_prop.property_value AS email,
    username_prop.property_value AS username,
    COALESCE(email_verified_prop.property_value, 'false') AS email_verified,
    u.account_status AS account_status
FROM "03_auth_manage"."03_fct_users" AS u
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS email_prop
    ON email_prop.user_id = u.id AND email_prop.property_key = 'email'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS username_prop
    ON username_prop.user_id = u.id AND username_prop.property_key = 'username'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS email_verified_prop
    ON email_verified_prop.user_id = u.id AND email_verified_prop.property_key = 'email_verified'
WHERE u.is_deleted = FALSE
  AND u.is_test = FALSE;
```

---

## 3. Backend Module Structure

### New module: `backend/03_auth_manage/17_passwordless/`

```
backend/03_auth_manage/17_passwordless/
├── __init__.py
├── constants.py        # TTL defaults, rate limits
├── models.py           # ChallengeRecord (reuse from models.py)
├── schemas.py          # RequestMagicLinkRequest, RequestMagicLinkResponse
├── repository.py       # Challenge CRUD, user lookup, external user count
├── service.py          # PasswordlessService
├── dependencies.py     # get_passwordless_service
└── router.py           # POST /request, POST /verify
```

Closest existing analog: `backend/03_auth_manage/09_invitations/`

### Service Dependencies

```python
class PasswordlessService:
    def __init__(
        self,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager,
    ):
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = PasswordlessRepository()
        self._auth_repository = AuthRepository()     # reuse for user creation
        self._refresh_tokens = RefreshTokenManager()  # reuse for token gen
        self._jwt_codec = JWTCodec(settings)          # reuse for access tokens
        self._audit_writer = AuditWriter()
```

### Key Method Signatures

```python
async def request_magic_link(
    self,
    payload: RequestMagicLinkRequest,
    *,
    client_ip: str | None,
    request_id: str | None,
) -> RequestMagicLinkResponse:
    """Create challenge, send email, return success message."""

async def verify_magic_link(
    self,
    token: str,
    *,
    client_ip: str | None,
    user_agent: str | None,
    request_id: str | None,
) -> TokenPairResponse:
    """Verify token, create/find user, create session, return JWT tokens."""
```

---

## 4. Modifications to Existing Files

### `backend/03_auth_manage/constants.py`

```python
# Add to AccountType
MAGIC_LINK = "magic_link"

# Add to ChallengeType
MAGIC_LINK = "magic_link"

# Add to AuditEventType
MAGIC_LINK_REQUESTED = "magic_link_requested"
MAGIC_LINK_VERIFIED = "magic_link_verified"
MAGIC_LINK_EXTERNAL_USER_CREATED = "magic_link_external_user_created"
```

### `backend/03_auth_manage/models.py`

```python
# Add user_category to AuthenticatedUser
@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    user_id: str
    tenant_key: str
    email: str
    username: str | None
    email_verified: bool
    account_status: str
    user_category: str = "full"  # NEW

# Add user_category to AccessSessionState
@dataclass(frozen=True, slots=True)
class AccessSessionState:
    ...
    user_category: str = "full"  # NEW
```

### `backend/00_config/settings.py`

```python
# Add to Settings dataclass (after api_key settings)
magic_link_enabled: bool = True
magic_link_default_ttl_hours: int = 24
magic_link_frontend_verify_url: str = ""
magic_link_assignee_frontend_verify_url: str = ""

# Add to load_settings()
magic_link_enabled=_read_bool("MAGIC_LINK_ENABLED", default=True),
magic_link_default_ttl_hours=_read_int("MAGIC_LINK_DEFAULT_TTL_HOURS", default=24, minimum=1),
magic_link_frontend_verify_url=os.getenv("MAGIC_LINK_FRONTEND_VERIFY_URL", "").strip(),
magic_link_assignee_frontend_verify_url=os.getenv("MAGIC_LINK_ASSIGNEE_FRONTEND_VERIFY_URL", "").strip(),
```

### `backend/03_auth_manage/repository.py`

New methods needed:

```python
async def find_user_by_email_only(
    self, connection, *, tenant_key: str, email: str
) -> AuthenticatedUser | None:
    """Lighter than find_user_by_identity — no password hash join."""

async def create_user_with_category(
    self, connection, *, tenant_key: str, user_category: str, now: datetime
) -> tuple[str, str]:
    """Like create_user but accepts user_category."""

async def count_users_by_category(
    self, connection, *, tenant_key: str, user_category: str
) -> int:
    """Count active, non-deleted users of a given category."""
```

### `backend/03_auth_manage/schemas.py`

```python
# Add user_category to AuthUserResponse
class AuthUserResponse(BaseModel):
    user_id: str
    tenant_key: str
    email: str
    username: str | None
    email_verified: bool
    account_status: str
    user_category: str = "full"  # NEW
    is_new_user: bool = False    # NEW (for magic link verify)
```

---

## 5. Sequence Diagrams

### Request Magic Link

```
User                Frontend              Backend                   DB                    Email
 │                    │                      │                       │                       │
 │  enter email       │                      │                       │                       │
 │───────────────────>│                      │                       │                       │
 │                    │  POST /request       │                       │                       │
 │                    │─────────────────────>│                       │                       │
 │                    │                      │  find_user_by_email   │                       │
 │                    │                      │──────────────────────>│                       │
 │                    │                      │  <── user or null     │                       │
 │                    │                      │                       │                       │
 │                    │                      │  expire old challenges│                       │
 │                    │                      │──────────────────────>│                       │
 │                    │                      │                       │                       │
 │                    │                      │  create challenge     │                       │
 │                    │                      │──────────────────────>│                       │
 │                    │                      │  <── challenge_id     │                       │
 │                    │                      │                       │                       │
 │                    │                      │  queue notification   │                       │
 │                    │                      │──────────────────────────────────────────────>│
 │                    │                      │                       │                       │
 │                    │  200 OK {message}    │                       │                       │
 │                    │<─────────────────────│                       │                       │
 │  "check email"     │                      │                       │                       │
 │<───────────────────│                      │                       │                       │
```

### Verify Magic Link (Existing User)

```
User                Frontend              Backend                   DB
 │                    │                      │                       │
 │  click magic link  │                      │                       │
 │───────────────────>│                      │                       │
 │                    │  POST /verify?token  │                       │
 │                    │─────────────────────>│                       │
 │                    │                      │  get challenge        │
 │                    │                      │──────────────────────>│
 │                    │                      │  <── challenge record │
 │                    │                      │                       │
 │                    │                      │  validate (expiry,    │
 │                    │                      │   consumed, hash)     │
 │                    │                      │                       │
 │                    │                      │  find user by email   │
 │                    │                      │──────────────────────>│
 │                    │                      │  <── user record      │
 │                    │                      │                       │
 │                    │                      │  ensure magic_link    │
 │                    │                      │  account exists       │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │                      │  create session       │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │                      │  consume challenge    │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │  200 TokenPairResponse│                      │
 │                    │<─────────────────────│                       │
 │  redirect /dashboard                      │                       │
 │<───────────────────│                      │                       │
```

### Verify Magic Link (New External Collaborator)

```
User                Frontend              Backend                   DB
 │                    │                      │                       │
 │  click magic link  │                      │                       │
 │───────────────────>│                      │                       │
 │                    │  POST /verify?token  │                       │
 │                    │─────────────────────>│                       │
 │                    │                      │  validate challenge   │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │                      │  find user → NULL     │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │                      │  check license limit  │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │                      │  BEGIN TRANSACTION    │
 │                    │                      │  create user (ext_c)  │
 │                    │                      │  create email prop    │
 │                    │                      │  create magic_link    │
 │                    │                      │    account            │
 │                    │                      │  add to ext_collab    │
 │                    │                      │    group              │
 │                    │                      │  create session       │
 │                    │                      │  consume challenge    │
 │                    │                      │  COMMIT               │
 │                    │                      │──────────────────────>│
 │                    │                      │                       │
 │                    │  200 TokenPairResponse│                      │
 │                    │  (is_new_user: true)  │                      │
 │                    │<─────────────────────│                       │
 │  redirect /dashboard (task-scoped view)   │                       │
 │<───────────────────│                      │                       │
```

---

## 6. Frontend Changes

### New Pages

| Page | Route | Purpose |
|------|-------|---------|
| Magic Link Request | `/magic-link` | Email input → "check your email" |
| Magic Link Verify | `/magic-link/verify?token=...` | Auto-verify on mount → redirect |

Both in route group `(001_auth)`.

### API Functions (`frontend/apps/web/src/lib/api/auth.ts`)

```typescript
export async function requestMagicLink(email: string): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/auth/passwordless/request`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  // ...
}

export async function verifyMagicLink(token: string): Promise<TokenPairResponse> {
  const res = await fetch(`${API_BASE}/auth/passwordless/verify?token=${encodeURIComponent(token)}`, {
    method: "POST",
  });
  // ...
}
```

### Login Page Enhancement

Add "Sign in with magic link" link below password form on `auth-page.tsx`. Links to `/magic-link`.

### Admin UI

- User list: filter by `user_category` (All / Full / External Collaborator)
- User rows: show category badge
- Count cards: "Full Users: X / max_users" | "External Users: Y / max_external_users"
- Platform settings: `magic_link_ttl_hours` number input (1-168)

---

## 7. Migration File

**Path:** `backend/01_sql_migrations/02_inprogress/20260317_add-passwordless-auth.sql`

Move to `01_migrated/` before merging to main.

---

## 8. Testing Strategy

### Integration Tests (`backend/90_tests/test_passwordless_auth.py`)

| Test | Description |
|------|-------------|
| `test_request_magic_link_existing_user` | User exists → challenge created, dev token returned |
| `test_request_magic_link_nonexistent_email` | No user → challenge still created (silent success) |
| `test_request_magic_link_disabled_user` | Disabled user → same success response (no info leak) |
| `test_verify_existing_user` | Existing user → session created, tokens returned |
| `test_verify_new_external_user` | No user → user auto-created with `external_collaborator` category |
| `test_verify_expired_token` | Challenge expired → 401 error |
| `test_verify_consumed_token` | Already consumed → 401 error |
| `test_verify_invalid_secret` | Wrong secret → 401 error |
| `test_full_user_gets_magic_link_account` | Existing `local_password` user → `magic_link` account added |
| `test_external_user_license_limit` | Exceed `max_external_users` → 409 error |
| `test_external_user_permissions` | External user can view assigned tasks, cannot view other tasks |

### Robot Framework Tests (`backend/90_tests/robot_tests/passwordless_auth.robot`)

End-to-end API flow:
1. Request magic link for new email
2. Extract token from dev response
3. Verify token → confirm tokens valid (call `/me`)
4. Confirm user has `user_category = 'external_collaborator'`
5. Request magic link for existing registered user
6. Verify → confirm session created without new user

---

## 9. Cache Impact

### New Cache Keys

| Key | TTL | Invalidated By |
|-----|-----|----------------|
| `passwordless:rate:{email_hash}` | 1 hour | Auto-expire (rate limiting counter) |

### Existing Cache Invalidation

- `user:{id}:profile` — invalidated when external user is auto-created
- `access:{uid}:{org}:{ws}` — invalidated when external user is added to group

---

## 10. Notification Integration

### Template: `magic_link_login`

**Seed via notification template system or migration:**

- Type: `magic_link_login`
- Channel: `email`
- Subject: `Your login link for K-Control`
- Body variables: `{{magic_link_url}}`, `{{expires_in_hours}}`, `{{email}}`

**Email body content:**

```
You've requested a login link for K-Control.

Click the link below to sign in:
{{magic_link_url}}

This link expires in {{expires_in_hours}} hours.

If you didn't request this link, you can safely ignore this email.
```

---

## 11. Implementation Order

1. SQL migration (can be deployed independently)
2. Backend constants + models (add enums, update dataclasses)
3. Backend settings (add magic_link config)
4. Backend repository updates (new query methods)
5. Backend passwordless module (service, repository, schemas, router)
6. Wire up router in main app
7. Notification template
8. Integration tests
9. Frontend API functions
10. Frontend pages (request + verify)
11. Login page enhancement (magic link button)
12. Admin UI updates (user category filter, license counts, TTL config)
13. Robot Framework tests
