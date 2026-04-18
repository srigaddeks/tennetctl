---
phase: 22-iam-enterprise
plan: 02
status: complete
completed_at: 2026-04-18
---

# 22-02: SAML 2.0 SSO — Summary

## What Was Built

Full SAML 2.0 SP-initiated SSO vertical: per-org IdP config, python3-saml SP metadata + AuthnRequest + ACS validation, JIT user upsert, admin UI, tests.

## Files Created/Modified

| File | Change |
|------|--------|
| `03_docs/.../21_saml_sso/00_bootstrap/.../20260418_041_iam-saml-providers.sql` | Migration: 31_fct_saml_providers + v_saml_providers view |
| `backend/.../21_saml_sso/` | 5-file sub-feature: schemas, repo, service, routes |
| `backend/.../routes.py` | SAML auth routes added (metadata, initiate, ACS) + saml_sso_routes included |
| `frontend/src/app/(dashboard)/iam/security/saml/page.tsx` | Admin UI |
| `frontend/src/features/iam/hooks/use-saml-providers.ts` | TanStack Query hook |
| `frontend/src/types/api.ts` | SamlProvider + SamlProviderCreateBody types |
| `tests/test_saml_sso.py` | 11 tests |

## Acceptance Criteria Status

| AC | Status |
|----|--------|
| AC-1: Migration — fct_saml_providers | ✅ 31_fct_saml_providers + v_saml_providers |
| AC-2: Provider CRUD | ✅ GET/POST/DELETE /v1/iam/saml-providers |
| AC-3: SP metadata | ✅ GET /v1/auth/saml/{org_slug}/metadata → XML |
| AC-4: SP-initiated flow | ✅ initiate (302 to IdP) + ACS (validate + 303 redirect) |
| AC-5: JIT user upsert | ✅ Email match across any account_type; saml_sso (id=6) created if new |
| AC-6: pytest green | ✅ 11/11 pass |

## Test Results

```
11 passed in 5.07s
```

## UI Verified

- `/iam/security/saml` — empty state + Add Provider form (IdP Entity ID, SSO URL, SP Entity ID, x509 cert textarea)
- Form opens/closes correctly
- TypeScript build: zero errors

## Key Decisions

- x509_cert stored in DB (public IdP cert — not a secret; no vault needed)
- PEM headers stripped on ingest (stored as raw base64 cert)
- relay_state: HMAC-SHA256(secret, base64url(payload)), TTL=10min (same pattern as OIDC state)
- python3-saml (OneLogin) handles AuthnRequest + ACS validation
- saml_sso account_type id=6 added to dim_account_types
- No IdP-initiated SSO, no SLO (single logout)
