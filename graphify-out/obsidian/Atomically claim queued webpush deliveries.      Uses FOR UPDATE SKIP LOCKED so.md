---
source_file: "backend/02_features/06_notify/sub_features/08_webpush/repository.py"
type: "rationale"
community: "Notify Templates & Email Delivery"
location: "L97"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Notify_Templates_&_Email_Delivery
---

# Atomically claim queued webpush deliveries.      Uses FOR UPDATE SKIP LOCKED so

## Connections
- [[poll_and_claim_webpush_deliveries()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Notify_Templates_&_Email_Delivery