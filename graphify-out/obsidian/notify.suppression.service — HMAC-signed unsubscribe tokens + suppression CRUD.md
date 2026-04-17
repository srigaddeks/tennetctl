---
source_file: "backend/02_features/06_notify/sub_features/16_suppression/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD

## Connections
- [[notify.deliveries.service — create_delivery]] - `conceptually_related_to` [INFERRED]
- [[notify.email routes — openclick tracking, bounce webhook]] - `calls` [EXTRACTED]
- [[notify.suppression.repository — asyncpg CRUD on 06_notify.17_fct_notify_suppressions]] - `calls` [EXTRACTED]
- [[notify.suppression.routes — v1notifysuppressions (admin) + v1notifyunsubscribe (public RFC 8058)]] - `calls` [EXTRACTED]
- [[notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller]] - `conceptually_related_to` [INFERRED]
- [[vault.client — VaultClient, VaultSecretNotFound (used by suppression + webpush for signing keys)]] - `calls` [EXTRACTED]
- [[vault.secrets.service — create_secret (used to bootstrap VAPID + suppression signing keys)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization