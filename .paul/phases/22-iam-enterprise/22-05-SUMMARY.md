# 22-05 MFA Enforcement Policy — Summary

## Status: COMPLETE

## What was built

Per-org MFA enforcement: admins can require all users to enroll in TOTP before signing in.

### Backend sub-feature `24_mfa_policy`
- `schemas.py` — `MfaPolicyUpdate`, `MfaPolicyStatus` Pydantic models
- `service.py` — reads/writes `iam.policy.mfa.required` vault config (scope=org), checks TOTP enrollment via OTP repo, `check_mfa_gate()` for sign-in enforcement
- `routes.py` — `GET /v1/iam/mfa-policy` (status + enrollment check), `PUT /v1/iam/mfa-policy` (toggle)

### Auth service wiring
- `backend/02_features/03_iam/sub_features/10_auth/service.py` — `signin()` calls `check_mfa_gate` with `ctx.org_id` (from `x-org-id` header) before minting session; raises `MFA_ENROLLMENT_REQUIRED` (403) if org requires MFA but user not enrolled; wrapped in best-effort try/except so transient failures don't block sign-in

### Frontend
- `frontend/src/features/iam/hooks/use-mfa-policy.ts` — TanStack Query hooks
- `frontend/src/app/(dashboard)/iam/security/mfa/page.tsx` — toggle switch + user enrollment status
- `frontend/src/types/api.ts` — `MfaPolicyStatus` type added

### Tests
- `tests/test_mfa_policy.py` — 5/5 passing
  - GET policy (default off + totp_enrolled=false)
  - Enable policy (PUT → GET confirms)
  - Disable policy (roundtrip)
  - Sign-in blocked when MFA required but not enrolled (403 + MFA_ENROLLMENT_REQUIRED code)
  - Sign-in passes when MFA required and enrolled (mocked TOTP credential)

## Key decisions
- Policy stored as vault config (scope=org) not in a separate table — no migration needed
- `ctx.org_id` (from `x-org-id` header) takes priority over attached org for gate check
- best-effort try/except around gate — transient vault failures never block all sign-ins
- No frontend TOTP enrollment flow here (exists in OTP sub-feature); this page only shows status
