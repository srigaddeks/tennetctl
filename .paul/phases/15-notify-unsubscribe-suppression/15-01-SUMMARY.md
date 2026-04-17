# Plan 15-01 Summary — List-Unsubscribe + Suppression List

**Status:** COMPLETE
**Date:** 2026-04-17
**Phase:** 15 (Notify Production — Unsubscribe + Suppression)

## What Was Built

### DB (migration 039)
- `06_notify.17_fct_notify_suppressions` with CHECK on reason_code (`hard_bounce | complaint | manual | unsubscribe`), `UNIQUE(org_id, email)`, case-insensitive index on `(org_id, lower(email))`, `v_notify_suppressions` view.

### Backend
- New sub-feature `06_notify/sub_features/16_suppression/` (5 files):
  - `service.py` — HMAC-SHA256 signed unsubscribe tokens (`make_unsubscribe_token` / `parse_unsubscribe_token`), `_signing_key_bytes` bootstraps via `notify.unsubscribe.signing_key` vault secret (same pattern as magic-link). CRUD wrappers: `list_suppressions`, `add_suppression`, `remove_suppression`, `is_suppressed`.
  - `routes.py` — admin CRUD (`GET/POST/DELETE /v1/notify/suppressions`, session-required) + public `GET/POST /v1/notify/unsubscribe?token=...` (cookie-less, RFC 8058 one-click). GET returns minimal HTML confirmation; POST returns JSON envelope.
  - Router included in `06_notify/routes.py`.
- **Email sender** (`07_email/service._send_one`):
  - Suppression check short-circuits before SMTP: sets delivery `status=unsubscribed (9)` + `failure_reason=suppressed:<code>` with no aiosmtplib.send call.
  - Adds `List-Unsubscribe: <mailto:unsubscribe@DOMAIN>, <https://host/v1/notify/unsubscribe?token=...>` + `List-Unsubscribe-Post: List-Unsubscribe=One-Click` to every outbound MIME message. Token carries `org_id`, `email`, template `category_code`.
- **Bounce webhook** (`07_email/routes.bounce_webhook_route`): after marking delivery `status=bounced`, auto-inserts the recipient email into the suppression list with `reason_code='hard_bounce'` and the delivery_id.
- **Transactional Send** (`11_send/service.send_transactional`): when channel is email and recipient looks like an email, raises `ValidationError` if the address is suppressed.

### Tests
- Full regression: 242 passed (up from 240) — 2 new tests from earlier phases still green; no existing test broke.
- Note: monitoring module manifest validation is broken (pre-existing from Phase 13 work); ran tests with `TENNETCTL_MODULES` excluding monitoring. Manifest fix lives outside this plan's scope.

## Acceptance criteria — status

| AC | Status |
|---|---|
| AC-1: Suppression blocks subsequent sends | ✅ |
| AC-2: One-click unsubscribe GET/POST flip suppression | ✅ |
| AC-3: `List-Unsubscribe` + `List-Unsubscribe-Post` injected | ✅ |
| AC-4: Bounce webhook inserts into suppression list | ✅ |

## Deviations

- **Preference flip dropped.** The plan originally wanted the unsubscribe endpoint to also flip `is_opted_in=false` on preferences. But `upsert_preference` keys on `user_id`, and the unsubscribe token carries an email address (which may not map to any user). Suppression list is authoritative anyway — it skips before preferences — so we rely on it alone. Documented in the route comment.
- **No UI this pass.** Settings-page "Suppressions" section deferred; admin CRUD works via API immediately.

## Files modified

Backend (10): `06_notify/sub_features/16_suppression/*` (5 new), `06_notify/routes.py`, `06_notify/sub_features/07_email/service.py`, `06_notify/sub_features/07_email/routes.py`, `06_notify/sub_features/11_send/service.py`.

DB (1): migration `20260417_039_notify-suppressions.sql`.

## Follow-ups

- Monitoring manifest validation error blocks the full-stack boot until `monitoring.traces.otlp_ingest` is reclassified (pre-existing defect, not mine).
- Settings UI for suppression list (1 phase in a future docs pass).
