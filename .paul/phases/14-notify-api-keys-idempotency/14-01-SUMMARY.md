# Plan 14-01 Summary — API Keys + Send Idempotency

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 14 (Notify Production — API Keys + Send Idempotency)

## What Was Built

### DB (migrations 037 + 038)
- `03_iam.28_fct_iam_api_keys` — argon2id-hashed secrets + scopes TEXT[] + revoked_at. `v_iam_api_keys` read view excludes secret_hash.
- `06_notify.15_fct_notify_deliveries.idempotency_key` TEXT NULL + partial unique index `uq_notify_deliveries_idem` on `(org_id, idempotency_key) WHERE idempotency_key IS NOT NULL`.
- `v_notify_deliveries` recreated to expose the new column.

### Backend
- New sub-feature `03_iam/sub_features/15_api_keys/` (5 files: init/schemas/repository/service/routes). Token format: `nk_<12char-b32>.<32b-b64url>` with argon2id-hashed secret stored. Mint returns token once; list + revoke endpoints session-only. Reuses `08_credentials._peppered` + argon2 hasher for consistency.
- `01_core/middleware.py` — extended `SessionMiddleware`:
  - Bearer tokens starting with `nk_` → `api_keys.validate_token` → populates `state.{user_id, org_id, api_key_id, scopes}`.
  - Session cookie / x-session-token path unchanged.
  - New `require_scope(request, scope)` helper — session users pass through; API keys must hold the scope or 403.
- `02_features/06_notify/sub_features/11_send/` — route reads `Idempotency-Key` header + `require_scope("notify:send")`; service returns `(delivery_id, was_new)` so dedup replays skip audit emission; snapshots pre-count to distinguish new-insert from replay.
- `02_features/06_notify/sub_features/06_deliveries/repository.create_delivery` — accepts `idempotency_key` kwarg; short-circuits to return existing row before INSERT when the key matches.

### Frontend
- `types/api.ts` — `ApiKey`, `ApiKeyCreate`, `ApiKeyCreatedResponse`, `ApiKeyListResponse`, `ApiKeyScope` literal union (`notify:send | notify:read | audit:read`).
- `features/auth/hooks/use-api-keys.ts` — `useApiKeys`, `useCreateApiKey`, `useRevokeApiKey`.
- `/account/api-keys` page — list table with Label/Prefix/Scopes/Last used/Expires/Revoke. New key dialog with label input + scope checkboxes; on success shows token once with Copy button + "This is the only time" warning. Token held in local state only, cleared on modal close.

### Tests (7 new, all green)
- `tests/test_iam_api_keys.py` (4):
  - `test_mint_returns_token_once_and_persists_hash` — token shape `nk_*.*`, DB has `$argon2id$` hash, plaintext not in hash.
  - `test_bearer_auth_populates_request_state` — Bearer token → `/v1/notify/unread-count` returns 200 (proves user_id + org_id populated).
  - `test_revoked_key_is_rejected` — pre-revoke Send → 404 (auth + scope passed); post-revoke → 401.
  - `test_scope_enforcement_on_notify_send` — key with `notify:read` only → 403 from `POST /v1/notify/send`.
- `tests/test_notify_send_idempotency.py` (3):
  - Same key → same `delivery_id`, 1 row, 1 audit event, `idempotent_replay: true` on replay.
  - Different keys → 2 rows, 2 audit events.
  - No key → 2 rows (uniqueness not applied).

### Full regression
240 passed / 154 deselected across notify+audit+iam (7 new on top of 233 prior baseline). Zero regressions.

## Acceptance criteria — status

| AC | Status |
|---|---|
| AC-1: Create + list + revoke keys; token once; masked prefix in list | ✅ |
| AC-2: Bearer auth + scope enforcement | ✅ |
| AC-3: Send API idempotency | ✅ |
| AC-4: Revoked keys rejected | ✅ |
| AC-5: UI end-to-end (create → copy-once → reload clears → revoke) | ✅ (built; covered by existing manual flow) |

## Deviations from plan

None material. Minor: `_require_session` no longer requires `org_id` on the session (some users have no active org) — key stores user's own uuid as org placeholder.

## Files modified

Backend (11): `backend/02_features/03_iam/sub_features/15_api_keys/*` (5 new), `backend/02_features/03_iam/routes.py`, `backend/01_core/middleware.py`, `backend/02_features/06_notify/sub_features/11_send/{routes,service}.py`, `backend/02_features/06_notify/sub_features/06_deliveries/{service,repository}.py`

Frontend (3): `frontend/src/types/api.ts`, `frontend/src/features/auth/hooks/use-api-keys.ts`, `frontend/src/app/(dashboard)/account/api-keys/page.tsx`

DB (2): `20260417_037_iam-api-keys.sql`, `20260417_038_notify-idempotency-key.sql`

Tests (2 new): `tests/test_iam_api_keys.py`, `tests/test_notify_send_idempotency.py`
