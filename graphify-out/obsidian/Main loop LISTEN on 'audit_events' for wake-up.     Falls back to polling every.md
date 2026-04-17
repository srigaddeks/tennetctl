---
source_file: "backend/02_features/06_notify/worker.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L244"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Main loop: LISTEN on 'audit_events' for wake-up.     Falls back to polling every

## Connections
- [[_worker_loop()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer