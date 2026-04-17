---
source_file: "backend/02_features/06_notify/sub_features/07_email/service.py"
type: "code"
community: "Notify Templates & Email Delivery"
location: "L258"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Notify_Templates_&_Email_Delivery
---

# process_queued_email_deliveries()

## Connections
- [[Poll + send queued email deliveries. Returns number successfully sent.     Each]] - `rationale_for` [EXTRACTED]
- [[_email_sender_loop()]] - `calls` [EXTRACTED]
- [[_send_one()]] - `calls` [EXTRACTED]
- [[backoff_seconds_for_attempt()]] - `calls` [INFERRED]
- [[get()_1]] - `calls` [INFERRED]
- [[mark_retryable_error()]] - `calls` [INFERRED]
- [[poll_and_claim_email_deliveries()]] - `calls` [INFERRED]
- [[service.py_8]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Notify_Templates_&_Email_Delivery