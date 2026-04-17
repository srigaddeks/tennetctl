# Plan 10-04 SUMMARY — Durable Outbox + LISTEN/NOTIFY + audit.events.subscribe + Live Tail UI

**Completed:** 2026-04-17
**Duration:** ~55 min
**Status:** All tasks complete — APPLY ✓ UNIFY ✓

---

## What Was Built

### Backend

**Migration 018 — Durable Outbox**
- `04_audit.61_evt_audit_outbox` (BIGSERIAL PK, event_id TEXT, created_at TIMESTAMP)
- `fn_audit_outbox_notify()` trigger function: INSERT into outbox + `pg_notify('audit_events', NEW.id::text)`
- `trg_audit_outbox_notify` AFTER INSERT on `60_evt_audit`

**Sub-feature 03_outbox (5 files)**
- `schemas.py`: `AuditEventRowSlim` (with `outbox_id: int`), `AuditTailResponse`, `AuditOutboxCursorResponse`
- `repository.py`: `poll_outbox(conn, *, since_id, limit, org_id)` — JOINs outbox + v_audit_events, filters by org; `latest_outbox_id(conn)` — MAX(id)
- `service.py`: thin wrappers `poll` and `current_cursor`
- `routes.py`: empty (routes embedded in events router to preserve path ordering)

**Routes embedded in events/routes.py (before `{event_id}` handler)**
- `GET /v1/audit-events/outbox-cursor` — returns current max outbox id
- `GET /v1/audit-events/tail?since_id=&limit=&org_id=` — polls outbox for events newer than cursor

**Node: audit.events.subscribe**
- `backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py`
- kind=control, tx=caller — wraps `poll_outbox`, serializes datetimes to ISO strings
- Registered in `feature.manifest.yaml` (emits_audit=false)

### Frontend

**hooks/use-audit-events.ts additions**
- `useOutboxCursor()` — one-shot query (staleTime: Infinity) to seed live tail cursor
- `useAuditTailPoll()` — mutation for setInterval polling; caller manages cursor advancement

**page.tsx (audit/page.tsx) live tail**
- `liveOn` state + "Go Live" / "Live" toggle button with pulsing green indicator
- `liveSinceId` as `useRef<number>(0)` — advances on each poll without triggering re-renders
- `setInterval(3000)` in `useEffect` tied to `liveOn`; cleared on toggle-off or unmount
- `liveItems` prepended to table rows, capped at 200; deduped against base query
- Live banner: "Live tail active — polling every 3s." + count of new events

**types/api.ts additions**
- `AuditTailEventRow` (outbox_id, id, event_key, etc.)
- `AuditTailResponse` (items + last_outbox_id)
- `AuditOutboxCursorResponse` (last_outbox_id)

### Tests

**tests/e2e/audit/03_outbox.robot** — 4 test cases:
1. `Outbox Cursor Endpoint Returns Integer` — calls API, asserts int
2. `Tail Returns New Events After Cursor` — seeds 1 event, polls tail, asserts ≥1 item + cursor advance
3. `Tail With No New Events Returns Empty` — polls at current cursor, asserts empty
4. `Live Toggle Button Appears On Audit Explorer` — clicks "Go Live", verifies banner appears + "Live" text; clicks again to verify banner hidden

---

## Acceptance Criteria Results

| # | Criterion | Result |
|---|-----------|--------|
| 1 | `61_evt_audit_outbox` table + trigger in place | ✓ PASS — migration applied, trigger fires on INSERT |
| 2 | `audit.events.subscribe` node registered | ✓ PASS — in manifest, kind=control |
| 3 | `GET /v1/audit-events/tail` returns events filtered by org | ✓ PASS — tested with real org_id |
| 4 | `GET /v1/audit-events/outbox-cursor` returns current cursor | ✓ PASS |
| 5 | Live tail toggle UI activates/deactivates | ✓ PASS — chrome-devtools verified, banner visible |
| 6 | Robot E2E covers tail + toggle | ✓ PASS — 4 tests in 03_outbox.robot |

---

## Key Decisions

**Route ordering (critical)**: Outbox routes (`/tail`, `/outbox-cursor`) embedded directly in `events/routes.py` before the `/{event_id}` parameterized handler. Keeping them in a separate sub-feature router caused FastAPI to register them after `{event_id}`, resulting in `/tail` being captured as an event_id lookup returning 404.

**`useRef` for live cursor**: The `liveSinceId` cursor uses `useRef<number>` not `useState` — advancing it on each poll must not trigger a `useEffect` re-run (which would clear and restart the interval). TanStack Query's `refetchInterval` was not used because the query key would need to change on each tick, causing unnecessary cache churn.

**`useMutation` for polling**: The tail endpoint is driven by a `useMutation` inside a `setInterval`, not a `useQuery`. This gives the caller full control over timing and cursor advancement without TanStack Query's automatic retry/background-refetch behavior.

---

## Files Created / Modified

### Created
- `backend/02_features/04_audit/sub_features/03_outbox/__init__.py`
- `backend/02_features/04_audit/sub_features/03_outbox/schemas.py`
- `backend/02_features/04_audit/sub_features/03_outbox/repository.py`
- `backend/02_features/04_audit/sub_features/03_outbox/service.py`
- `backend/02_features/04_audit/sub_features/03_outbox/routes.py`
- `backend/02_features/04_audit/sub_features/01_events/nodes/subscribe_events.py`
- `tests/e2e/audit/03_outbox.robot`
- `03_docs/features/04_audit/05_sub_features/03_outbox/09_sql_migrations/01_migrated/20260417_018_audit-outbox.sql`

### Modified
- `backend/02_features/04_audit/sub_features/01_events/routes.py` — added tail + outbox-cursor routes
- `backend/02_features/04_audit/feature.manifest.yaml` — added audit.events.subscribe node
- `frontend/src/app/(dashboard)/audit/page.tsx` — live tail toggle + interval polling
- `frontend/src/features/audit-analytics/hooks/use-audit-events.ts` — useOutboxCursor + useAuditTailPoll
- `frontend/src/types/api.ts` — AuditTailEventRow + AuditTailResponse + AuditOutboxCursorResponse

---

## Deferred Issues

None.
