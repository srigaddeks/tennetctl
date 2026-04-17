---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/repository.py"
type: "document"
community: "Delivery Tracking & Retry"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# Concept: idempotency key dedup for transactional sends

## Connections
- [[Concept delivery status lifecycle (queued → sent → openedclickedfailed)]] - `conceptually_related_to` [INFERRED]
- [[notify.deliveries repository]] - `implements` [EXTRACTED]
- [[notify.send service (transactional)]] - `implements` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry