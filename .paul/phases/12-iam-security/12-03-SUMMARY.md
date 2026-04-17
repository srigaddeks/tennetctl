# Plan 12-03 Summary — WebAuthn Passkeys Sub-Feature

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 12 (IAM Security Completion)

## What Was Built

### DB
- Migration 031: `"03_iam"."25_fct_iam_passkey_challenges"` — short-lived ceremony challenges (registration + authentication, 5-min TTL, consumed once)
- Migration 031: `"03_iam"."26_fct_iam_passkey_credentials"` — FIDO2 credentials per user (credential_id, public_key, aaguid, sign_count, device_name, soft-delete)

### Backend
- `sub_features/13_passkeys/` — full sub-feature (schemas, repository, service, routes)
- Registration: `POST /v1/auth/passkeys/register/begin` + `POST /v1/auth/passkeys/register/complete`
- Authentication: `POST /v1/auth/passkeys/auth/begin` + `POST /v1/auth/passkeys/auth/complete`
- Management: `GET /v1/auth/passkeys` + `DELETE /v1/auth/passkeys/{id}`
- Uses `py_webauthn` (v2.7.1) for WebAuthn ceremonies
- RP ID/origin configured via `TENNETCTL_WEBAUTHN_RP_ID`, `TENNETCTL_WEBAUTHN_ORIGIN` env vars
- Routes wired in `backend/02_features/03_iam/routes.py`

### Tests (`tests/test_iam_passkeys.py` — 9 tests)
- Register begin requires auth → 401 (unauthenticated)
- Register begin (authenticated) → valid options JSON with challenge + rp.id
- Auth begin (no passkeys) → 404 NO_PASSKEYS
- Auth begin (unknown user) → 404
- Auth begin (user with passkey) → valid options JSON + allowCredentials populated
- Register complete (invalid challenge) → 401 INVALID_CHALLENGE
- Auth complete (invalid challenge) → 401 INVALID_CHALLENGE
- List passkeys → returns enrolled credentials
- Delete passkey → 204, removed from list
Note: register_complete/auth_complete happy paths require real authenticator — validated via E2E browser test

### Frontend
- Types: `PasskeyRegisterBeginResponse`, `PasskeyAuthBeginResponse`, `PasskeyCredential`, `PasskeyListResponse` added to `api.ts`
- Hooks: `usePasskeyRegisterBegin`, `usePasskeyRegisterComplete`, `usePasskeyAuthBegin`, `usePasskeyAuthComplete`, `usePasskeyList`, `usePasskeyDelete` added to `use-auth.ts`
- Passkey tab added to signin form — email → navigator.credentials.get() → complete ceremony → redirect
- `/account/security` page extended with passkey enrollment (navigator.credentials.create()) + device management (list + delete)

## Decisions
- RP_ID defaults to `localhost` for development; configurable via env var
- Origin defaults to `http://localhost:51735` (frontend dev server port)
- Challenges stored in DB with 5-min TTL (not Redis/Valkey — no requirement for cache yet)
- Public key stored as base64url string (py_webauthn returns bytes; converted for DB storage)
- Tests use direct DB credential insertion for list/delete tests (bypassing WebAuthn ceremony which requires real browser)
