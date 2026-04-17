---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/service.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Error_Types_&_Authorization
---

# notify.deliveries.service — create_delivery

## Connections
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - `conceptually_related_to` [INFERRED]
- [[notify.variables.repository — resolve_variables (used by worker to render template vars)]] - `shares_data_with` [INFERRED]
- [[notify.worker — Subscription worker polls audit outbox, matches subscriptions, enqueues deliveries]] - `calls` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Error_Types_&_Authorization