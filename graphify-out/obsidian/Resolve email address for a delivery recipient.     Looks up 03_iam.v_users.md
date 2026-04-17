---
source_file: "backend/02_features/06_notify/sub_features/07_email/service.py"
type: "rationale"
community: "Notify Templates & Email Delivery"
location: "L72"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Notify_Templates_&_Email_Delivery
---

# Resolve email address for a delivery recipient.     Looks up "03_iam"."v_users"

## Connections
- [[_get_recipient_email()]] - `rationale_for` [EXTRACTED]
- [[_signing_key_bytes()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Notify_Templates_&_Email_Delivery