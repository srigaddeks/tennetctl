# 22-03 SCIM 2.0 — Summary

## Status: COMPLETE

## What was built

SCIM 2.0 (RFC 7644) provisioning system for identity providers (Okta, Azure AD, etc.).

### Migration
- `20260418_042_iam-scim-tokens.sql` — creates `"03_iam"."32_fct_scim_tokens"` with per-org token storage (SHA256 hashed), SCIM external ID attr_def (id=50)

### Backend
- `schemas.py` — SCIM envelope builders (`scim_user`, `scim_group`, `scim_list`, `scim_error`), admin token Pydantic models
- `repository.py` — token CRUD, externalId EAV attr ops, group member link table ops (`43_lnk_user_groups`)
- `service.py` — SHA256 bearer auth, SCIM filter parser, full Users + Groups CRUD with PatchOp engine
- `routes.py` — admin token router at `/v1/iam/scim-tokens`, SCIM 2.0 router at `/scim/v2/{org_slug}/Users|Groups`

### Frontend
- `frontend/src/features/iam/hooks/use-scim-tokens.ts` — TanStack Query hooks (list, create, revoke)
- `frontend/src/app/(dashboard)/iam/security/scim/page.tsx` — token management UI with one-time token reveal
- `frontend/src/types/api.ts` — `ScimToken`, `ScimTokenCreateBody` types added

### Tests
- `tests/test_scim.py` — 13/13 passing
  - Token create/list/revoke
  - Bearer auth rejection
  - User CRUD (create, get, list, patch deactivate, deprovision)
  - Group CRUD (create, list, patch add member)
  - Conflict detection (409)

## Key decisions
- Tokens stored as SHA256 hex, raw token returned once at creation only
- SCIM users provisioned as `email_password` account type (standard JIT)
- Groups use existing `14_fct_groups` + `43_lnk_user_groups` tables
- externalId stored as EAV attr (attr_def_id=50) to keep fct_users clean
