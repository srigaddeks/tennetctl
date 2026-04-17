# Example: Admin Broadcast — Role-Based Recipient Routing

Scenario: you want everyone with the `admin` role to get notified when a critical infra event fires (e.g., a SaaS subscription is nearing cancellation, an external API is throwing errors).

## The event

Your backend fires:

```python
await run_node(
    pool, "audit.events.emit", ctx,
    {
        "event_key": "ops.subscription.nearing_cancellation",
        "outcome": "success",
        "metadata": {
            "subscription_id": sub_id,
            "customer_name": customer_name,
            "days_until_churn": 3,
        },
    },
)
```

## Subscription

- **Event pattern:** `ops.subscription.nearing_cancellation`
- **Template:** `admin-churn-alert` (channel=email)
- **Recipient mode:** `roles`
- **Recipient filter:** `{"role_codes": ["admin", "owner"]}`

Worker behavior:
1. Reads the audit event's org_id.
2. Runs `SELECT DISTINCT user_id FROM "03_iam"."42_lnk_user_roles" WHERE org_id = $1 AND role_code = ANY($2)`.
3. For each resolved user, creates a delivery on email + in-app (always-on fan-out).
4. Each user's preferences are checked; anyone who opted out of the `transactional` category on email still gets in-app.

## Fallback for operators who miss emails

Admins live in the app. Email is backup. Use the fallback chain inverted — primary webpush, fallback email at 10 minutes:

```sql
UPDATE "06_notify"."12_fct_notify_templates"
SET fallback_chain = '[{"channel_id": 1, "wait_seconds": 600}]'::jsonb
WHERE key = 'admin-churn-alert';
```

And trigger with `channel_code: "webpush"` on the subscription. If the admin clicks the push notification (status → opened), the email never goes out.

## Preventing noise

Critical alerts should use `category: critical` on the template group so users can't opt out. But for nudge-level broadcasts (like this churn alert), keep the category as `transactional` so admins can mute themselves during PTO via their preferences page.

## Role resolution caveat

`recipient_filter.role_codes` resolves against `lnk_user_roles` at send time. Role grants/revokes take effect immediately — no cache invalidation needed.

If an admin role changes between event fire and delivery send, the delivery still goes to them (the worker resolves at event time). That's the correct semantics for notifications: the person with the role when the event happened should hear about it.

## Debugging: who actually got notified?

```sql
SELECT v.recipient_user_id, u.email, v.channel_code, v.status_code, v.created_at
FROM "06_notify"."v_notify_deliveries" v
JOIN "03_iam"."v_users" u ON u.id = v.recipient_user_id
WHERE v.org_id = $1
  AND v.subscription_id = $2
  AND v.created_at > NOW() - INTERVAL '1 hour'
ORDER BY v.created_at DESC;
```

Check `audit_outbox_id` to correlate the delivery with the triggering event; the audit explorer shows the metadata.
