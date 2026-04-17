# Plan 16-01 Summary — Scheduled Sends

**Status:** COMPLETE (scoped down)
**Date:** 2026-04-17
**Phase:** 16 (Notify Production — Scheduled + Quiet Hours)

## What Was Built

### Backend
- `07_email/repository.poll_and_claim_email_deliveries`: added `AND (scheduled_at IS NULL OR scheduled_at <= CURRENT_TIMESTAMP)`.
- `08_webpush/repository.poll_and_claim_webpush_deliveries`: same filter.
- `06_deliveries/repository.create_delivery`: accepts `scheduled_at`; included in INSERT column list.
- `06_deliveries/service.create_delivery`: accepts + passes through `scheduled_at`. In-app auto-advance to `delivered` now gated on `scheduled_at is None or <= now` so future-scheduled in-app deliveries wait.
- `11_send/schemas.TransactionalSendRequest`: adds `send_at: datetime | None` + `delay_seconds: int | None (1..30d)`; `@model_validator(mode="after")` rejects both.
- `11_send/service.send_transactional`: accepts `scheduled_at`.
- `11_send/routes.send_transactional_route`: resolves `send_at | delay_seconds → scheduled_at` (naive UTC); returns `scheduled_at` in the response envelope.

### Frontend
- `/notify/send` form: new "Schedule for (optional)" `datetime-local` input; converts to ISO UTC for `send_at`.

### Tests — 4 new, all passing
- `test_send_at_stores_scheduled_at` — ISO roundtrip.
- `test_delay_seconds_produces_future_scheduled_at` — relative delay.
- `test_send_at_and_delay_both_supplied_rejects` — mutually exclusive → 422.
- `test_email_poll_skips_future_scheduled` — future delivery not claimed; flipped to past → claimed.

## Descoped
- **Quiet hours** (per-user timezone-aware silent windows).
- **Per-user timezone column** on iam users.

Both require a user-profile schema change + preferences UI for quiet windows. Tracked as a follow-up in the next minor (v0.1.8) alongside the "timezone on iam.users" schema work.

## Acceptance criteria — status

| AC | Status |
|---|---|
| AC-1: Future-scheduled not picked up | ✅ |
| AC-2: Picked up once scheduled_at passes | ✅ |
| AC-3: send_at / delay_seconds stored; both → 422 | ✅ |

## Files modified

Backend (7): `07_email/repository.py`, `08_webpush/repository.py`, `06_deliveries/{service,repository}.py`, `11_send/{schemas,service,routes}.py`.

Frontend (1): `notify/send/page.tsx`.

Tests (1 new): `tests/test_notify_send_scheduled.py`.
