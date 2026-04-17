---
phase: 11-notify
plan: 03
type: summary
status: complete
---

# Summary — Plan 11-03: Subscriptions + Audit-Outbox Consumer + Critical Fan-Out

## What Was Built

### Migration 024 — Subscriptions + Deliveries + Delivery Events
- `14_fct_notify_subscriptions`: event_key_pattern → template + channel mapping per org
- `15_fct_notify_deliveries`: delivery queue with status lifecycle (queued → sent → delivered)
- `61_evt_notify_delivery_events`: append-only tracking (open/click/bounce/unsubscribe/spam_report)
- Views: `v_notify_subscriptions`, `v_notify_deliveries`, `v_notify_delivery_events`

### Migration 025 — Delivery Idempotency Constraint
- `UNIQUE INDEX uq_notify_deliveries_sub_outbox ON (subscription_id, audit_outbox_id, channel_id)`
- Partial: `WHERE subscription_id IS NOT NULL AND audit_outbox_id IS NOT NULL`
- `channel_id` included so critical fan-out (3 channels) isn't blocked by the constraint

### 05_subscriptions sub-feature (full CRUD)
- `matches_pattern(event_key, pattern)` — pure Python: exact / prefix.* / *
- CRUD at `/v1/notify/subscriptions` + `/{sub_id}`
- `list_active_for_worker(conn)` — cross-org read for background worker

### 06_deliveries sub-feature (read-only API)
- `GET /v1/notify/deliveries` with filters: org_id, status_code, channel_code, recipient_user_id
- `GET /v1/notify/deliveries/{delivery_id}`
- `create_delivery` → `ON CONFLICT (subscription_id, audit_outbox_id, channel_id) ... DO NOTHING` (idempotent)
- `update_delivery_status` — for channel workers (Plans 11-04/05/06)

### Worker (background asyncio task)
- `process_audit_events(pool, since_id)` — poll outbox → match subscriptions → enqueue deliveries
- `_CRITICAL_CHANNELS = [1, 2, 3]` (email, webpush, in_app)
- Critical fan-out: category_code == "critical" → deliveries for all 3 channels, not just subscription's channel
- LISTEN on `'audit_events'` NOTIFY channel + 30s fallback poll
- Cursor starts at latest outbox ID on boot (no historical replay)
- Worker started in `main.py` lifespan; cancelled on shutdown

### Manifest + Routes
- `feature.manifest.yaml` updated: sub-features 5 (subscriptions) + 6 (deliveries) with routes
- `routes.py` mounts both sub-feature routers

## Test Results

21/21 tests green (`tests/test_notify_subscriptions_api.py`):
- Pattern matching (5): exact, suffix wildcard, deep wildcard, global wildcard, no-match
- Subscription CRUD (6): create, list empty, list with items, get, update, delete
- Worker delivery creation (5): matching event, different org (no delivery), pattern mismatch (no delivery), critical fan-out (3 deliveries), resolved variables stored
- Delivery API (3): list empty, list after worker, get one
- Schema validation (2): invalid pattern, missing required fields

## Key Decisions Made

1. **3-column unique index** — initial migration used (subscription_id, audit_outbox_id). Manually corrected to (subscription_id, audit_outbox_id, channel_id) because critical fan-out shares same sub+outbox pair across 3 channels.
2. **Worker cursor starts at latest** — not at 0; avoids replaying historical events on startup.
3. **Worker races handled by unique index** — background worker + direct `process_audit_events()` test call both fire; `ON CONFLICT DO NOTHING` prevents duplicates without locking.
4. **recipient_user_id from actor_user_id** — audit event's actor is the delivery recipient for subscription-driven notifications.

## Files Created/Modified

**Created:**
- `03_docs/features/06_notify/05_sub_features/05_subscriptions/09_sql_migrations/02_in_progress/20260417_024_notify-subscriptions-deliveries.sql` (→ moved to 01_migrated)
- `03_docs/features/06_notify/05_sub_features/06_deliveries/09_sql_migrations/01_migrated/20260417_025_notify-deliveries-idempotency.sql`
- `backend/02_features/06_notify/sub_features/05_subscriptions/__init__.py`
- `backend/02_features/06_notify/sub_features/05_subscriptions/schemas.py`
- `backend/02_features/06_notify/sub_features/05_subscriptions/repository.py`
- `backend/02_features/06_notify/sub_features/05_subscriptions/service.py`
- `backend/02_features/06_notify/sub_features/05_subscriptions/routes.py`
- `backend/02_features/06_notify/sub_features/06_deliveries/__init__.py`
- `backend/02_features/06_notify/sub_features/06_deliveries/schemas.py`
- `backend/02_features/06_notify/sub_features/06_deliveries/repository.py`
- `backend/02_features/06_notify/sub_features/06_deliveries/service.py`
- `backend/02_features/06_notify/sub_features/06_deliveries/routes.py`
- `backend/02_features/06_notify/worker.py`
- `tests/test_notify_subscriptions_api.py`

**Modified:**
- `backend/02_features/06_notify/routes.py` (added subscriptions + deliveries routers)
- `backend/02_features/06_notify/feature.manifest.yaml` (added sub-features 5 + 6)
- `backend/main.py` (worker start/stop in lifespan)
