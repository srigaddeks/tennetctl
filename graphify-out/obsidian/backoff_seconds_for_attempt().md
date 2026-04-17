---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/repository.py"
type: "code"
community: "Notify Templates & Email Delivery"
location: "L164"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Notify_Templates_&_Email_Delivery
---

# backoff_seconds_for_attempt()

## Connections
- [[Exponential backoff 60s, 120s, 240s, 480s, ...]] - `rationale_for` [EXTRACTED]
- [[_send_one()]] - `calls` [INFERRED]
- [[process_queued_email_deliveries()]] - `calls` [INFERRED]
- [[process_queued_webpush_deliveries()]] - `calls` [INFERRED]
- [[repository.py_6]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Notify_Templates_&_Email_Delivery