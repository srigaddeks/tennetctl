---
phase: 11-notify
plan: 04
type: summary
status: complete
---

# Summary — Plan 11-04: Email Channel

## What Was Built

### `07_email` sub-feature (5 files)
- `schemas.py`: BounceWebhookPayload (delivery_id, reason)
- `repository.py`: `poll_and_claim_email_deliveries()` — atomic UPDATE with FOR UPDATE SKIP LOCKED, returns full view rows
- `service.py`:
  - `apply_email_tracking(html, delivery_id, base_url)` — pytracking adapt_html() adds open pixel + wraps links
  - `_get_recipient_email(conn, recipient_user_id)` — looks up `03_iam.v_users`; falls back to treating value as direct email if '@' present
  - `_send_one(conn, delivery, vault, base_tracking_url)` — render (jinja2 + pre-resolved vars from delivery) → track → build MIME → aiosmtplib.send → update status
  - `process_queued_email_deliveries(pool, vault, base_tracking_url, limit=10)` — poll + send loop, marks failed on exception
  - `start_email_sender(pool, vault, base_tracking_url)` → asyncio.Task (5s idle sleep, 10s+ error backoff)
- `routes.py`:
  - `GET /v1/notify/email/track/o/{token}` → pytracking decode → create 'open' event → return 1px transparent GIF
  - `GET /v1/notify/email/track/c/{token}` → pytracking decode → create 'click' event → 302 redirect to original URL
  - `POST /v1/notify/email/webhooks/bounce` → create 'bounce' event → update delivery status to bounced(7)

### Integration points
- `routes.py` updated: email router mounted
- `main.py` updated: email sender task started in lifespan (after vault init), cancelled on shutdown
- `feature.manifest.yaml` updated: sub-feature 7 (notify.email, number=7) with 3 routes

## Test Results

14/14 tests green (`tests/test_notify_email_channel.py`):
- Unit tests (2): tracking pixel in HTML, click link wrapping
- Service integration (5): sent status on success, failed status on SMTP error, direct email address as recipient, no smtp_config marks failed, non-email deliveries ignored
- Route integration (7): open tracking creates event, open tracking advances status to 'opened', click tracking 302 + event, invalid token returns GIF (graceful), bounce webhook sets bounced status, bounce webhook creates event, bounce 404 on unknown delivery

## Key Decisions Made

1. **`patch.object()` not `patch("path")`** — Python's `pkgutil.resolve_name` rejects module paths starting with digits (`02_features`). All mock patches must use `patch.object(module, 'attr')`.
2. **Background sender suppressed in tests** — `start_email_sender` patched to no-op in `live_app` fixture to prevent races between test and background worker.
3. **`FOR UPDATE SKIP LOCKED`** — Atomic claim prevents double-processing if multiple workers run.
4. **`@` fallback for recipients** — `recipient_user_id` treated as a direct email address if it contains `@`, making tests simple without needing full IAM user setup.
5. **Pre-resolved variables** — Delivery stores `resolved_variables` JSONB; email sender uses them directly via jinja2 without re-resolving dynamic SQL.

## Files Created/Modified

**Created:**
- `backend/02_features/06_notify/sub_features/07_email/__init__.py`
- `backend/02_features/06_notify/sub_features/07_email/schemas.py`
- `backend/02_features/06_notify/sub_features/07_email/repository.py`
- `backend/02_features/06_notify/sub_features/07_email/service.py`
- `backend/02_features/06_notify/sub_features/07_email/routes.py`
- `tests/test_notify_email_channel.py`

**Modified:**
- `backend/02_features/06_notify/routes.py` (mounted email router)
- `backend/02_features/06_notify/feature.manifest.yaml` (added sub-feature 7)
- `backend/main.py` (email sender task start/stop)
