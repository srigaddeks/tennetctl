---
phase: 22-iam-enterprise
plan: 01
status: complete
completed_at: 2026-04-17
---

# 22-01: OIDC SSO — Summary

## What Was Built

Full OIDC SSO vertical: per-org provider config, OAuth2 authorization-code + PKCE (S256), JIT user upsert on callback, admin UI, and sign-in entry point.

## Files Created/Modified

| File | Change |
|------|--------|
| `03_docs/.../20260417_040_iam-oidc-providers.sql` | Migration: 30_fct_oidc_providers + v_oidc_providers view |
| `03_docs/.../02_dim_account_types.yaml` | Added oidc_sso (id=5) |
| `backend/.../20_oidc_sso/` | 5-file sub-feature: schemas, repo, service, routes |
| `backend/.../routes.py` | OIDC auth routes added (initiate + callback) |
| `backend/.../feature.manifest.yaml` | iam.oidc_sso sub-feature registered (number=25) |
| `frontend/src/app/(dashboard)/iam/security/sso/page.tsx` | Admin UI |
| `frontend/src/app/auth/oidc/callback/page.tsx` | Callback page (spinner + error) |
| `frontend/src/features/iam/hooks/use-oidc-providers.ts` | TanStack Query hook |
| `frontend/src/features/auth/_components/signin-form.tsx` | SSO entry added |
| `frontend/src/types/api.ts` | OidcProvider + OidcProviderCreateBody types |
| `tests/test_oidc_sso.py` | 11 tests |

## Acceptance Criteria Status

| AC | Status |
|----|--------|
| AC-1: Provider CRUD | ✅ GET/POST/DELETE /v1/iam/oidc-providers |
| AC-2: PKCE initiate redirect | ✅ code_challenge S256, HMAC-signed state |
| AC-3: JIT user creation | ✅ New email → oidc_sso account_type user |
| AC-4: JIT merge existing | ✅ Same email → reuses existing user |
| AC-5: Admin UI | ✅ /iam/security/sso renders, form works |
| AC-6: pytest green | ✅ 11/11 pass |

## Test Results

```
11 passed in 3.76s
```

## UI Verified

- `/iam/security/sso` — empty state + Add Provider form
- `/auth/oidc/callback?error=oidc_failed` — error card + Back link
- TypeScript build: zero errors

## Key Decisions

- client_secret NEVER returned in API responses — only vault key reference stored
- State token: HMAC-SHA256(secret, base64url(payload)), TTL=10min
- JIT upsert matches email across ANY account_type (no duplicate users)
- Bootstrap default state secret derived from key name (dev); production sets vault key
