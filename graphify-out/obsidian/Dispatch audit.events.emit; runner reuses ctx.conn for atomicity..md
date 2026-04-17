---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L36"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Dispatch audit.events.emit; runner reuses ctx.conn for atomicity.

## Connections
- [[_emit_audit()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer