---
source_file: "backend/02_features/06_notify/worker.py"
type: "code"
community: "Service & Repository Layer"
location: "L133"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# _enqueue_for_subscription()

## Connections
- [[Create delivery row(s) for one matched subscription + audit event.]] - `rationale_for` [EXTRACTED]
- [[_resolve_recipients()]] - `calls` [EXTRACTED]
- [[_safe_deep_link()]] - `calls` [EXTRACTED]
- [[create_delivery()_1]] - `calls` [INFERRED]
- [[get()_1]] - `calls` [INFERRED]
- [[get_template()_1]] - `calls` [INFERRED]
- [[is_opted_in()]] - `calls` [INFERRED]
- [[process_audit_events()]] - `calls` [EXTRACTED]
- [[resolve_variables()_1]] - `calls` [INFERRED]
- [[worker.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer