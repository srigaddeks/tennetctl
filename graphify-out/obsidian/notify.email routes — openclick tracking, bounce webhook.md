---
source_file: "backend/02_features/06_notify/sub_features/07_email/routes.py"
type: "code"
community: "Error Types & Authorization"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Error_Types_&_Authorization
---

# notify.email routes — open/click tracking, bounce webhook

## Connections
- [[notify.deliveries.repository — mark_retryable_error, backoff_seconds_for_attempt (used by webpush)]] - `calls` [EXTRACTED]
- [[notify.email repository — poll_and_claim_email_deliveries]] - `calls` [INFERRED]
- [[notify.suppression.service — HMAC-signed unsubscribe tokens + suppression CRUD]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Error_Types_&_Authorization