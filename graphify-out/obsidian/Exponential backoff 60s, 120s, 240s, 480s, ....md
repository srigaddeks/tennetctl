---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/repository.py"
type: "rationale"
community: "Notify Templates & Email Delivery"
location: "L165"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Notify_Templates_&_Email_Delivery
---

# Exponential backoff: 60s, 120s, 240s, 480s, ...

## Connections
- [[backoff_seconds_for_attempt()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Notify_Templates_&_Email_Delivery