---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/service.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.deliveries service

## Connections
- [[Concept delivery status lifecycle (queued → sent → openedclickedfailed)]] - `implements` [EXTRACTED]
- [[Concept in-app delivery auto-advances to delivered on creation]] - `implements` [EXTRACTED]
- [[notify.deliveries repository]] - `calls` [EXTRACTED]
- [[notify.deliveries routes]] - `calls` [EXTRACTED]
- [[notify.send service (transactional)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry