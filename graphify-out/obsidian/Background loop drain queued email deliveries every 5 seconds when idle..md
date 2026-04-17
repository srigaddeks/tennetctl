---
source_file: "backend/02_features/06_notify/sub_features/07_email/service.py"
type: "rationale"
community: "Notify Templates & Email Delivery"
location: "L303"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Notify_Templates_&_Email_Delivery
---

# Background loop: drain queued email deliveries every 5 seconds when idle.

## Connections
- [[_email_sender_loop()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Notify_Templates_&_Email_Delivery