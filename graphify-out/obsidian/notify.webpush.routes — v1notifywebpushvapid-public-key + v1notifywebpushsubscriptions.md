---
source_file: "backend/02_features/06_notify/sub_features/08_webpush/routes.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.webpush.routes — /v1/notify/webpush/vapid-public-key + /v1/notify/webpush/subscriptions

## Connections
- [[notify.routes — Feature router aggregating all notify sub-feature routers]] - `references` [EXTRACTED]
- [[notify.webpush.repository — asyncpg CRUD on 06_notify.16_fct_notify_webpush_subscriptions]] - `calls` [EXTRACTED]
- [[notify.webpush.schemas — WebpushSubscriptionCreate  WebpushSubscriptionOut  VapidPublicKeyOut]] - `references` [EXTRACTED]
- [[notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization