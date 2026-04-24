# Notify Integration

> Every customer-facing or operator-facing notification somaerp sends goes through tennetctl 06_notify. somaerp owns templates, triggers, and recipient resolution — never delivery.

## What somaerp uses notify for

Two audiences, two registers:

- **Customers** — Soma Delights subscribers. Friendly, brand-voice, multi-lingual (Telugu / Hindi / English per `multi-lingual-strategy.md`).
- **Operators** — the people running the tenant. Functional, alert-style, action-oriented.

The same notify primitive serves both. Templates are tagged with audience.

## Use cases (Soma Delights, by lifecycle)

### Customer-facing

| Event | Trigger | Channel | Template key | Category |
| --- | --- | --- | --- | --- |
| Welcome on signup | `somaerp.customers.subscriptions.created` | WhatsApp + email | `somaerp.customer.subscription.welcomed` | operational |
| Subscription pause confirmation | `somaerp.customers.subscriptions.paused` | WhatsApp | `somaerp.customer.subscription.paused` | operational |
| Subscription resumed | state→active after pause | WhatsApp | `somaerp.customer.subscription.resumed` | operational |
| Delivery dispatched (your juice is on the way) | `somaerp.delivery.runs.dispatched` (per stop) | WhatsApp | `somaerp.customer.delivery.dispatched` | operational |
| Delivery completed (photo of bag at door) | `somaerp.delivery.stops.recorded` | WhatsApp | `somaerp.customer.delivery.delivered` | operational |
| Delivery delayed | conditional on dispatched > 15min late | WhatsApp | `somaerp.customer.delivery.delayed` | operational |
| Quality issue (your bottle today did not meet our standard) | `somaerp.production.batches.qc_failed` (proactive replacement message) | WhatsApp | `somaerp.customer.quality.batch_replaced` | operational |
| Plan change confirmation | `somaerp.customers.subscriptions.state_changed` | WhatsApp | `somaerp.customer.subscription.changed` | operational |
| Payment receipt (when billing ships) | future | email | `somaerp.customer.billing.receipt` | operational |
| Wellness tip / weekly content | broadcast (operator-triggered) | WhatsApp | `somaerp.customer.tip.weekly` | promotional (opt-in) |
| Privacy/DPDP notice | `somaerp.customers.consent.recorded` | email | `somaerp.customer.privacy.notice` | privacy |
| DSAR fulfillment | `somaerp.customers.dsar.exported` | email | `somaerp.customer.dsar.delivered` | privacy |

### Operator-facing

| Event | Trigger | Channel | Template key | Category |
| --- | --- | --- | --- | --- |
| Today's production list (4 AM) | scheduled job | email | `somaerp.operator.production.daily_list` | operational |
| Batch completion summary | `somaerp.production.batches.completed` | email | `somaerp.operator.production.batch_completed` | operational |
| QC failure alert | `somaerp.production.batches.qc_failed` | email + push | `somaerp.operator.qc.batch_failed` | critical |
| Cold-chain breach | delivery stop with temp > 12°C | email + push | `somaerp.operator.delivery.cold_chain_breach` | critical |
| FSSAI license expiry warning (30/14/7 days) | scheduled check on `somaerp.tenants.{ws}.fssai_license_expiry` | email | `somaerp.operator.compliance.fssai_expiring` | critical |
| FSSAI compliance breach (e.g. failed QC on delivered batch) | `somaerp.production.batches.qc_failed` AND batch already dispatched | email | `somaerp.operator.compliance.breach` | critical |
| Low inventory warning | `evt_inventory_movements` aggregate dropped below threshold | email | `somaerp.operator.inventory.low_stock` | operational |
| Procurement reminder (next 3 days due) | scheduled job reading projected demand | email | `somaerp.operator.procurement.reminder` | operational |
| Delivery rider not started by 6:00 AM | scheduled check | push | `somaerp.operator.delivery.rider_late` | critical |
| New customer signup | `somaerp.customers.created` | email | `somaerp.operator.customers.new_signup` | operational |
| Daily reconciliation summary (8 PM) | scheduled job | email | `somaerp.operator.daily.reconciliation` | operational |
| Weekly review report (Sunday 8 PM) | scheduled job | email | `somaerp.operator.weekly.review` | operational |

## Template registration — `somaerp.{audience}.{topic}.{event}` namespace

All keys are namespaced under `somaerp.`. Templates are registered in tennetctl notify at boot via:

```text
client.notify_register_template(
    key="somaerp.customer.delivery.dispatched",
    audience="customer",
    channel="whatsapp",
    locales=["en", "hi", "te"],
    body_template="<localized template body, see multi-lingual-strategy.md>",
    category="operational",
)
```

Boot-time template registration is idempotent. Registering an already-registered template with identical content is a no-op; with changed content, it bumps the template version (tennetctl notify owns versioning).

### Locales

Per `multi-lingual-strategy.md`, customer-facing templates ship in three locales at v0.9.0:

- `en` — English (default)
- `hi` — Hindi
- `te` — Telugu

Operator-facing templates ship in `en` only at v0.9.0; multi-lingual operator UX is deferred.

The recipient locale is resolved from `fct_customers.preferred_language` (per `08_customers` data layer, forward reference). The default is `en` if unset. Templates that fail to resolve a locale fall back to `en`.

### Category mapping to notify primitives

`category=critical` triggers tennetctl notify's high-priority path:
- Multiple-channel delivery (email + push)
- Retry on failure (up to 5 attempts with exponential backoff)
- Operator escalation if not acknowledged within configured window

`category=operational` is the default — single-channel, single-attempt, no escalation.

`category=promotional` requires opt-in. somaerp checks `fct_customers.properties.opted_in_to_tips` before emitting; per `customer-data-privacy.md` § 8.

`category=privacy` is single-channel email, audited under `category=privacy` per `02_audit_emission.md`.

## How somaerp triggers a notification

Service layer pseudocode:

```text
service.dispatch_delivery_run(conn, ctx, run_id):
    run = await repo.get_delivery_run(conn, run_id, ctx.workspace_id)
    stops = await repo.list_stops(conn, run_id, ctx.workspace_id)
    for stop in stops:
        customer = await repo.get_customer(conn, stop.customer_id, ctx.workspace_id)
        await client.notify_send({
            "template_key": "somaerp.customer.delivery.dispatched",
            "recipient": {"channel": "whatsapp", "address": customer.whatsapp_number},
            "locale": customer.preferred_language or "en",
            "context": {
                "customer_name": customer.name,
                "estimated_arrival": stop.estimated_arrival_iso,
                "rider_name": run.rider_name,
            },
            "workspace_id": ctx.workspace_id,
            "audit_correlation_id": str(stop.id),
        })
    await client.emit_audit(
        event_key="somaerp.delivery.runs.dispatched",
        outcome="success",
        metadata={"run_id": str(run_id), "stops": len(stops), ...},
        actor_user_id=ctx.user_id, org_id=ctx.org_id, workspace_id=ctx.workspace_id,
    )
```

`notify_send` failure does NOT block the parent mutation. Like audit, notify is best-effort with retry (tennetctl side). A failed send emits its own audit row at category=`operational` with `outcome=failure`.

## Channels

v0.9.0 channels supported through tennetctl notify (no external SaaS providers — the empire thesis prohibits any third-party transactional-email or SMS service):

| Channel | Backed by | Notes |
| --- | --- | --- |
| `email` | tennetctl SMTP relay (operator-configured, optionally per-tenant via vault) | Always available |
| `whatsapp` | Direct WhatsApp Business Cloud API integration owned by tennetctl notify (or future) — at v0.9.0 may be a stub that operators fulfill manually for the first cohort | The Soma Delights launch may run this manually for the first weeks per `customer-data-privacy.md` (operator copies the message into WhatsApp Business app) until the integration ships |
| `push` | Tennetctl operator dashboard push (in-app browser push) | Operator-only |
| `sms` | Deferred to v1.0; needs a self-hosted gateway | Out of v0.9.0 |

The "WhatsApp via Cloud API" path is a tennetctl notify implementation concern, not somaerp's. somaerp emits the template; tennetctl chooses how to deliver it.

## Recipient resolution

For customer notifications, somaerp resolves the recipient channel address from `fct_customers`:

- `whatsapp` channel: `fct_customers.whatsapp_number` (if set)
- `email` channel: `fct_customers.email` (if set)

For operator notifications, somaerp resolves the recipient(s) from tennetctl iam role membership:

- "all users with `somaerp.qc.read` in this workspace" — for QC failure alerts
- "all users with `somaerp.production.write`" — for production daily list
- "the user with `somaerp.admin`" — for FSSAI license expiry

Resolution is via `client.list_workspace_role_members(role_key, workspace_id)` (a tennetctl iam read). Per `01_auth_iam_consumption.md`.

## Opt-in and opt-out

Per `customer-data-privacy.md` § 8, customers can opt out of `category=promotional` messages by replying STOP. somaerp:

1. Records the opt-out as `somaerp.customers.consent.recorded` audit event with `category=privacy`, metadata `{"opted_in_to_tips": false}`.
2. Updates `fct_customers.properties.opted_in_to_tips = false`.
3. Future promotional sends check this flag and skip.

Operational and privacy categories cannot be opted out of (they are required for service delivery and legal compliance).

## What somaerp does NOT do

- Never sends email/SMS/WhatsApp directly. No `smtplib` import. No vendor SDK. Always via `client.notify_send`.
- Never stores recipient channel addresses redundantly. The `fct_customers` row is the only source.
- Never schedules its own retries. Notify retries are a tennetctl notify concern.
- Never templates inline with f-strings. All templates are registered with tennetctl notify at boot; the service layer passes context.

## Critical-category for FSSAI breaches

`compliance-food-safety.md` lists FSSAI breaches that demand immediate operator action:
- A delivered batch later failed QC (cold-chain breach detected post-dispatch).
- An ingredient lot was found contaminated AFTER consumption.
- The FSSAI license expired and production continued.

Each emits a `category=critical` notification to all `somaerp.admin` and `somaerp.qc.sign_off` role members in the workspace. The notification body is action-oriented:
- What happened (lot/batch/customer ID).
- What action is required.
- Who else has been notified.
- Link to the relevant somaerp UI screen.

## Related documents

- `00_tennetctl_proxy_pattern.md` — `notify_send` signature
- `01_auth_iam_consumption.md` — role-based recipient resolution
- `02_audit_emission.md` — every notify trigger emits its own audit row
- `03_vault_for_secrets_and_blobs.md` — per-tenant SMTP credentials in vault
- `../01_data_model/08_customers.md` (forward reference — Task 2) — `preferred_language`, `opted_in_to_tips`
- `99_business_refs/somadelights/09-execution/multi-lingual-strategy.md`
- `99_business_refs/somadelights/09-execution/customer-data-privacy.md`
- `99_business_refs/somadelights/09-execution/compliance-food-safety.md`
