---
phase: 21-iam-oss-completion
plan: 01
status: complete
---

## What Was Built

Email verification sub-feature (`16_email_verification/`) for IAM — policy-gated, HMAC-signed tokens, Notify integration, frontend page.

## Deliverables

### Migration
- `20260417_056_iam-email-verification.sql` — creates `29_fct_iam_email_verifications` table + registers `email_verified_at` attr_def (entity_type_id=3, value_type=text). Applied successfully.

### Backend Sub-feature
- `backend/02_features/03_iam/sub_features/16_email_verification/` — 5 files (`__init__.py`, `schemas.py`, `repository.py`, `service.py`, `routes.py`)
- `POST /v1/auth/verify-email/send` (202, no user enumeration, rate-limited 5/60min)
- `POST /v1/auth/verify-email/consume` (400 on invalid/expired/double-consumed, 200 on success + sets email_verified_at)
- Token: 32-byte random `secrets.token_urlsafe`, HMAC-SHA256 stored hash, 24h TTL, signing key auto-bootstrapped to vault

### Auth /me Enhancement
- `GET /v1/auth/me` now includes `email_verified: bool` field (from `email_verified_at` EAV attr)

### IAM Routes
- `backend/02_features/03_iam/routes.py` — registered `_email_verification_routes`

### Notify Seed
- `backend/02_features/06_notify/seeds/iam_email_verify_template.yaml` — template key `iam.email.verify`, transactional group, email channel, variables: `verify_url`, `ttl_hours`, `user_display_name`

### Frontend
- `frontend/src/app/(dashboard)/auth/verify-email/page.tsx` — consumes `?token=` param via API, auto-redirects on success; shows resend form when no token present
- `frontend/src/types/api.ts` — added `email_verified?: boolean` to `User` type + `EmailVerifySendBody`, `EmailVerifyConsumeBody`, `EmailVerifyConsumeResult` types

## Test Results

```
10 passed in 4.17s
```

All acceptance criteria covered:
- AC-1: Schema — table + attr_def exist
- AC-3: Consume flow — invalid/expired/double-consume → 400; valid → 200 + email_verified_at set
- AC-4: /me email_verified field before and after verification

## Acceptance Criteria Status

- [x] Migration clean; attr_def registered
- [x] send endpoint: no enumeration, 202 always
- [x] consume endpoint: all error cases + success path
- [x] /me includes email_verified bool
- [x] Frontend page for token consumption + resend
- [x] Notify template seeded (iam.email.verify)
- [x] 10 pytest tests pass

## Notes

- `schedule_verification_if_required()` in service.py is available for signup hook integration (auth service can call it post-user-creation; fire-and-forget so email send failure never breaks signup)
- Policy gate uses `AuthPolicy.resolve(None, "signup.require_email_verification")` — falls back to `require=True` if policy unavailable
- Robot E2E (`21_email_verification.robot`) deferred — requires live SMTP/notify delivery chain
