# Phase 35 Plan 02 — SUMMARY

**Plan:** 35-02 Notify Subscriptions admin (edit flows)
**Status:** ✅ Complete
**Date:** 2026-04-18

## What shipped
- Edit (PATCH) wired end-to-end for Notify SMTP Configs, Template Groups, and Subscriptions — previously only create + delete
- Three new Update types + three new update hooks with dirty-field submission pattern
- Inline Edit button on every row in `/notify/settings`; dedicated edit modals pre-fill from the row and submit only dirty fields
- Subscriptions get an `is_active` toggle — activate/deactivate without delete-recreate
- Template Groups get `is_active` + editable `smtp_config_id` and `category_id`
- SMTP Configs get full label/host/port/tls/username/vault-key/from_*/is_active editing

## Files
- **Modified**
  - `frontend/src/types/api.ts` — added `NotifySMTPConfigUpdate`, `NotifyTemplateGroupUpdate`, `NotifySubscriptionUpdate`
  - `frontend/src/features/notify/hooks/use-notify-settings.ts` — added `useUpdateSMTPConfig`, `useUpdateTemplateGroup`, `useUpdateSubscription`
  - `frontend/src/app/(dashboard)/notify/settings/page.tsx` — Edit buttons on all three tables; `EditSMTPDialog`, `EditGroupDialog`, `EditSubscriptionDialog` components added

## Verification
- `npx tsc --noEmit` — clean (pre-existing FormEvent deprecation warnings only, non-blocking)
- `npx next build` — success

## Decisions
- Kept `/notify/settings` monolithic rather than splitting into three pages — unified nav + route separation is Phase 36 scope. Inline edit unblocks daily admin without creating routing churn.
- Dirty-field body construction (same pattern Plan 35-01 used for workspaces): compare each field to the original row, only PATCH what changed; empty-body short-circuits with a no-op close. Avoids over-posting and makes the audit trail accurate.
- Edit dialogs use plain `useState` + manual reset-on-row-change rather than react-hook-form. Settings page's existing create dialogs use the same pattern — consistency > library preference.
- Subscriptions don't allow editing `recipient_mode`/`recipient_filter` via this plan. Backend Update schema omits both; if an operator needs to change recipient wiring, delete + recreate is the correct path because filter semantics change the dim_channel fan-out contract.

## Deferred
- Suppressions admin, Campaigns admin, per-template Analytics — 🟡 severity, not 🔴
- Playwright MCP walk-through — deferred to /paul:verify (no live backend this session)
- apiFetch → @tennetctl/sdk swap — Phase 36-03
- Split /notify/settings into per-resource routes — Phase 36
