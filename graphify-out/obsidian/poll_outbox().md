---
source_file: "backend/02_features/04_audit/sub_features/03_outbox/repository.py"
type: "code"
community: "Audit Outbox"
location: "L17"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Audit_Outbox
---

# poll_outbox()

## Connections
- [[.run()_63]] - `calls` [INFERRED]
- [[Return events from the outbox newer than `since_id`.     Joins with v_audit_even]] - `rationale_for` [EXTRACTED]
- [[poll()]] - `calls` [INFERRED]
- [[process_audit_events()]] - `calls` [INFERRED]
- [[repository.py_37]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Audit_Outbox