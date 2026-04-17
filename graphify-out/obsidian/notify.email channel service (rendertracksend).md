---
source_file: "backend/02_features/06_notify/sub_features/07_email/service.py"
type: "code"
community: "Delivery Tracking & Retry"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Delivery_Tracking_&_Retry
---

# notify.email channel service (render/track/send)

## Connections
- [[Concept RFC 8058 one-click unsubscribe header (List-Unsubscribe)]] - `implements` [EXTRACTED]
- [[Concept SMTP password stored in vault, fetched at send time]] - `references` [EXTRACTED]
- [[Concept email suppression list check before send]] - `implements` [EXTRACTED]
- [[Concept exponential backoff retry for delivery failures (60s, 120s, 240s...)]] - `references` [EXTRACTED]
- [[Concept pytracking open pixel + click wrapping for email]] - `implements` [EXTRACTED]
- [[notify.deliveries repository]] - `calls` [EXTRACTED]
- [[notify.smtp_configs repository]] - `calls` [EXTRACTED]
- [[notify.templates repository]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Delivery_Tracking_&_Retry