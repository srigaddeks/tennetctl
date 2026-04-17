---
phase: 11-notify
plan: 05
type: summary
status: complete
---

# Summary — Plan 11-05: Web Push Channel

## What Was Built

### `08_webpush` sub-feature (5 files)
- `schemas.py`: `WebpushSubscriptionCreate`, `WebpushSubscriptionOut`, `VapidPublicKeyOut`
- `repository.py`:
  - `list_subscriptions(conn, *, user_id)` — active subs from view
  - `get_subscription(conn, *, sub_id)` — single active sub
  - `get_subscription_by_endpoint(conn, *, endpoint)` — lookup by endpoint
  - `upsert_subscription(conn, ...)` — `ON CONFLICT (endpoint) DO UPDATE` for browser key refresh
  - `soft_delete_subscription(conn, *, sub_id, updated_by)` — returns bool
  - `poll_and_claim_webpush_deliveries(conn, *, limit)` — `FOR UPDATE SKIP LOCKED`, channel_id=2
  - `get_user_webpush_subscriptions(conn, *, user_id)` — all active subs for sender
  - `mark_delivery_sent` / `mark_delivery_failed` — atomic status updates
- `service.py`:
  - `ensure_vapid_keys(pool, vault)` — idempotent bootstrap of `notify.vapid.private_key` + `notify.vapid.public_key` into vault
  - `_send_one(conn, delivery, vault)` — resolves subs for recipient, calls `pywebpush.webpush_async()` per subscription
  - `process_queued_webpush_deliveries(pool, vault, limit)` — poll + send loop
  - `start_webpush_sender(pool, vault)` → asyncio.Task (5s idle sleep, 10s error backoff)
- `routes.py`:
  - `GET /v1/notify/webpush/vapid-public-key` → 87-char base64url key from vault (public)
  - `GET /v1/notify/webpush/subscriptions` → list caller's active subs (auth required)
  - `POST /v1/notify/webpush/subscriptions` → upsert browser push subscription (auth required)
  - `DELETE /v1/notify/webpush/subscriptions/{sub_id}` → soft-delete (auth required)

### Migration 026
- `16_fct_notify_webpush_subscriptions` — endpoint (UNIQUE), p256dh, auth, device_label, user_id, org_id
- `v_notify_webpush_subscriptions` — active only (excludes deleted)

### Integration points
- `routes.py` updated: webpush router mounted
- `main.py` updated: `ensure_vapid_keys` called at startup; webpush sender task started/cancelled in lifespan
- `feature.manifest.yaml` updated: sub-feature 8 (notify.webpush, number=8) with 4 routes
- `test_notify_email_channel.py` updated: `live_app` fixture now patches `start_webpush_sender` to prevent races

## Test Results

14/14 tests green (`tests/test_notify_webpush_channel.py`):
- VAPID bootstrap (2): keys bootstrapped into vault; idempotent
- Service integration (5): sent status on success, failed on no-subscriptions, failed on WebPushException, sends to all user subs, non-webpush deliveries ignored
- Route/repo (7): VAPID public key endpoint, auth guard (list + create), create+list sub, upsert updates keys, soft-delete removes from view, delete nonexistent returns False

Email tests: 14/14 still green (no regression).

## Key Decisions Made

1. **`patch.object(pywebpush, "webpush_async", ...)` works for in-function imports** — `from pywebpush import webpush_async` inside `_send_one` re-looks up the attribute on the module object each call, so patching the module attribute intercepts it.
2. **VAPID private key stored as PEM in vault** — `py_vapid.Vapid().from_pem()` can reload it; `webpush_async` accepts PEM string directly as `vapid_private_key`.
3. **`webpush_async` (convenience function) preferred over `WebPusher.send_async`** — derives `aud` claim automatically from endpoint URL; simpler call site.
4. **Endpoint UNIQUE constraint enables browser key refresh** — browser re-registers same endpoint with new p256dh/auth after expiry; `ON CONFLICT (endpoint) DO UPDATE` handles this without creating duplicates.
5. **Sender patches in email `live_app` updated** — `start_webpush_sender` now patched to no-op in email tests to prevent cross-test interference.

## Files Created/Modified

**Created:**
- `03_docs/.../08_webpush/09_sql_migrations/02_in_progress/20260417_026_notify-webpush-subscriptions.sql` (migrated to 01_migrated/)
- `backend/02_features/06_notify/sub_features/08_webpush/__init__.py`
- `backend/02_features/06_notify/sub_features/08_webpush/schemas.py`
- `backend/02_features/06_notify/sub_features/08_webpush/repository.py`
- `backend/02_features/06_notify/sub_features/08_webpush/service.py`
- `backend/02_features/06_notify/sub_features/08_webpush/routes.py`
- `tests/test_notify_webpush_channel.py`

**Modified:**
- `backend/02_features/06_notify/routes.py` (mounted webpush router)
- `backend/02_features/06_notify/feature.manifest.yaml` (added sub-feature 8)
- `backend/main.py` (VAPID bootstrap + webpush sender start/stop)
- `tests/test_notify_email_channel.py` (live_app patches start_webpush_sender)
