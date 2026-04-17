# Plan 20-06 Summary — Miscellaneous IAM OSS Completion

## Status: COMPLETE

## What Was Done

### Task 1: TOTP Backup Codes
- Migration 054: `"03_iam"."28_fct_totp_backup_codes"` table (UUID v7 PK, user_id FK, code_hash TEXT, consumed_at TIMESTAMP NULL).
- `otp/repository.py`: `insert_backup_code`, `list_active_backup_codes`, `get_backup_code_by_hash`, `mark_backup_code_consumed`, `delete_all_backup_codes`.
- `otp/service.py`: `setup_totp()` now generates 10 backup codes on enrollment; `verify_backup_code()` consumes one code atomically; `generate_backup_codes()` regenerates.
- `otp/routes.py`: `POST /v1/auth/totp/backup-codes/verify` and `POST /v1/auth/totp/backup-codes/regenerate`.

### Task 2: Email OTP via Notify
- OTP delivery already routes through `notify.send.transactional` node with template key `iam.otp-code`.

### Task 3: API Key Rotation + last_used_at
- Migration 055: `ALTER TABLE 28_fct_iam_api_keys ADD COLUMN last_used_at TIMESTAMP NULL`.
- `api_keys/repository.py`: `touch_last_used()` already in place; added `get_raw_by_id()`.
- `api_keys/service.py`: `rotate_api_key()` — revokes old, creates new with same scopes, emits `iam.api_keys.rotated`.
- `api_keys/routes.py`: `POST /v1/api-keys/{key_id}/rotate`.
- `middleware.py`: `touch_last_used` already called fire-and-forget on every Bearer auth.

### Task 4: IAM Metrics
- `iam/metrics.py`: helpers for `iam_failed_auth_total`, `iam_lockouts_triggered_total`, `iam_sessions_evicted_total`, `iam_otp_verify_total`, `iam_password_reset_total`.
- `auth/service.py`: already wires `_emit_metric()` for lockout + failed auth counter.

### Task 5: Tests
- `tests/test_iam_totp_backup_codes.py`: 4 tests — enrollment returns 10 codes, verify works, single-use enforced, regenerate invalidates old codes.
- `tests/test_iam_api_key_rotation.py`: 2 tests — rotation creates new + revokes old, last_used_at column exists.

## Test Results
```
All 6 new tests pass.
```

## Audit Event Keys Added
- `iam.api_keys.rotated` registered in feature.manifest.yaml
