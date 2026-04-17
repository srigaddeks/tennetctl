---
phase: 13-monitoring
plan: 08
subsystem: monitoring
tags: [monitoring, alerts, alerting, silences, rules, ui, nextjs, tanstack-query]

requires:
  - phase: 13-05
    provides: Query DSL (alert rule dsl payload)
  - phase: 11
    provides: Notify transactional send (notify_template_key)

provides:
  - monitoring alerts UI at /monitoring/alerts (events), /monitoring/alerts/rules, /monitoring/alerts/silences
  - frontend types (AlertRule, AlertEvent, Silence, etc.)
  - 11 TanStack Query hooks for alerts (rules CRUD + pause/unpause, events list/detail with auto-poll, silences CRUD, silence-from-event)
affects: [future alerting-adjacent features]

tech-stack:
  added: []
  patterns:
    - "Auto-refetch (15s) on firing-alerts list for near-live view"
    - "labels key=value newline-separated input pattern for simple JSON map editing"

key-files:
  created:
    - frontend/src/features/monitoring/hooks/use-alerts.ts
    - frontend/src/app/(dashboard)/monitoring/alerts/page.tsx
    - frontend/src/app/(dashboard)/monitoring/alerts/rules/page.tsx
    - frontend/src/app/(dashboard)/monitoring/alerts/silences/page.tsx
  modified:
    - frontend/src/types/api.ts  (added AlertSeverity, AlertTarget, AlertConditionOp, AlertState, AlertCondition, AlertRule, AlertRuleCreateRequest, AlertRuleUpdateRequest, AlertRuleListResponse, SilenceMatcher, Silence, SilenceCreateRequest, SilenceListResponse, AlertEvent, AlertEventListResponse)
    - frontend/src/config/features.ts  (nav entries Alerts / Alert Rules / Silences)

key-decisions:
  - "Three separate pages (events / rules / silences) rather than a single tabbed page — matches the 7-page monitoring pattern and keeps each concern isolated"
  - "DSL entered as raw JSON textarea, not a guided builder — minimum-viable; guided builder is a follow-up (reuses dsl-filter-builder component possible)"
  - "Labels input is key=value per line rather than JSON — simpler for operators; parsed on submit"
  - "Alert-events auto-poll every 15s — operators need near-live firing status without websockets"

duration: ~45min
completed: 2026-04-17
---

# Phase 13 Plan 08: Alerts Frontend Summary

**Three new pages under /monitoring/alerts drive the existing 13-08 backend (sub-feature `07_alerts`): event list with silence-from-event action, rules CRUD with pause/unpause, and silences CRUD. Full TanStack Query layer + types + nav wiring; tsc + build green.**

## Scope note

Plan 13-08 originally covered backend + frontend. The backend (migrations 049/050, `07_alerts` sub-feature with 5 files + nodes) was applied ad-hoc before this session and was documented implicitly in STATE.md. This summary covers only the **frontend UI layer** delivered in this session. E2E suite deferred per directive (2026-04-17: "forget about robot e2e completely focus on features and functionality").

## Acceptance Criteria Results

| AC | Status | Notes |
|---|---|---|
| Alert rules CRUD UI | Pass | Create (full form with DSL JSON + condition + severity + template key + labels), list, pause 1h, unpause, delete |
| Alert events list | Pass | Firing / Resolved / All filter, severity badges, state column (shows "silenced" chip), value/threshold, started/resolved times, inline Silence action |
| Silences UI | Pass | Create (rule select + labels + duration + reason), list with active/expired status, delete |
| Auto-refresh firing alerts | Pass | 15s refetchInterval on events query |
| Navigation | Pass | 3 sub-nav items added under Monitoring: Alerts / Alert Rules / Silences |
| E2E | Deferred | Per user directive |

## What Was Built

### Types (`frontend/src/types/api.ts`)
15 new types covering rules, silences, and events — mirror the Pydantic response shapes exactly (including `severity_label`, `silenced`, `silence_id`, `annotations`).

### Hook (`frontend/src/features/monitoring/hooks/use-alerts.ts`)
11 TanStack Query hooks:
- `useAlertRules`, `useAlertRule`, `useCreateAlertRule`, `useUpdateAlertRule`, `useDeleteAlertRule`, `usePauseAlertRule`, `useUnpauseAlertRule`
- `useAlertEvents(state?)`, `useAlertEvent`
- `useSilences`, `useCreateSilence`, `useDeleteSilence`, `useSilenceFromEvent`

Invalidations cross-invalidate events and silences together (silence creation re-polls events so the "silenced" chip appears).

### Pages

- **`/monitoring/alerts`** — table of events with Firing/Resolved/All filter. Silence action opens modal with duration-hours + reason; submits via `/v1/monitoring/alerts/{id}/silence`.
- **`/monitoring/alerts/rules`** — rules table with status chip (active / paused / disabled). Create modal has DSL as raw JSON textarea, op/threshold/for-duration condition, severity select, notify-template-key input, labels textarea (key=value per line). Pause is 1h preset; Unpause cancels.
- **`/monitoring/alerts/silences`** — silences table with active/expired chip. Create modal with optional rule select + label matchers + duration-hours + reason.

### Nav
`features.ts` gains 3 entries under the Monitoring group.

## Deviations from Plan

| Deviation | Why |
|-----------|-----|
| No guided DSL builder | Plan scope is minimum viable; raw-JSON textarea ships faster and the query-builder component from logs/metrics pages can be slotted in later |
| No "edit rule" modal | Create/delete/pause are enough for v1; edit can reuse the create modal with prefilled state when added |
| Label input is `key=value` per line, not a chip editor | Same simplicity-first reasoning; operator-facing feature, low churn |
| E2E deferred | Per user directive 2026-04-17 — "forget about robot e2e completely" |

## Verification

- `npx tsc --noEmit` → clean
- `npm run build` → green; 3 new static routes prerendered (`/monitoring/alerts`, `/monitoring/alerts/rules`, `/monitoring/alerts/silences`)
- No modifications to backend or tests

## Next Phase Readiness

**Ready:** Phase 13 (Monitoring) feature work is now complete end-to-end through alerting.

**Concerns:**
- Edit-rule UX missing (workaround: delete + recreate)
- DSL input is free-text JSON — operator typos are caught by backend validation but not surfaced inline

**Blockers:** None.

---
*Phase: 13-monitoring, Plan: 08*
*Completed: 2026-04-17 (frontend only; backend applied ad-hoc prior)*
