# Example: Password Reset Email

Your app already has `POST /v1/auth/password-reset/request` wired to the notify system. This is how the pipeline ticks. Replicate the same pattern for any "user initiated a flow, now email them a signed link" scenario.

## Steps your app performs

1. User submits their email on `/auth/forgot-password`.
2. Your auth endpoint mints a signed HMAC token with 15-minute TTL.
3. Your auth endpoint calls `POST /v1/notify/send`:

```python
await run_node(
    pool, "notify.send.transactional", ctx,
    {
        "org_id": org_id,
        "template_key": "password-reset-email",
        "recipient_user_id": user["id"],  # or the email directly
        "channel_code": "email",
        "variables": {
            "user_name": user["display_name"],
            "reset_url": f"{app_base_url}/auth/password-reset?token={token}",
        },
        "deep_link": f"/auth/password-reset?token={token}",
    },
)
```

4. The notify worker renders the template, applies pytracking to the HTML, signs an unsubscribe token, and sends via SMTP.

## Template

**Key:** `password-reset-email`
**Group:** `transactional` (critical-enough that users shouldn't be able to opt out — consider making it `critical` category if you want always-delivered).
**Subject:** `Reset your {{ app_name | default("account") }} password`

**HTML body:**
```html
<p>Hi {{ user_name }},</p>
<p>We got a request to reset your password. Click the button below within 15 minutes.</p>
<p><a href="{{ reset_url }}"
      style="display:inline-block;padding:10px 18px;background:#111;color:#fff;text-decoration:none;border-radius:6px">
  Reset password
</a></p>
<p>Didn't ask for this? Ignore this email — your password won't change.</p>
<p>— The team</p>
```

**Text body:**
```
Hi {{ user_name }},

We got a request to reset your password. Open the link below within 15 minutes.

{{ reset_url }}

Didn't ask for this? Ignore this email — your password won't change.

— The team
```

## Idempotency

Double-clicks on "Send reset link" will double-send unless you pass `Idempotency-Key`. The built-in `iam.password_reset` service uses the token itself as the key:

```python
headers["Idempotency-Key"] = f"pw-reset-{token}"
```

Repeat submits within the same token lifetime share the same `delivery_id`.

## Deep link

The `deep_link` field is what the bell / push notification / email CTA should point to. Same URL in all surfaces keeps analytics coherent.

## What to watch for

- **Hard bounces**: the user's email is invalid / full. Our bounce webhook adds them to the suppression list automatically. Next time the user taps "Forgot password", the Send API will return 422 "suppressed" — gracefully surface that in your UI ("this email cannot receive notifications — contact support").
- **Complaint (spam reports)**: same handling — suppressed. If your open rates drop, check the provider's complaint rate first.
- **Template A/B testing**: outside the core. Build campaign logic in a separate app per the v0.1.7 charter.
