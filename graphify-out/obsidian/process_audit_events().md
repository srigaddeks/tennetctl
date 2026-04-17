---
source_file: "backend/02_features/06_notify/worker.py"
type: "code"
community: "Service & Repository Layer"
location: "L60"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# process_audit_events()

## Connections
- [[Poll the audit outbox for events newer than `since_id`.     For each event, matc]] - `rationale_for` [EXTRACTED]
- [[_enqueue_for_subscription()]] - `calls` [EXTRACTED]
- [[_worker_loop()]] - `calls` [EXTRACTED]
- [[list_active_for_worker()]] - `calls` [INFERRED]
- [[matches_pattern()]] - `calls` [INFERRED]
- [[poll_outbox()]] - `calls` [INFERRED]
- [[worker.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer