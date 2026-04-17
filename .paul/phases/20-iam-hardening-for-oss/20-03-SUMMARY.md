# Plan 20-03 Summary — Account Lockout

## Completed
- Migration `20260417_052_create-failed-auth-attempts.sql`: Creates `"03_iam"."23_fct_failed_auth_attempts"` with index on `(email, attempted_at DESC)`. Applied.
- `08_credentials/repository.py`: Added `record_failed_attempt`, `count_failed_in_window`, `get_lockout_until`, `set_lockout_until`, `clear_lockout`. Lockout stored as `dtl_attrs.key_text` using auto-registered attr_def.
- `08_credentials/service.py`: Added `check_lockout` (with expired lockout auto-clear) and `record_failure_and_maybe_lock` (uses fresh pool connection to survive caller tx rollback).
- `10_auth/service.py` `signin()`: Pre-signin lockout check (423 if locked); post-failure lockout recording + `iam.lockout.triggered` audit event emission.
- `tests/test_iam_account_lockout.py`: 4 tests covering attempt recording, threshold lockout (via monkeypatched auth_policy), expired lockout auto-clear, active lockout blocking.

## Key design decisions
- `record_failure_and_maybe_lock` uses `pool.acquire()` (fresh connection) not `conn` so the insert survives the caller's rolled-back transaction.
- Lockout threshold/window/duration all come from `AuthPolicy.lockout(org_id)` — no hardcoded values.
- `check_lockout` proactively clears expired lockouts so the column is self-healing.
- On account-not-found path, we record best-effort attempt (no user_id) for IP forensics.

## Tests: 4 passed

## Post-completion fixes (2026-04-17)
- `check_lockout` now returns `(locked_until, was_expired_and_cleared)` tuple instead of `locked_until | None`.
- `signin()` unpacks the tuple and emits `iam.lockout.cleared` when a previously locked account successfully authenticates.
- Fixed `utcnow()` deprecation: now uses `datetime.now(timezone.utc)`.
- Feature manifest: added `iam.lockout` sub-feature (number: 20) documenting the two audit event keys.
