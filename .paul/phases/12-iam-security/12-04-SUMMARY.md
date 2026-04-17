# Plan 12-04 Summary — Password Reset + Account Recovery + E2E

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 12 (IAM Security Completion)

## What Was Built

### DB
- Migration 032: `"03_iam"."27_fct_iam_password_reset_tokens"` — HMAC-signed reset tokens with 15-min TTL, rate-limit index, consumed_at soft-expire

### Backend
- `sub_features/14_password_reset/` — full sub-feature (schemas, repository, service, routes)
- `POST /v1/auth/password-reset/request` — rate-limited (3/15min), HMAC token, notify fire-and-forget, always 200 (no enumeration)
- `POST /v1/auth/password-reset/complete` — hash lookup + expiry check + mark consumed + update argon2id password + mint session
- Routes wired in `backend/02_features/03_iam/routes.py`
- Signing key bootstrapped lazily into vault (`iam.password_reset_signing_key`)

### Tests (`tests/test_iam_password_reset.py` — 7 tests)
- Unknown email → 200 (no enumeration)
- Known email → 200 + token in DB
- Invalid token → 401 INVALID_TOKEN
- Expired token → 401 INVALID_TOKEN (DB expires_at check)
- Weak password → 422 WEAK_PASSWORD
- Valid token → 200 + session + new password works + old password rejected
- Double-use same token → 401 INVALID_TOKEN (consumed_at set)

### Frontend
- Types: `PasswordResetRequestBody`, `PasswordResetCompleteBody` added to `api.ts`
- Hooks: `usePasswordResetRequest`, `usePasswordResetComplete` added to `use-auth.ts`
- `/auth/forgot-password` page — email form → success state → back to sign-in link
- `/auth/password-reset` page — reads token from URL query param, new password + confirm form
- "Forgot your password?" link added to signin password tab

### E2E Robot (`tests/e2e/iam/12_auth_security.robot` — 8 smoke tests)
- All 4 signin tabs present (password, magic-link, otp, passkey)
- Forgot password link visible on password tab
- /auth/forgot-password renders
- Magic Link tab shows email form
- OTP tab shows email form
- Passkey tab shows email form
- /account/security loads without 500
- /auth/password-reset without token shows error message

## Phase 12 Complete

All 4 plans implemented:
- 12-01: Magic Link — ✅
- 12-02: Email OTP + TOTP — ✅
- 12-03: WebAuthn Passkeys — ✅
- 12-04: Password Reset + E2E — ✅

Total Phase 12 tests: 29 passing (6 magic link + 7 OTP + 9 passkeys + 7 password reset)
