---
source_file: "backend/02_features/06_notify/sub_features/16_suppression/routes.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.suppression.routes — /v1/notify/suppressions (admin) + /v1/notify/unsubscribe (public RFC 8058)

## Connections
- [[notify.routes — Feature router aggregating all notify sub-feature routers]] - `references` [EXTRACTED]
- [[notify.suppression.schemas — SuppressionAdd  SuppressionRow (ReasonCode hard_bounce, complaint, manual, unsubscribe)]] - `references` [EXTRACTED]
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization