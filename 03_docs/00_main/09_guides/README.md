# Developer Guides

Integration docs aimed at developers building real business apps on TennetCTL.

## Notify (multi-channel notifications)

Start here to wire notifications into your app:

- **[Integration Guide](./notify-integration.md)** — zero → first notification in 10 minutes.
- **[Template Authoring](./notify-template-authoring.md)** — Jinja2, per-channel bodies, variables, fallback chain, deep linking.
- **[API Reference](./notify-api-reference.md)** — every endpoint with curl + TypeScript examples.
- **[Deployment](./notify-deployment.md)** — SMTP providers (Postmark / SendGrid / Mailgun / SES), DKIM / SPF / DMARC, suppression list, webhooks.

### Worked examples

- **[Password reset email](./notify-examples/password-reset.md)** — transactional Send with idempotency key, signed URL deep-link.
- **[Order confirmation](./notify-examples/order-confirmation.md)** — audit-event-driven subscription fan-out to customer + ops + vendor.
- **[Admin broadcast](./notify-examples/admin-broadcast.md)** — role-based recipient resolution for ops alerts.

## Beyond notify

- See [03_rules.md](../03_rules.md) for project-wide conventions.
- See [07_adding_a_feature.md](../07_adding_a_feature.md) for the feature-vertical pattern every new module follows.
- Architecture Decision Records live under [08_decisions/](../08_decisions/).
- Protocol specs live under [protocols/](../protocols/).
