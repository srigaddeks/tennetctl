---
source_file: "backend/02_features/06_notify/sub_features/07_email/service.py"
type: "code"
community: "Notify Templates & Email Delivery"
location: "L91"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Notify_Templates_&_Email_Delivery
---

# _send_one()

## Connections
- [[Render + track + send a single email delivery.     Raises on any failure — calle]] - `rationale_for` [EXTRACTED]
- [[ValueError]] - `calls` [INFERRED]
- [[_get_recipient_email()]] - `calls` [EXTRACTED]
- [[_signing_key_bytes()]] - `calls` [INFERRED]
- [[apply_email_tracking()]] - `calls` [EXTRACTED]
- [[backoff_seconds_for_attempt()]] - `calls` [INFERRED]
- [[get()_1]] - `calls` [INFERRED]
- [[get_reason()]] - `calls` [INFERRED]
- [[get_smtp_config()_1]] - `calls` [INFERRED]
- [[get_template()_1]] - `calls` [INFERRED]
- [[get_template_group()_1]] - `calls` [INFERRED]
- [[get_user_webpush_subscriptions()]] - `calls` [INFERRED]
- [[is_suppressed()_1]] - `calls` [INFERRED]
- [[make_unsubscribe_token()]] - `calls` [INFERRED]
- [[mark_delivery_failed()]] - `calls` [INFERRED]
- [[mark_delivery_sent()]] - `calls` [INFERRED]
- [[mark_retryable_error()]] - `calls` [INFERRED]
- [[process_queued_email_deliveries()]] - `calls` [EXTRACTED]
- [[process_queued_webpush_deliveries()]] - `calls` [EXTRACTED]
- [[service.py_2]] - `contains` [EXTRACTED]
- [[service.py_8]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Notify_Templates_&_Email_Delivery