---
source_file: "backend/02_features/06_notify/sub_features/08_webpush/service.py"
type: "code"
community: "Notify Templates & Email Delivery"
location: "L190"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Notify_Templates_&_Email_Delivery
---

# process_queued_webpush_deliveries()

## Connections
- [[Exception]] - `calls` [INFERRED]
- [[Poll and send up to `limit` queued webpush deliveries. Returns count processed.]] - `rationale_for` [EXTRACTED]
- [[_send_one()]] - `calls` [EXTRACTED]
- [[_webpush_sender_loop()]] - `calls` [EXTRACTED]
- [[backoff_seconds_for_attempt()]] - `calls` [INFERRED]
- [[get()_1]] - `calls` [INFERRED]
- [[mark_retryable_error()]] - `calls` [INFERRED]
- [[poll_and_claim_webpush_deliveries()]] - `calls` [INFERRED]
- [[service.py_2]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Notify_Templates_&_Email_Delivery