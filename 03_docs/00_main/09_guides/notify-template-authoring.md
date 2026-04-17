# Template Authoring Guide

Templates are the rendering primitive. They have:

- A **subject** (string, Jinja2-templated) — becomes the email subject + the bell/push notification title.
- Per-channel **bodies** — `email` has HTML + text + preheader; `webpush` and `in_app` have text only.
- **Variables** resolved at send time (static overrides from the caller + dynamic variables from `13_fct_notify_template_variables`).
- An optional **fallback chain** — e.g. "try webpush, if not opened in 5 min, fall back to email".

## Jinja2 basics

Bodies use the Jinja2 engine in non-strict mode — unresolved variables render as empty strings (safer than blowing up at send).

```jinja
<h1>Hello, {{ user_name }}!</h1>

{% if order_total > 100 %}
<p>You got free shipping 🎉</p>
{% endif %}

<ul>
{% for item in line_items %}
  <li>{{ item.name }} — {{ item.qty }}× ${{ item.price }}</li>
{% endfor %}
</ul>

<a href="{{ deep_link }}">Track your order</a>
```

## Variable resolution order

The final variable dict merges three sources, in order:

1. **Dynamic variables** (`notify.template_variables`) — safelisted SQL queries parameterized by audit event metadata. Useful for enriching notifications with data the trigger event didn't carry.
2. **Template subject** → stamped as `subject` and `title` in the dict (if the caller didn't override).
3. **Per-call overrides** — the `variables` field on the Send API or the audit event metadata at the moment the worker fires.

Later sources win. If the caller passes `variables: {user_name: "Alice"}`, that beats any dynamic resolver.

## Per-channel bodies

The delivery pipeline picks the right body based on the channel at send-time:

| Channel | Uses | Falls back to |
|---|---|---|
| email | `body_html` + `body_text` | required (no fallback) |
| webpush | `body_text` | `resolved_variables.body` |
| in_app | `body_text` | `resolved_variables.body` or subject |

If you omit a channel's body, the worker fills in from `resolved_variables.{body, subject, title}` so users still see something reasonable.

## Preheader

Set it on the Email tab. The preheader shows in Gmail/iOS Mail preview lists alongside the subject. Short, descriptive:

```
Your receipt for Order #1234
```

## Fallback chain

Authored on the template (via API; UI is deferred). Persisted as JSONB on `12_fct_notify_templates.fallback_chain`:

```json
[
  {"channel_id": 1, "wait_seconds": 300}
]
```

Read as: "if the primary delivery isn't opened/clicked within 300 seconds, send a fallback on channel 1 (email)".

Behavior:
1. `send_transactional(channel=webpush)` → creates primary webpush delivery (immediate) + scheduled email delivery at `now + 300s`.
2. If the user opens the webpush before 5 minutes, the email delivery is marked `superseded_by_primary` when its turn comes — no email goes out.
3. If they don't, the email sender picks up the scheduled delivery at the scheduled time and sends normally.

## Deep linking

Every delivery carries a canonical `deep_link` URL. Pass it on the Send API (or set `url` in `resolved_variables`). Requirements:

- Must start with `/` (path-only). Absolute URLs and protocol-relative `//evil.com` are rejected as an open-redirect guard.
- Surfaces:
  - **In-app**: bell dropdown items are clickable → `router.push(deep_link)`.
  - **Web push**: the service worker's notificationclick handler navigates to it.
  - **Email**: include `{{ deep_link }}` in the HTML/text body wherever you want the CTA.

## Static + dynamic variables

Each template can declare typed variables in `13_fct_notify_template_variables`. Two kinds:

1. **Static** — a constant value that renders the same for every delivery (e.g., `"support_email": "help@acme.com"`).
2. **Dynamic** — a parameterized SQL snippet safelisted by the platform (e.g., `SELECT display_name FROM v_users WHERE id = $recipient_user_id`). The worker resolves them with values from the audit event.

Dynamic variables read from a strict allow-list of SQL templates — callers don't ship raw SQL. This keeps the system injection-safe while still letting templates pull in data the trigger event didn't carry.

## Testing a template

**Template editor → Test send** lets you send a one-off email to any address with a custom `variables` payload. Use for iterating on copy before wiring the real subscription.

## Checklist for a production-ready template

- [ ] Subject line is meaningful without needing the body (Gmail / Outlook preview).
- [ ] Preheader set.
- [ ] HTML body has a `<head>` with a `<title>` (matches subject).
- [ ] Plain-text body exists — spam filters punish HTML-only.
- [ ] Links are wrapped as `{{ deep_link }}` or absolute; avoid raw `localhost` URLs.
- [ ] `List-Unsubscribe` header — automatic, nothing to do from your side.
- [ ] Test-send to at least Gmail + iCloud + Outlook.
- [ ] If sending to Gmail at any volume, ensure DKIM + SPF + DMARC are set up (see [deployment guide](./notify-deployment.md)).
