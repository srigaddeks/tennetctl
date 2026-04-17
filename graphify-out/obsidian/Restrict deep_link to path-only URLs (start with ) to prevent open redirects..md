---
source_file: "backend/02_features/06_notify/worker.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L124"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Restrict deep_link to path-only URLs (start with /) to prevent open redirects.

## Connections
- [[_safe_deep_link()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer