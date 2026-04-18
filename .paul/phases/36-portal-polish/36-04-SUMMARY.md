# Phase 36 Plan 04 — SUMMARY

**Plan:** 36-04 Monitoring saved queries admin + nav completeness sweep
**Status:** ✅ Complete
**Date:** 2026-04-18

## What shipped

### Monitoring saved queries admin
- New page `/monitoring/saved-queries` — lists saved DSL snippets (logs/metrics/traces)
- Filter dropdown by target; per-row link back to the matching explorer with `?saved={id}`
- Delete confirm; shared/private Badge; inactive state surfaced
- New hooks: `useSavedQueries`, `useSavedQuery`, `useCreateSavedQuery`, `useUpdateSavedQuery`, `useDeleteSavedQuery`
- New types: `SavedQueryCreateRequest`, `SavedQueryUpdateRequest` (reused existing `SavedQuery`, `SavedQueryListResponse`, `QueryTarget`)

### Nav completeness sweep
Cross-referenced every `frontend/src/app/(dashboard)/*` route against the sidebar FEATURES config and added every missing entry:

- **IAM**: `/iam/invites`, `/iam/security/sso`, `/iam/security/saml`, `/iam/security/scim`, `/iam/security/mfa`, `/iam/security/ip-allowlist`, `/iam/security/siem`, `/iam/security/tos`
- **Account**: `/account/privacy`
- **Monitoring**: `/monitoring/saved-queries`

After this sweep every static route in `src/app/(dashboard)/**` is either in the sidebar or a legitimate drill-down (dynamic `[id]` route reached via list navigation). Auth `/auth/**` flow routes remain intentionally unlinked from the admin sidebar.

## Files
- **Modified**
  - `frontend/src/types/api.ts` — Create/Update request types for saved queries
  - `frontend/src/config/features.ts` — 10 new nav entries across IAM + Account + Monitoring
- **Created**
  - `frontend/src/features/monitoring/hooks/use-saved-queries.ts`
  - `frontend/src/app/(dashboard)/monitoring/saved-queries/page.tsx`

## Verification
- `npx tsc --noEmit` — clean
- `npx next build` — success, all new routes registered

## Why the nav gap mattered
Before this sweep, `/iam/security/sso`, `/iam/security/saml`, `/iam/security/scim`, `/iam/security/mfa`, `/iam/security/ip-allowlist`, `/iam/security/siem`, `/iam/security/tos`, and `/iam/invites` were shipped pages with no sidebar link — admins had to know the URL to reach them. Similarly `/account/privacy` was a complete GDPR export/erasure surface with no discoverable entry.

## Remaining gaps (backend does not exist)
- **Notify Campaigns** — sub_feature directory is `__pycache__`-only, no code
- **Impersonation history** — routes only support status/start/end, no list endpoint
- **Audit Funnel / Retention** — no backend sub-features
- **Monitoring Synthetic Checks** — no backend
- **Background worker status / Migration history** — no dedicated endpoints

Adding UI for any of these requires backend work first and belongs in a future milestone (v0.3.0+).
