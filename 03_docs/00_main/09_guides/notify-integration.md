# Notify Integration Guide — From Zero to First Notification

This guide walks a developer from an empty TennetCTL instance to sending their first transactional notification in under 10 minutes. Assumes you've already run `./scripts/setup` and the app is reachable on `http://localhost:51734`.

## Mental model

```
audit event  ─┐
              ├─► notify.worker ─► delivery row ─► email/webpush/in-app sender
subscription ─┘                     │
                                    ├─► evt_notify_delivery_events (open/click/bounce)
                                    └─► delivery status (queued → sent → delivered → opened)

Send API ─────────────────────────► delivery row (direct path; same downstream)
```

Everything lands in the unified `15_fct_notify_deliveries` table. In-app is automatic — every delivery (any channel) fans out an in-app copy so the bell icon always reflects what the user should see.

## Five minutes

### 1. Sign in to the dashboard
Visit `http://localhost:51735`, sign up, land on the Overview.

### 2. Configure an SMTP server (only needed for email)
Navigate to **Notify → Settings → SMTP Configs → + New SMTP**.

Example for Postmark:
- Key: `primary`
- Label: `Primary SMTP`
- Host: `smtp.postmarkapp.com`
- Port: `587`
- TLS: on
- Username: `<your-server-token>`
- Vault auth key: `notify.smtp.primary.password`
- From email: `notifications@yourdomain.com`
- From name: `Your App`

Then add the SMTP password as a vault secret under the key `notify.smtp.primary.password`.

Providers like SendGrid, Postmark, Mailgun use an API key as the SMTP username — this is why **From email** is a separate field.

### 3. Create a template group
**Notify → Settings → Template Groups → + New Group**.

- Key: `transactional`
- Label: `Transactional`
- Category: `Transactional`
- SMTP config: `primary` (for email-sending groups)

### 4. Create a template
**Notify → Templates → + New Template**.

- Key: `welcome-email`
- Group: `transactional`
- Subject: `Welcome, {{user_name}}!`
- Priority: Normal

Open the template, pick the **Email** tab, and author HTML + text. Variables like `{{user_name}}` are resolved at send-time from the `variables` payload.

Add per-channel bodies on the **Web Push** and **In-app** tabs if you want different wording on each surface.

### 5. Send your first notification

```bash
curl -X POST http://localhost:51734/v1/notify/send \
  -H "Authorization: Bearer nk_<your-api-key>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: $(uuidgen)" \
  -d '{
    "org_id": "<your-org-uuid>",
    "template_key": "welcome-email",
    "recipient_user_id": "<user-uuid-or-email>",
    "channel_code": "email",
    "variables": {"user_name": "Alice"},
    "deep_link": "/account"
  }'
```

Response:
```json
{"ok": true, "data": {"delivery_id": "019d...", "idempotent_replay": false, "scheduled_at": null}}
```

Within a few seconds the email sender picks it up, delivers it, and flips the delivery status to `sent` → `delivered`. When the recipient opens the email, pytracking flips it to `opened` (pixel) or `clicked` (link redirect).

## API keys + idempotency

Create an API key from **Account → API Keys** with scope `notify:send`. The raw token appears once — copy it.

Every transactional send should include an `Idempotency-Key` header. Repeat calls with the same key return the same `delivery_id` with `idempotent_replay: true`, never double-send.

## Subscriptions for event-driven notifications

Instead of polling to send notifications, subscribe to audit events:

**Notify → Settings → Subscriptions → + New Subscription**.

- Name: `New user welcome`
- Event key pattern: `iam.users.created`
- Template: `welcome-email`
- Channel: `email`
- Recipient mode: `actor` (the user who triggered the event, i.e., the new signup themselves)

When any audit event matches, the worker creates a delivery automatically. Use `users` or `roles` recipient modes to notify explicit users or everyone with a role code (e.g., `admin` role gets notified when a billing event fires).

## What to read next

- [Template authoring guide](./notify-template-authoring.md) — Jinja2, per-channel bodies, variables, fallback chain.
- [API reference](./notify-api-reference.md) — every endpoint with curl + TypeScript.
- [Deployment guide](./notify-deployment.md) — SMTP providers, DKIM/SPF/DMARC, webhook endpoints.
- [Examples](./notify-examples/) — worked recipes: password reset, order confirmation, daily digest.
