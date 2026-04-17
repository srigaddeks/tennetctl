---
phase: 10-audit-analytics
plan: 02
subsystem: ui
tags: [tanstack-query, react, nextjs, robot-framework, playwright, audit]

requires:
  - phase: 10-01
    provides: audit query API (GET /v1/audit-events, /stats, /audit-event-keys), AuditEventRow types

provides:
  - Audit Explorer page at /audit with filter bar + cursor pagination + detail drawer + stats panel
  - useAuditEvents / useAuditEventDetail / useAuditEventStats / useAuditEventKeys hooks
  - Robot E2E 3/3 green covering navigate + filter + detail drawer
  - Chrome-devtools verified: no JS errors, full render confirmed

affects: [10-03, 10-04, notify-frontend, iam-frontend]

tech-stack:
  added: []
  patterns:
    - "Cursor-aware TanStack Query with accumulated pages (prev + new, dedup by id)"
    - "Fire-and-forget stats refetch via separate TanStack Query key"
    - "data-testid on TR via ...rest spread (HTMLAttributes) — strict-mode safe"
    - "Robot glob filter: * required for prefix match (exact match otherwise)"

key-files:
  created:
    - frontend/src/features/audit-analytics/hooks/use-audit-events.ts
    - frontend/src/features/audit-analytics/_components/filter-bar.tsx
    - frontend/src/features/audit-analytics/_components/events-table.tsx
    - frontend/src/features/audit-analytics/_components/event-detail-drawer.tsx
    - frontend/src/features/audit-analytics/_components/stats-panel.tsx
    - frontend/src/app/(dashboard)/audit/page.tsx
    - tests/e2e/audit/01_explorer.robot
    - tests/e2e/keywords/audit.resource
  modified:
    - frontend/src/config/features.ts
    - frontend/src/components/ui.tsx

key-decisions:
  - "TR component accepts ...rest HTMLAttributes — testid on <tr> not hidden <span>"
  - "Robot glob filter needs * suffix for prefix matching (backend LIKE only when * present)"
  - "Test seeds 12 events but org has auth events too — prefix filter isolates seeded set"

patterns-established:
  - "Robot audit tests filter by ${PREFIX}.evt* before asserting seeded counts"
  - "Open Audit Explorer includes Wait For Load State networkidle before assertions"
  - "Assert Totals Equals retries 15s with 500ms polling via Wait Until Keyword Succeeds"

duration: ~45min
started: 2026-04-16T12:00:00Z
completed: 2026-04-16T18:00:00Z
---

# Phase 10 Plan 02: Audit Explorer UI — Full Vertical

**PostHog-class Audit Explorer with filter bar, cursor-paginated events table, detail drawer, and stats mini-dashboard — Robot E2E 3/3 green, no JS errors.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~45min |
| Tasks | 3 completed |
| Files created | 8 |
| Files modified | 2 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Hooks wrap 4 endpoints | Pass | useAuditEvents (cursor), useAuditEventDetail, useAuditEventStats, useAuditEventKeys |
| AC-2: /audit page end-to-end | Pass | Filter bar + events table + stats panel + detail drawer all render |
| AC-3: Robot E2E 3+ green | Pass | 3/3: navigate+stats, glob filter, detail drawer |
| AC-4: Chrome-devtools verify | Pass | No JS errors; snapshot shows 36 events, filter bar, stats, time series |

## Accomplishments

- Audit Explorer page rivals PostHog event explorer: glob filter, multi-field filters, cursor pagination, category/outcome badges, detail drawer with pretty-printed JSON metadata and trace chip
- Stats mini-dashboard: totals by outcome, breakdown by category, top-8 event keys with bar chart, time-series bar chart
- Robot E2E seeds 12 events via raw SQL, signs in via UI, verifies filtering and detail drawer
- Zero JS console errors confirmed via chrome-devtools MCP

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `frontend/src/features/audit-analytics/hooks/use-audit-events.ts` | Created | TanStack Query hooks: list (cursor), detail, stats, keys |
| `frontend/src/features/audit-analytics/_components/filter-bar.tsx` | Created | Event key glob, category, outcome, actor, metadata, bucket filters |
| `frontend/src/features/audit-analytics/_components/events-table.tsx` | Created | Paginated events table with badges + relative time |
| `frontend/src/features/audit-analytics/_components/event-detail-drawer.tsx` | Created | Right drawer with all fields + pretty metadata + trace chip |
| `frontend/src/features/audit-analytics/_components/stats-panel.tsx` | Created | Totals/outcome/category panel + top event keys bar + time series |
| `frontend/src/app/(dashboard)/audit/page.tsx` | Created | Full page with filter state + cursor accumulation + drawer |
| `tests/e2e/audit/01_explorer.robot` | Created | 3 Robot test cases |
| `tests/e2e/keywords/audit.resource` | Created | Shared keywords: Open Explorer, Assert Totals, Seed SQL, Cleanup |
| `frontend/src/config/features.ts` | Modified | Added Audit nav entry (basePath=/audit, subFeature=Explorer) |
| `frontend/src/components/ui.tsx` | Modified | TR accepts ...rest HTMLAttributes for data-testid passthrough |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| TR accepts `...rest` HTMLAttributes | Browser library strict mode rejects duplicate selectors; testid must be on `<tr>` not a hidden child | Robot can select rows by `data-testid^="audit-row-"` |
| Robot prefix filter uses `${PREFIX}.evt*` not `${PREFIX}.evt` | Backend uses exact match unless `*` present; LIKE only enabled by glob wildcard | Glob filter tests work correctly |
| Test filters by prefix before asserting count=12 | Org accumulates auth events (signup, signin) alongside seeded events | Isolation without mocking |
| `Wait Until Keyword Succeeds 15s 500ms` for totals | Stats panel skeleton hides the total span; needs polling not one-shot check | Robust timing |

## Deviations from Plan

### Auto-fixed Issues

**1. Robot strict-mode: data-testid on hidden span**
- Found during: Task 2 (Robot E2E)
- Issue: `data-testid` was on a `<span class="hidden">` child; Browser library strict mode rejected
- Fix: Extended TR component to accept `...rest: HTMLAttributes<HTMLTableRowElement>`, put testid on `<tr>` directly
- Verification: Robot `css=tr[data-testid^="audit-row-"]` selects correctly

**2. Robot glob syntax: prefix must include `*`**
- Found during: Task 2 (Robot E2E — third run)
- Issue: Typing `${PREFIX}.evt` did exact match (0 results); needed `${PREFIX}.evt*` for LIKE
- Fix: Updated test to use `${PREFIX}.evt*` in first test, `${PREFIX}.evt.alpha` for second (exact)
- Verification: `Assert Totals Equals 12` and `Assert Totals Equals 4` both pass

**3. Robot timing: stats total 0 on first check**
- Found during: Task 2 (Robot E2E)
- Issue: `Wait For Elements State audit-stats-total visible 5s` succeeded on skeleton; value was stale
- Fix: Added `Wait For Load State networkidle` in Open Audit Explorer; `Wait Until Keyword Succeeds` for total polling
- Verification: 3/3 tests green consistently

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Badge tone "green" not in type | Changed to "emerald" (Badge type supports: zinc/emerald/red/blue/amber/purple) |
| Auth events in org inflate totals | Applied prefix glob filter in tests to isolate seeded events |

## Next Phase Readiness

**Ready:**
- Audit Explorer is a fully functional standalone UI — operators can filter, drill down, view metadata
- Robot keyword library (audit.resource) established as reusable for 10-03 tests
- Pattern established: seed SQL via DatabaseLibrary + glob filter isolation

**Concerns:**
- No saved views yet (10-03)
- No CSV export (10-03)
- No live-tail (deferred)

**Blockers:** None

---
*Phase: 10-audit-analytics, Plan: 02*
*Completed: 2026-04-16*
