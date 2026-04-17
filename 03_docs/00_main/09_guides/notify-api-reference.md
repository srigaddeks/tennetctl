# Notify API Reference

All endpoints return the standard envelope:

```json
{"ok": true, "data": {...}}
{"ok": false, "error": {"code": "CODE", "message": "..."}}
```

Auth: session cookie (`tennetctl_session`) OR API key (`Authorization: Bearer nk_<key_id>.<secret>`). Scopes enforced only where noted.

Base URL: `http://<host>:51734` (default dev port).

## Transactional Send

### `POST /v1/notify/send`
Scope: `notify:send`.

Create a delivery for an already-defined template. Best for ad-hoc sends like magic links, password resets, receipts, OTPs — anything not driven by the subscription/audit-event pipeline.

**Request body**
```json
{
  "org_id": "019d...",
  "template_key": "welcome-email",
  "recipient_user_id": "019d... or alice@example.com",
  "channel_code": "email",
  "variables": {"user_name": "Alice"},
  "deep_link": "/account",
  "send_at": "2026-05-01T12:00:00Z",
  "delay_seconds": null
}
```

- `channel_code` — `"email" | "webpush" | "in_app"`. SMS is intentionally rejected.
- `variables` — merged into the template's resolved variables (overrides).
- `deep_link` — path-only URL the notification navigates to.
- `send_at` / `delay_seconds` — mutually exclusive. Leave both null for immediate.

**Headers**
- `Idempotency-Key: <uuid>` — optional but strongly recommended. Repeat requests with the same key return the same delivery.
- `Authorization: Bearer nk_...` — API key; required scope `notify:send`.

**Response 201**
```json
{"ok": true, "data": {"delivery_id": "019d...", "idempotent_replay": false, "scheduled_at": null}}
```

**Errors**
- `422` — validation (bad channel, both `send_at` and `delay_seconds`, suppressed recipient).
- `404` — template not found for that org.
- `403` — API key missing `notify:send` scope.
- `401` — no auth.

```bash
curl -sS -X POST http://localhost:51734/v1/notify/send \
  -H "Authorization: Bearer $NOTIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d @body.json
```

```typescript
const res = await fetch("/v1/notify/send", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.NOTIFY_TOKEN}`,
    "Content-Type": "application/json",
    "Idempotency-Key": crypto.randomUUID(),
  },
  body: JSON.stringify({ org_id, template_key, recipient_user_id, channel_code, variables }),
});
const { ok, data } = await res.json();
if (!ok) throw new Error("send failed");
```

## Deliveries

### `GET /v1/notify/deliveries?org_id=X[&recipient_user_id=Y][&channel=email|webpush|in_app][&status=CODE][&limit=50][&offset=0]`
Scope: `notify:read` (session users bypass).

Returns deliveries across channels. Each row includes `deep_link`, `idempotency_key`, `scheduled_at`, `attempt_count`, `next_retry_at`, `failure_reason`, etc.

### `GET /v1/notify/deliveries/{delivery_id}`
Single delivery.

### `GET /v1/notify/unread-count?org_id=X&recipient_user_id=Y`
Server-computed unread count. Cheap for the bell badge.

### `PATCH /v1/notify/deliveries/{delivery_id}`
Mark any channel's delivery as read (i.e., `status=opened`). Caller must be the `recipient_user_id`.
```json
{"status": "opened"}
```

## Templates

### `GET /v1/notify/templates?org_id=X` / `POST` / `PATCH {id}` / `DELETE {id}`
Standard CRUD.

### `PUT /v1/notify/templates/{id}/bodies`
Upsert per-channel bodies. Body is an array of `{channel_id, body_html, body_text, preheader}`.

### `POST /v1/notify/templates/{id}/test-send`
Send a one-off test email.

### `GET /v1/notify/templates/{id}/analytics`
Per-template aggregate counts.

Response:
```json
{"ok": true, "data": {
  "by_status":     {"sent": 123, "delivered": 120, "opened": 88, "clicked": 32, "failed": 3},
  "by_event_type": {"open": 88, "click": 32, "bounce": 3},
  "total_deliveries": 123
}}
```

## Template groups & SMTP configs

Standard CRUD:
- `GET/POST/DELETE /v1/notify/template-groups`
- `GET/POST/PATCH/DELETE /v1/notify/smtp-configs`

Template group binds templates to one SMTP config. Each group has a `category` (`transactional | critical | marketing | digest`) that gates user preferences.

## Subscriptions

### `GET/POST/DELETE /v1/notify/subscriptions`

Trigger rules: audit event match → fan out. Subscription fields:
- `name`
- `event_key_pattern` — glob like `iam.users.*` or exact `iam.users.created`.
- `template_id` + `channel_id` — primary channel.
- `recipient_mode` — `actor | users | roles`.
- `recipient_filter` — `{}` (for `actor`), `{user_ids: [...]}` (for `users`), or `{role_codes: [...]}` (for `roles`).

The worker resolves recipients, respects user preferences, respects the suppression list, and always fans out to in-app in addition to the primary channel.

## User preferences

### `GET/PUT /v1/notify/preferences?org_id=X&user_id=Y`
Grid of per-`(channel, category)` opt-in toggles. `critical` category is locked on — users cannot opt out of security alerts.

## Suppression list (RFC 8058)

### `GET/POST/DELETE /v1/notify/suppressions`
Admin CRUD (session-auth).

### `GET /v1/notify/unsubscribe?token=...`
Cookie-less HTML confirmation page. Linked from every outbound email's `List-Unsubscribe` header.

### `POST /v1/notify/unsubscribe`
Cookie-less JSON endpoint for RFC 8058 one-click (`List-Unsubscribe-Post: List-Unsubscribe=One-Click`).

## Webhooks (inbound)

### `POST /v1/notify/email/webhooks/bounce`
From your SMTP provider. Body: `{delivery_id, reason}`. Marks delivery bounced + adds recipient email to the suppression list with `reason_code=hard_bounce`.

## Email tracking (for HTML email clients)

- `GET /v1/notify/email/track/o/{token}` — 1px pixel. First load → `status=opened` + event row.
- `GET /v1/notify/email/track/c/{token}?url=...` — click redirect. 302 to the original URL + `status=clicked` + event row.

Tokens are pytracking-encoded `{delivery_id}`. No auth needed.

## WebPush

- `GET /v1/notify/webpush/vapid-public-key` — public endpoint, returns base64url VAPID public key.
- `GET/POST/DELETE /v1/notify/webpush/subscriptions` — session-auth; register browser push subscriptions.

## API key management

### `GET/POST/DELETE /v1/api-keys`
Session-only. Create a scoped key; the raw token appears once in the response.

Scopes:
- `notify:send` — `POST /v1/notify/send`.
- `notify:read` — read-only endpoints.
- `audit:read` — reserved for audit.

## Rate limits

Not enforced in v0.1.7. Delivery senders poll every 5s with per-email retry backoff (60s, 120s, 240s …) — the app won't self-DoS your SMTP provider at low volume.

## OpenAPI spec

FastAPI auto-generates `/openapi.json` and `/docs`. Point your Postman/httpie/Stoplight at those for an always-up-to-date schema.
