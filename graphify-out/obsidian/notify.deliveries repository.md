---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/repository.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.deliveries repository

## Connections
- [[Concept exponential backoff retry for delivery failures (60s, 120s, 240s...)]] - `implements` [EXTRACTED]
- [[Concept idempotency key dedup for transactional sends]] - `implements` [EXTRACTED]
- [[DB table 06_notify.15_fct_notify_deliveries]] - `references` [EXTRACTED]
- [[DB table 06_notify.61_evt_notify_delivery_events]] - `references` [EXTRACTED]
- [[DB view 06_notify.v_notify_deliveries]] - `references` [EXTRACTED]
- [[notify.deliveries service]] - `calls` [EXTRACTED]
- [[notify.email channel service (rendertracksend)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry