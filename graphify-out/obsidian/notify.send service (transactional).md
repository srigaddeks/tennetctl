---
source_file: "backend/02_features/06_notify/sub_features/11_send/service.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.send service (transactional)

## Connections
- [[Concept email suppression list check before send]] - `implements` [EXTRACTED]
- [[Concept fallback channel chain (scheduled deliveries on alternate channels)]] - `implements` [EXTRACTED]
- [[Concept idempotency key dedup for transactional sends]] - `implements` [EXTRACTED]
- [[SendTransactional node (notify.send.transactional)]] - `calls` [EXTRACTED]
- [[notify.deliveries service]] - `calls` [EXTRACTED]
- [[notify.send routes (POST v1notifysend)]] - `calls` [EXTRACTED]
- [[notify.template_variables repository]] - `calls` [EXTRACTED]
- [[notify.templates repository]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry