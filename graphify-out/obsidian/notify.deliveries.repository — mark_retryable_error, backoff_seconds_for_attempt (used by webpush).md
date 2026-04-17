---
source_file: "backend/02_features/06_notify/sub_features/06_deliveries/repository.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.deliveries.repository — mark_retryable_error, backoff_seconds_for_attempt (used by webpush)

## Connections
- [[notify.email routes — openclick tracking, bounce webhook]] - `calls` [EXTRACTED]
- [[notify.webpush.service — VAPID key bootstrap + pywebpush sending + delivery poller]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization