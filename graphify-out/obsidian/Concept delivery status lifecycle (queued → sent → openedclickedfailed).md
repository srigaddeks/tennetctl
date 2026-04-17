---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/service.py"
type: "document"
community: "Delivery Tracking & Retry"
tags:
  - graphify/document
  - graphify/INFERRED
  - community/Delivery_Tracking_&_Retry
---

# Concept: delivery status lifecycle (queued → sent → opened/clicked/failed)

## Connections
- [[Concept Jinja2 template rendering (subject + html + text)]] - `conceptually_related_to` [INFERRED]
- [[Concept fallback channel chain (scheduled deliveries on alternate channels)]] - `conceptually_related_to` [INFERRED]
- [[Concept idempotency key dedup for transactional sends]] - `conceptually_related_to` [INFERRED]
- [[notify.deliveries service]] - `implements` [EXTRACTED]

#graphify/document #graphify/INFERRED #community/Delivery_Tracking_&_Retry