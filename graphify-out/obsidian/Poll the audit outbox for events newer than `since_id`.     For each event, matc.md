---
source_file: "backend/02_features/06_notify/worker.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L61"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Poll the audit outbox for events newer than `since_id`.     For each event, matc

## Connections
- [[process_audit_events()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer