---
source_file: "backend/02_features/06_notify/sub_features/08_webpush/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller

## Connections
- [[notify.deliveries.repository — mark_retryable_error, backoff_seconds_for_attempt (used by webpush)]] - `calls` [EXTRACTED]
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - `conceptually_related_to` [INFERRED]
- [[notify.webpush.repository — asyncpg CRUD on 06_notify.16_fct_notify_webpush_subscriptions]] - `calls` [EXTRACTED]
- [[notify.webpush.routes — v1notifywebpushvapid-public-key + v1notifywebpushsubscriptions]] - `calls` [EXTRACTED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `calls` [EXTRACTED]
- [[vault.secrets.service — create_secret (used to bootstrap VAPID + suppression signing keys)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization