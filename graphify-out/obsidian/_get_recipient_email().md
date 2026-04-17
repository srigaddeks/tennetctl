---
source_file: "backend/02_features/06_notify/sub_features/07_email/service.py"
type: "code"
community: "Notify Templates & Email Delivery"
location: "L71"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Notify_Templates_&_Email_Delivery
---

# _get_recipient_email()

## Connections
- [[Resolve email address for a delivery recipient.     Looks up 03_iam.v_users]] - `rationale_for` [EXTRACTED]
- [[ValueError]] - `calls` [INFERRED]
- [[_send_one()]] - `calls` [EXTRACTED]
- [[bounce_webhook_route()]] - `calls` [INFERRED]
- [[service.py_8]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Notify_Templates_&_Email_Delivery