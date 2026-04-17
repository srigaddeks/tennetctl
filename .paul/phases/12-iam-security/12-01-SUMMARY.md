# Plan 12-01 Summary — Magic Link Sub-Feature

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 12 (IAM Security Completion)

## What Was Built

### DB
- Migration 029: `"03_iam"."19_fct_iam_magic_link_tokens"` table with HMAC token hash, TTL, consumed_at, ip_address, rate-limit index

### Backend
- `sub_features/11_magic_link/` — full sub-feature (schemas, repository, service, routes)
- `POST /v1/auth/magic-link/request` — rate-limited (3/15min), creates HMAC token, enqueues notify (fire-and-forget), always returns 200
- `POST /v1/auth/magic-link/consume` — validates hash + expiry + consumed_at, marks consumed, mints session (same response shape as signin)
- Routes wired in `backend/02_features/03_iam/routes.py`

### Frontend
- Magic Link tab added to signin form (`_components/signin-form.tsx`)
- `useMagicLinkRequest()` hook in `use-auth.ts`
- `/auth/magic-link/callback` page — consumes token from URL, redirects to `/`

### Tests (`tests/test_iam_magic_link.py` — 6 tests)
- Unknown email → 200 (no user enumeration)
- Known email → 200 + token created
- Invalid token → 401
- Valid token → 200 + session returned
- Token used twice → 401 TOKEN_ALREADY_USED
- Expired token → 401 TOKEN_EXPIRED

### Bug Fix
- `SendTransactional` node rewrote to use `run()` + `Input`/`Output` Pydantic models (was using `handler()` + JSON Schema dicts which the runner doesn't support)

## Decisions
- Notify call in `request_magic_link` is fire-and-forget (catch exception silently) — endpoint always returns 200 (no enumeration)
- Signing key bootstrapped lazily into vault on first use (`iam.magic_link_signing_key`)
- `pydantic[email]` added to deps for EmailStr in schemas
