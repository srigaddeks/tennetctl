# 22-04 Admin Impersonation — Summary

## Status: COMPLETE

## What was built

Admin impersonation system: super-admins can impersonate regular users for debugging, with a 30-minute TTL and full dual-actor audit trail.

### Migration
- `20260418_043_iam-impersonation.sql` — creates `"03_iam"."45_lnk_impersonations"` linking impersonation sessions to both actors

### Backend sub-feature `23_impersonation`
- `repository.py` — insert/get/end impersonation link rows
- `service.py` — super-admin check via system role (role_type_id=1), guards (no self-impersonation, no admin impersonation, no nesting), mints 30-min session, dual-actor audit events
- `routes.py` — `GET /v1/iam/impersonation` (status), `POST /v1/iam/impersonation` (start), `DELETE /v1/iam/impersonation` (end)

### Middleware update
- `backend/01_core/middleware.py` — detects impersonation sessions, populates `request.state.impersonator_user_id` and `request.state.impersonated_user_id` on every request

### Frontend
- `frontend/src/features/iam/hooks/use-impersonation.ts` — TanStack Query hooks
- `frontend/src/features/iam/_components/impersonation-banner.tsx` — red banner with "End session" button
- `frontend/src/app/(dashboard)/layout.tsx` — banner wired into dashboard layout
- `frontend/src/types/api.ts` — `ImpersonationStatus`, `StartImpersonationRequest` types

### Tests
- `tests/test_impersonation.py` — 8/8 passing
  - Start impersonation (201, session token works as target)
  - Impersonated session acts as target user
  - Status check (no active impersonation)
  - End impersonation (204, subsequent request → 401)
  - Non-admin → 403
  - Self-impersonation → 403
  - Admin-impersonation → 403
  - Nested impersonation → 403/409

## Key decisions
- Super-admin identified by system role (role_type_id=1), not a column on fct_users
- `lnk_*` table keeps fct_sessions pure (no extra columns)
- 30-min TTL enforced via `expires_at` on the minted session row
- `ended_at` on lnk allows early termination
