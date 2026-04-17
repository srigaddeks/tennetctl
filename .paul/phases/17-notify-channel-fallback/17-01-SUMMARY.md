# Plan 17-01 Summary — Channel Fallback

**Status:** COMPLETE
**Date:** 2026-04-17

## What Was Built

### DB (migration 040)
- `12_fct_notify_templates.fallback_chain JSONB NOT NULL DEFAULT '[]'`.
- `v_notify_templates` recreated with `fallback_chain` in SELECT.

### Backend
- `03_templates/repository.py` — SELECT includes `fallback_chain`; `_row_to_dict` parses JSONB to Python list; defaults to `[]`.
- `11_send/service.send_transactional` — after creating the primary delivery, iterates `template.fallback_chain` and creates a scheduled delivery per step (skipping steps whose `channel_id` equals the primary). Idempotency key gets `-fb{channel_id}` suffix for uniqueness.
- `07_email/service._send_one` + `08_webpush/service._send_one` — before send, check for a sibling delivery on `(org_id, template_id, recipient_user_id)` with `status IN ('opened','clicked')`. If found, mark self `status=unsubscribed` with `failure_reason='superseded_by_primary'` and return.

### Tests — 2 new, all green
- `test_send_creates_primary_and_scheduled_fallback` — template with email fallback on in-app primary → 2 rows (in-app immediate, email scheduled).
- `test_fallback_skipped_when_primary_opened` — primary marked opened; email sender polls the fallback with scheduled_at in past; `aiosmtplib.send` never called; row status flips to `unsubscribed` with `superseded_by_primary` reason.

## Acceptance criteria

| AC | Status |
|---|---|
| AC-1: Fallback chain column persists | ✅ |
| AC-2: Send creates primary + scheduled fallback | ✅ |
| AC-3: Sender skips superseded fallback | ✅ |

## Not in scope
- Template editor UI for fallback_chain (deferred to template-editor polish pass).
- Subscription-worker fallback (only transactional Send for now).
- Automatic fallback on a *failed* primary (superseded means primary succeeded; truly-failed primary needs a different signal).

## Files modified

Backend (4): `03_templates/repository.py`, `11_send/service.py`, `07_email/service.py`, `08_webpush/service.py`.

DB (1): migration 040.

Tests (1 new): `test_notify_channel_fallback.py`.
