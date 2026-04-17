---
plan: 20-04
status: complete
completed_at: 2026-04-17
---

# Plan 20-04 — Session Limits: COMPLETE

## What Was Done

- Migration 053: `last_activity_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP` added to `16_fct_sessions`, backfilled to `created_at`, indexed. Already applied.
- Sessions repo: `bump_last_activity`, `list_active_for_user`, `revoke_session_by_reason`, `get_raw_by_id` added.
- Sessions service: `enforce_session_limits` (oldest/lru/reject eviction) and `check_session_timeouts` (idle + absolute TTL) implemented.
- Middleware: after session validation, checks idle_timeout + absolute_ttl via `check_session_timeouts`; returns 401 SESSION_EXPIRED if expired. Fire-and-forget `bump_last_activity` on each accepted request.

## Tests

5 tests in `tests/test_session_limits.py` — all pass.

- `test_bump_last_activity_updates_column`
- `test_idle_timeout_revokes_session`
- `test_absolute_ttl_revokes_session`
- `test_max_concurrent_oldest_evicts`
- `test_max_concurrent_reject_raises_429`
