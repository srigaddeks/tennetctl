---
phase: 22-iam-enterprise
plan: 07
type: summary
status: complete
completed_at: 2026-04-17
---

# 22-07 Summary — Time-Bounded Role Assignments + Expiry Sweeper

## What Was Built

`expires_at` column on `lnk_user_roles` so role assignments can self-revoke after a deadline. A background sweeper runs every 5 minutes, marks expired rows `revoked_at = NOW()`, and emits `iam.roles.expired` audit events.

## Deliverables

**Backend** (`backend/02_features/03_iam/sub_features/04_roles/`):
- `repository.py` — `assign_role` now accepts `expires_at`; `expire_due()` bulk-revokes overdue rows and returns them for audit emission
- `expiry_sweeper.py` — `run_once(pool)` + `start_sweeper(pool, interval_seconds=300)` async background task; best-effort audit per revoked row
- `routes.py` — `POST /v1/iam/roles/assign` updated to accept optional `expires_at` (ISO8601)

**Backend wiring** (`backend/main.py`):
- `start_sweeper` launched as `asyncio` background task on app startup

**Tests** (`tests/test_role_expiry.py`):
- Covers assign-with-expiry, sweeper run_once revoke count, no-op on non-expired

## Decisions

- Sweeper uses `CURRENT_TIMESTAMP` comparison — no clock drift risk (all in Postgres)
- Audit emitted fire-and-forget per row; sweeper never fails on audit error
- `audit_category="setup"` (system-initiated, no user actor)
- Interval configurable at call site; default 300s (5 min)
