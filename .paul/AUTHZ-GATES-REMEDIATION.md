# Authorization Gates Remediation Plan

**Status:** Critical security gap identified in v0.1.8 audit  
**Impact:** Fresh users with zero roles can mutate admin resources (MFA policy, IP allowlist, SMTP configs, etc.)  
**Severity:** 🔴 CRITICAL — blocks compliance certification

---

## Root Cause

All admin endpoint handlers in `/v1/notify/*`, `/v1/iam/roles/*`, `/v1/iam/mfa-policy/*`, `/v1/iam/ip-allowlist/*`, and similar check `user_id` existence but **never validate the user has an admin role in the org**.

Current pattern:
```python
@router.post("/v1/notify/smtp-configs")
async def create_smtp_config_route(request: Request, body: SmtpConfigCreate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)  # ← only extracts user_id from session
    async with pool.acquire() as conn:
        row = await _service.create_smtp_config(conn, pool, ctx2, data=...)  # ← no role check!
    return _response.success(...)
```

This allows any authenticated user (even with zero roles) to:
- Create/update/delete SMTP configs
- Modify MFA enforcement policy
- Add/remove IP allowlist entries
- Modify role templates
- And more...

---

## Solution: Authorization Helper Module

Created: `backend/02_features/03_iam/sub_features/29_authz_gates/authz_helpers.py`

Provides:
- `require_admin_role(conn, user_id, org_id)` — check admin-level role
- `require_org_owner(conn, user_id, org_id)` — check org owner
- `require_mfa_admin(conn, user_id, org_id)` — check MFA admin role
- `require_security_admin(conn, user_id, org_id)` — check security admin
- `require_notify_admin(conn, user_id, org_id)` — check notify admin

All defined roles must exist in `fct_roles`:
```sql
INSERT INTO 03_iam.fct_roles (org_id, role_type, code, label) VALUES
('...', 'admin', 'org_admin', 'Organization Administrator'),
('...', 'security_admin', 'security_admin', 'Security Administrator'),
('...', 'notify_admin', 'notify_admin', 'Notification Administrator'),
('...', 'owner', 'org_owner', 'Organization Owner');
```

---

## Endpoints Requiring Gates (by module)

### notify (06_notify)

| Endpoint | Method | Requires | Rationale |
|----------|--------|----------|-----------|
| `/v1/notify/smtp-configs` | POST | admin or notify_admin | SMTP is org-level config |
| `/v1/notify/smtp-configs/{id}` | PATCH | admin or notify_admin | Only admin can modify |
| `/v1/notify/smtp-configs/{id}` | DELETE | admin or notify_admin | Only admin can delete |
| `/v1/notify/templates` | POST | admin or notify_admin | Template design is org-scoped |
| `/v1/notify/templates/{id}` | PATCH | admin or notify_admin | — |
| `/v1/notify/templates/{id}` | DELETE | admin or notify_admin | — |
| `/v1/notify/template-groups` | POST | admin or notify_admin | — |
| `/v1/notify/template-groups/{id}` | PATCH | admin or notify_admin | — |
| `/v1/notify/subscriptions/{id}` | PATCH | admin or (self if user) | Users manage own, admin can override |
| `/v1/notify/suppression-rules` | POST | admin or notify_admin | — |
| `/v1/notify/suppression-rules/{id}` | DELETE | admin or notify_admin | — |

### iam.roles (03_iam/04_roles)

| Endpoint | Method | Requires | Rationale |
|----------|--------|----------|-----------|
| `/v1/roles` | POST | admin | Only admin creates roles |
| `/v1/roles/{id}` | PATCH | admin | Only admin modifies roles |
| `/v1/roles/{id}` | DELETE | admin | Only admin deletes roles |

### iam.mfa_policy (03_iam/24_mfa_policy)

| Endpoint | Method | Requires | Rationale |
|----------|--------|----------|-----------|
| `/v1/iam/mfa-policy` | PATCH | admin or mfa_admin | MFA is org-level security policy |
| `/v1/iam/mfa-policy/enforcement` | POST | admin or mfa_admin | — |

### iam.ip_allowlist (03_iam/25_ip_allowlist)

| Endpoint | Method | Requires | Rationale |
|----------|--------|----------|-----------|
| `/v1/iam/ip-allowlist` | POST | admin or security_admin | IP rules are org-level security |
| `/v1/iam/ip-allowlist/{id}` | PATCH | admin or security_admin | — |
| `/v1/iam/ip-allowlist/{id}` | DELETE | admin or security_admin | — |

### iam.siem_export (03_iam/26_siem_export)

| Endpoint | Method | Requires | Rationale |
|----------|--------|----------|-----------|
| `/v1/iam/siem/destinations` | POST | admin or security_admin | SIEM export is org-scoped audit |
| `/v1/iam/siem/destinations/{id}` | PATCH | admin or security_admin | — |
| `/v1/iam/siem/destinations/{id}` | DELETE | admin or security_admin | — |

### iam.tos (03_iam/27_tos)

| Endpoint | Method | Requires | Rationale |
|----------|--------|----------|-----------|
| `/v1/iam/tos` | PATCH | admin | ToS is org-level policy |

---

## Implementation Checklist

Each endpoint requires this pattern:

```python
@router.post("/v1/notify/smtp-configs")
async def create_smtp_config_route(request: Request, body: SmtpConfigCreate) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    
    # ← ADD: Authorization gate
    if not ctx.user_id:
        raise _errors.HTTPException(403, "Forbidden: Authentication required")
    
    async with pool.acquire() as conn:
        # ← ADD: Role check before mutation
        is_admin = await _authz.require_notify_admin(conn, ctx.user_id, ctx.org_id)
        if not is_admin:
            raise _errors.HTTPException(403, "Forbidden: Admin role required to create SMTP configs")
        
        ctx2 = replace(ctx, conn=conn)
        row = await _service.create_smtp_config(...)
    return _response.success(...)
```

---

## Phase Breakdown (v0.1.8 Hardening)

| Phase | Scope | Endpoints | Effort |
|-------|-------|-----------|--------|
| 38-01 | Session hardening + rate limit | — | ✅ SHIPPED |
| 38-02 | Session rotation + TOTP | — | ✅ SHIPPED |
| **38-03** | **AuthZ gates (THIS)** | 30+ endpoints | ~3-4 hours |
| 39-01-03 | NCP v1 maturity | — | Deferred |

---

## Testing

Add to `tests/test_iam_authz_gates.py`:

```python
@pytest.mark.asyncio
async def test_create_smtp_config_requires_admin(pool, test_org_id, test_user_no_role):
    """Non-admin user cannot create SMTP config."""
    client = TestClient(app)
    response = client.post(
        "/v1/notify/smtp-configs",
        headers={"x-user-id": test_user_no_role, "x-org-id": test_org_id},
        json={"host": "...", ...}
    )
    assert response.status_code == 403
    assert "forbidden" in response.json()["error"].lower()
```

---

## Deployment

1. Create `sub_features/29_authz_gates/` module
2. Implement `authz_helpers.py` (done ✅)
3. Patch all mutation endpoints (30 endpoints across 6 modules)
4. Add role seeding migration
5. Add unit + E2E tests
6. Deploy to staging, validate with non-admin user
7. Merge to main + release v0.1.8

---

## Deferred (v1.0)

- Fine-grained role-based access control (per-workspace, per-resource)
- Delegation (users grant admin to others without being admin)
- Time-limited elevated access
- Audit of all admin actions (already audited; will enhance dashboard)
