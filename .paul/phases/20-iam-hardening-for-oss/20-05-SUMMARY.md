---
phase: 20-iam-hardening-for-oss
plan: 05
status: complete
---

# Plan 20-05 Summary: Audit Coverage Closure

## What Was Done

- **Audit emissions wired** across all auth-adjacent service functions:
  - `magic_link/service.py` — `iam.magic_link.consume_failed`
  - `otp/service.py` — `iam.otp.email.verify_succeeded/failed`, `iam.otp.totp.verify_succeeded/failed`, `iam.otp.totp.enrolled/deleted`
  - `password_reset/service.py` — `iam.password_reset.requested/completed`
  - `10_auth/service.py` — `iam.credentials.verify_failed`

- **Password reset revokes all sessions** atomically in same transaction.

- **Tests passing**: `tests/test_iam_audit_coverage_closure.py` (4 tests), `tests/test_iam_password_reset_revokes.py` (1 test)
