---
source_file: "backend/02_features/06_notify/worker.py"
type: "code"
community: "Service & Repository Layer"
location: "L243"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# _worker_loop()

## Connections
- [[Exception]] - `calls` [INFERRED]
- [[Main loop LISTEN on 'audit_events' for wake-up.     Falls back to polling every]] - `rationale_for` [EXTRACTED]
- [[clear()]] - `calls` [INFERRED]
- [[latest_outbox_id()]] - `calls` [INFERRED]
- [[process_audit_events()]] - `calls` [EXTRACTED]
- [[start_worker()]] - `calls` [EXTRACTED]
- [[worker.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer