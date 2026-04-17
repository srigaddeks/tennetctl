---
type: community
cohesion: 0.09
members: 29
---

# Notify API Reference

**Cohesion:** 0.09 - loosely connected
**Members:** 29 nodes

## Members
- [[Notify API Keys (notifysend + notifyread scopes)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify API Reference]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify Bounce Webhook (POST v1notifyemailwebhooksbounce)]] - document - 03_docs/00_main/09_guides/notify-deployment.md
- [[Notify Critical Category (users cannot opt out)]] - document - 03_docs/00_main/09_guides/notify-examples/admin-broadcast.md
- [[Notify DNS for Deliverability (SPF + DKIM + DMARC)]] - document - 03_docs/00_main/09_guides/notify-deployment.md
- [[Notify Deep Link (path-only URL, open-redirect guard)]] - document - 03_docs/00_main/09_guides/notify-template-authoring.md
- [[Notify Deliveries Endpoints (GET list, GET one, unread-count, PATCH)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify Deployment Guide (SMTP + DNS)]] - document - 03_docs/00_main/09_guides/notify-deployment.md
- [[Notify Developer Guides README]] - document - 03_docs/00_main/09_guides/README.md
- [[Notify Dynamic Variables SQL Safelist (injection-safe enrichment)]] - document - 03_docs/00_main/09_guides/notify-template-authoring.md
- [[Notify Email Tracking (open pixel + click redirect via pytracking)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify Example Admin Broadcast (role-based routing)]] - document - 03_docs/00_main/09_guides/notify-examples/admin-broadcast.md
- [[Notify Fallback Chain (webpush → email at N seconds if not opened)]] - document - 03_docs/00_main/09_guides/notify-template-authoring.md
- [[Notify Idempotency Key (Idempotency-Key header)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify In-App Always-On Fan-Out]] - document - 03_docs/00_main/09_guides/notify-integration.md
- [[Notify Integration Guide (Zero to First Notification)]] - document - 03_docs/00_main/09_guides/notify-integration.md
- [[Notify Jinja2 Template Engine (non-strict mode)]] - document - 03_docs/00_main/09_guides/notify-template-authoring.md
- [[Notify Mental Model (audit event → subscription → delivery → sender)]] - document - 03_docs/00_main/09_guides/notify-integration.md
- [[Notify Role Resolution (lnk_user_roles at send time)]] - document - 03_docs/00_main/09_guides/notify-examples/admin-broadcast.md
- [[Notify SMTP Password Stored in Vault]] - document - 03_docs/00_main/09_guides/notify-integration.md
- [[Notify Subscription Recipient Modes (actor  users  roles)]] - document - 03_docs/00_main/09_guides/notify-integration.md
- [[Notify Subscriptions Endpoints]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify Supported SMTP Providers (Postmark, SendGrid, Mailgun, SES, Resend)]] - document - 03_docs/00_main/09_guides/notify-deployment.md
- [[Notify Suppression List + RFC 8058 Unsubscribe]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify Template Authoring Guide]] - document - 03_docs/00_main/09_guides/notify-template-authoring.md
- [[Notify Template Endpoints (CRUD + bodies + test-send + analytics)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[Notify Variable Resolution Order (dynamic → subject → per-call overrides)]] - document - 03_docs/00_main/09_guides/notify-template-authoring.md
- [[Notify WebPush Endpoints (VAPID key + subscriptions)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md
- [[POST v1notifysend (Transactional Send Endpoint)]] - document - 03_docs/00_main/09_guides/notify-api-reference.md

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Notify_API_Reference
SORT file.name ASC
```
