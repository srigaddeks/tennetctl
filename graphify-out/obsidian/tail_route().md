---
source_file: "backend/02_features/04_audit/sub_features/01_events/routes.py"
type: "code"
community: "Node Catalog & Feature Implementations"
location: "L345"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Node_Catalog_&_Feature_Implementations
---

# tail_route()

## Connections
- [[AuditEventRowSlim]] - `calls` [INFERRED]
- [[AuditTailResponse]] - `calls` [INFERRED]
- [[Poll the outbox for events newer than `since_id`. Returns items + new cursor.]] - `rationale_for` [EXTRACTED]
- [[_session_scope()]] - `calls` [EXTRACTED]
- [[poll()]] - `calls` [INFERRED]
- [[routes.py_44]] - `contains` [EXTRACTED]
- [[success()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Node_Catalog_&_Feature_Implementations