# Example: Order Confirmation — Event-Driven Subscription

Different pattern: the user triggers a domain event (checkout), you want every relevant downstream — the user, the vendor, your ops Slack — to get notified. Instead of N `POST /v1/notify/send` calls from your checkout code, emit **one** audit event and let subscriptions fan it out.

## Your checkout service emits an audit event

```python
await run_node(
    pool, "audit.events.emit", ctx,
    {
        "event_key": "commerce.orders.created",
        "outcome": "success",
        "metadata": {
            "order_id": order["id"],
            "total_cents": order["total_cents"],
            "currency": order["currency"],
            "line_items": order["line_items"],  # list of {name, qty, price_cents}
        },
    },
)
```

`ctx.user_id` is the customer (the actor). `ctx.org_id` is the merchant org. Both are important for subscription routing.

## Three subscriptions, one event

### (1) Notify the customer
- **Event pattern:** `commerce.orders.created`
- **Template:** `order-confirmation-customer` (email)
- **Recipient mode:** `actor` — the user who checked out.

### (2) Notify the ops team
- **Event pattern:** `commerce.orders.created`
- **Template:** `order-confirmation-ops` (in-app — lands in their bell)
- **Recipient mode:** `roles`
- **Recipient filter:** `{"role_codes": ["ops", "cs"]}`

### (3) Notify the vendor (custom per-line-item)
If line items span multiple vendors, your app would emit one audit event per vendor (`commerce.orders.created.for_vendor`) and subscribe to that pattern with `recipient_mode=users` + a specific `user_ids` list resolved at emit time. More elaborate but keeps the fan-out logic in data, not code.

## Template variables

Templates can use **dynamic variables** resolved from `notify.template_variables`. Example: inline the user's display name from v_users using a safelisted query:

```sql
-- registered once under key "user_display_name"
SELECT display_name FROM "03_iam"."v_users" WHERE id = $recipient_user_id
```

Then reference it in the template body:

```html
Hi {{ user_display_name }},

Thanks for order #{{ event_metadata.order_id }}.
Total: {{ event_metadata.currency }} {{ (event_metadata.total_cents / 100) | round(2) }}.

{% for item in event_metadata.line_items %}
- {{ item.name }} × {{ item.qty }}
{% endfor %}
```

`event_metadata` is always available as a dict key carrying the audit event's metadata.

## Fallback chain for critical ops alerts

For the ops subscription, set the template's fallback_chain to email 5 minutes after the in-app if nobody opens it. A row of SQL on `12_fct_notify_templates`:

```sql
UPDATE "06_notify"."12_fct_notify_templates"
SET fallback_chain = '[{"channel_id": 1, "wait_seconds": 300}]'::jsonb
WHERE key = 'order-confirmation-ops';
```

When the audit event fires, the worker creates an in-app delivery now + an email delivery scheduled for 5 minutes later. If anyone on the ops team opens the in-app notification, the email is marked `superseded_by_primary` and never goes out.

## Analytics

After a few hours of live traffic, visit **Notify → Templates → order-confirmation-customer**. The Analytics strip shows total / sent / delivered / opened / clicked counts. Drill into `evt_notify_delivery_events` for raw event times.
