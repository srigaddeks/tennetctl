---
source_file: "backend/02_features/06_notify/sub_features/08_webpush/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L40"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Bootstrap VAPID keys into vault if not already present.      Returns the base64u

## Connections
- [[ensure_vapid_keys()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer