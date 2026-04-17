---
phase: 21-iam-oss-completion
plan: 03
status: complete
---

# Plan 21-03 Summary: First-Run Setup Wizard

## What Was Built

**Backend `backend/02_features/03_iam/sub_features/18_setup/`**:
- `GET /v1/setup/status` — always public, returns `{initialized, setup_required, user_count}`
- `POST /v1/setup/initial-admin` — creates first admin user with mandatory TOTP + 10 backup codes, sets `system.initialized=true` in vault. Returns TOTP otpauth URI + backup codes once only.

**`SetupModeMiddleware`** in `backend/01_core/middleware.py`:
- Blocks all routes with `503 SETUP_REQUIRED` when `12_fct_users` is empty and vault config not set
- Allowlist: `/health`, `/v1/setup/status`, `/v1/setup/initial-admin`, `/docs`, `/openapi.json`, `/redoc`
- Caches `True` on `app.state.setup_initialized` after first confirmed-initialized check
- Registered before `SessionMiddleware` (outermost gate)

**Frontend**:
- `frontend/src/app/setup/page.tsx` — setup page
- `frontend/src/features/iam/_components/setup-wizard.tsx` — 2-step wizard
- `frontend/src/features/iam/hooks/use-setup.ts` — TanStack Query hooks
- `frontend/src/proxy.ts` — updated to redirect to `/setup` when `setup_required=true`; removed conflicting `middleware.ts`
- `frontend/src/types/api.ts` — `SetupStatus`, `InitialAdminBody`, `InitialAdminResult` types

**Tests**: `tests/test_iam_setup_mode.py` — 6 passing tests.

**Pre-existing build fix**: `frontend/src/app/(dashboard)/iam/users/[id]/page.tsx` — Badge `variant→tone`, Button `warning→danger`, `showToast→toast`.

## Key Design Decisions

- Idempotency: `user_count > 0` is the authoritative check
- Role assignment deferred: `lnk_user_roles.org_id` is NOT NULL FK; role record created but user-to-role link waits for org creation
- TOTP mandatory for root; backup codes generated atomically in same call
