---
source_file: "backend/02_features/04_audit/sub_features/03_outbox/repository.py"
type: "rationale"
community: "Audit Outbox"
location: "L24"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Audit_Outbox
---

# Return events from the outbox newer than `since_id`.     Joins with v_audit_even

## Connections
- [[poll_outbox()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Audit_Outbox