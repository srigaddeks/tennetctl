---
source_file: "backend/02_features/02_vault/sub_features/01_secrets/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# vault.secrets.service — create_secret (used to bootstrap VAPID + suppression signing keys)

## Connections
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - `calls` [EXTRACTED]
- [[notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization