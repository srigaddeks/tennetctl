---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/repository.py"
type: "document"
community: "Delivery Tracking & Retry"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# Concept: exponential backoff retry for delivery failures (60s, 120s, 240s...)

## Connections
- [[notify.deliveries repository]] - `implements` [EXTRACTED]
- [[notify.email channel service (rendertracksend)]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry