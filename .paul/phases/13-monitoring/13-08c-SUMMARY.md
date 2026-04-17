# 13-08c — Monitoring Alerts Frontend + E2E — SUMMARY

Final chunk of Plan 13-08. Brings Phase 13 Monitoring to 100% by completing
the alerts UI (list, detail, rule editor, silence dialog), wiring sidebar
navigation, and proving the end-to-end loop (seed → evaluator fires → UI
row → silence → editor create/edit) in Robot Framework.

## Scope delivered

### Frontend types (frontend/src/types/api.ts)

All alert types already landed in 13-08b: `AlertSeverity`, `AlertTarget`,
`AlertConditionOp`, `AlertState`, `AlertCondition`, `AlertRule`,
`AlertRuleCreateRequest`, `AlertRuleUpdateRequest`,
`AlertRuleListResponse`, `SilenceMatcher`, `Silence`,
`SilenceCreateRequest`, `SilenceListResponse`, `AlertEvent`,
`AlertEventListResponse`. Verified complete — no additions needed.

### Hooks (frontend/src/features/monitoring/hooks/)

- `use-alerts.ts` — already existed; extended:
  - `useAlertEvent(id, startedAt)` now takes the composite key and passes
    `?started_at=…` per backend contract
  - `useSilenceFromEvent` now sends full `SilenceCreateRequest` body
    (`matcher`, `starts_at`, `ends_at`, `reason`) + `?started_at=` query
    param, matching the backend route signature
- `use-alert-rules.ts` — NEW: focused re-exports of the rule hooks
  (`useAlertRule`, `useAlertRules`, `useCreateAlertRule`,
  `useUpdateAlertRule`, `useDeleteAlertRule`, `usePauseAlertRule`,
  `useUnpauseAlertRule`) so the editor imports from a single module
- `use-silences.ts` — NEW: focused re-exports of silence hooks
  (`useSilences`, `useCreateSilence`, `useDeleteSilence`,
  `useSilenceFromEvent`)

### Components (frontend/src/features/monitoring/_components/)

- `alert-list.tsx` — NEW: table of alert events, severity pill (blue /
  yellow / orange / red per info / warn / error / critical), state badge
  (firing red, resolved emerald, silenced purple), filter chips for state
  + severity, per-row Silence button, empty state + loading skeleton,
  refetch every 15s. Each row click routes to `/monitoring/alerts/[id]`
  with `started_at` query param
- `alert-rule-editor.tsx` — NEW: create/edit form with:
  - Name, description
  - Target switcher (metrics/logs) — defaults to metrics
  - DSL simple form — metrics: `metric_key` + `aggregate` + `bucket` +
    `timerange` selects; logs: `severity_min` + `body_contains` +
    `timerange` selects
  - Advanced "Raw DSL JSON" mode toggle for power users
  - Condition form: op + threshold + for_duration_seconds
  - Severity radio group (info / warn / error / critical) + hidden mirror
    select `data-testid="rule-severity-select"` so Robot
    `Select Options By` works
  - Notify template key input (free text — no Notify `GET /templates`
    listing call, per plan's "recommended path" which avoids blocking on
    notify template plumbing)
  - Recipient user_id input, stored in `labels.recipient_user_id` (how
    the evaluator resolves notify recipients)
  - Save + Cancel
  - Update path strips `target` field before PATCH (update schema
    forbids it per `extra="forbid"`)
- `silence-dialog.tsx` — NEW: modal with datetime-local `starts_at` /
  `ends_at` inputs (default: now → now + 1h), required reason textarea,
  wired to either `useSilenceFromEvent` (when opened from alert row /
  detail) or `useCreateSilence` (generic). Passes through
  `alertEvent.started_at` so the backend's `?started_at=` requirement
  is met

### Pages (frontend/src/app/(dashboard)/monitoring/alerts/)

- `page.tsx` — `/monitoring/alerts` — renders `AlertList` + "Manage
  rules" link
- `[id]/page.tsx` — `/monitoring/alerts/[id]?started_at=…` — detail
  view:
  - Header: rule name + severity pill + state badge + silenced badge
  - Stats grid: Value / Threshold / Notifications (w/ last notified)
  - Inline Recharts `LineChart` of metric values (last 1h, 1m bucket)
    with horizontal `ReferenceLine` at threshold — only renders when
    the alert's annotations carry a `metric_key`
  - Labels table (k/v) and annotations JSON panel
  - Silence button opens `SilenceDialog`
- `rules/page.tsx` — `/monitoring/alerts/rules` — table with columns
  name / target / severity / condition / template / status; row actions
  edit / pause-1h / unpause / delete. "New rule" button routes to
  `rules/new`. Rules fetched with `useAlertRules`
- `rules/new/page.tsx` — NEW: renders `<AlertRuleEditor ruleId={null} />`
- `rules/[id]/page.tsx` — NEW: renders `<AlertRuleEditor ruleId={id} />`
  — the editor loads existing rule via `useAlertRule` and prefills state

### Nav (frontend/src/config/features.ts)

Extended the Monitoring feature's `subFeatures` array with:
- Alerts — `/monitoring/alerts`
- Alert Rules — `/monitoring/alerts/rules`
- Silences — `/monitoring/alerts/silences`

All with `nav-monitoring-*` testIds.

### Robot E2E (tests/e2e/monitoring/05_alerts_end_to_end.robot)

4 test cases, all green. Suite reuses `monitoring_keywords.resource`
(shared helpers for signup / OTLP seeding / metric API) and relies on
the stack launch setting `TENNETCTL_MONITORING_ALERT_EVAL_INTERVAL_S=10`
so evaluator cycles complete within the E2E Sleep windows.

1. `Alert Rule Fires When Threshold Breached` — seeds a counter metric
   and rule with `threshold=0`, waits 40s, verifies an `alert-row` +
   `alert-severity-critical` appear in the list
2. `Silence Alert From Row` — clicks the row's Silence button, fills
   reason, saves; verifies via API that the silence was created (note:
   existing firing events don't retroactively flip `silenced=true` —
   that's an append-only invariant; the silence still suppresses
   further Notify delivery, which is covered by pytest in 13-08b)
3. `Alert Rule Editor Creates Rule` — navigates to `/rules/new`, fills
   the form (simple metrics mode), saves; verifies the new rule appears
   on the list
4. `Rule Editor Supports Edit Flow` — opens an existing rule via the
   Edit action, changes severity via the hidden mirror select, saves;
   verifies the PATCH succeeded and the rule row is still listed

## Files

Created:
- `frontend/src/features/monitoring/_components/alert-list.tsx`
- `frontend/src/features/monitoring/_components/alert-rule-editor.tsx`
- `frontend/src/features/monitoring/_components/silence-dialog.tsx`
- `frontend/src/features/monitoring/hooks/use-alert-rules.ts`
- `frontend/src/features/monitoring/hooks/use-silences.ts`
- `frontend/src/app/(dashboard)/monitoring/alerts/[id]/page.tsx`
- `frontend/src/app/(dashboard)/monitoring/alerts/rules/[id]/page.tsx`
- `frontend/src/app/(dashboard)/monitoring/alerts/rules/new/page.tsx`
- `tests/e2e/monitoring/05_alerts_end_to_end.robot`
- `.paul/phases/13-monitoring/13-08c-SUMMARY.md` (this file)

Modified:
- `frontend/src/features/monitoring/hooks/use-alerts.ts` — added
  `startedAt` param on `useAlertEvent`; rewired `useSilenceFromEvent`
  to send full `SilenceCreateRequest` body and pass `?started_at=`
- `frontend/src/app/(dashboard)/monitoring/alerts/page.tsx` — swapped
  the inline table for `<AlertList />` composition
- `frontend/src/app/(dashboard)/monitoring/alerts/rules/page.tsx` —
  replaced inline rule-create modal with a table that links to
  `/rules/new` + `/rules/[id]` (editor page)

## Verification

- `npx tsc --noEmit` — 0 errors
- `npm run build` — success, all 9 new routes prerendered / server-rendered
- Robot E2E `tests/e2e/monitoring/05_alerts_end_to_end.robot` — **4 tests
  passed, 0 failed**

## Notes / carve-outs

- **Append-only `silenced` column** — existing firing event rows are not
  retroactively updated when a silence is created. The silence takes
  effect on the next evaluator cycle (suppresses Notify delivery). This
  is consistent with `evt_*` append-only convention. The E2E asserts
  silence creation via API rather than waiting for retroactive flag
  propagation. Pytest `test_silences_match.py` (13-08b) covers the
  evaluator's silence-enforcement path directly
- **Notify template picker** — deliberately implemented as a plain input
  (not a dropdown reading `GET /v1/notify/templates`) per the plan's
  "recommended path" to avoid blocking on notify template seeding
- **Hidden mirror select for severity** — the radio group UX is
  preserved for humans; a visually-hidden `<select>` with the same
  value wiring lets Robot's `Select Options By` keyword drive severity
  changes reliably in E2E
