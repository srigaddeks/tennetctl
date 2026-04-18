# Phase 36 Plan 02 — SUMMARY

**Plan:** 36-02 Notify Suppressions admin
**Status:** ✅ Complete
**Date:** 2026-04-18

## What shipped
- `/notify/suppressions` page — list + add modal + remove
- Reason-coded Badge tones (hard_bounce red, complaint amber, unsubscribe blue, manual zinc)
- Sidebar entry under Notify feature between Deliveries and Send API
- `use-suppressions.ts` hook module + `NotifySuppression*` types

## Files
- **Created**
  - `frontend/src/app/(dashboard)/notify/suppressions/page.tsx`
  - `frontend/src/features/notify/hooks/use-suppressions.ts`
- **Modified**
  - `frontend/src/types/api.ts` — suppression types
  - `frontend/src/config/features.ts` — nav entry

## Verification
- `npx tsc --noEmit` — clean
- `npx next build` — success, `/notify/suppressions` registered as static

## Decisions
- No edit path — suppressions are immutable by design in the backend schema. Delete + re-add is the correct flow.
- Reason options in the Add modal default to `manual` (operator-initiated). `hard_bounce` and `complaint` are backend-generated via SES/SMTP feedback loops but remain valid options for debugging.
- Confirmed via `window.confirm` rather than Modal — matches existing Notify settings delete UX; avoids UI sprawl.
