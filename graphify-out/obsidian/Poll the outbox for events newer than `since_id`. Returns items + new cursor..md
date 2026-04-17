---
source_file: "backend/02_features/04_audit/sub_features/01_events/routes.py"
type: "rationale"
community: "Node Catalog & Feature Implementations"
location: "L351"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Node_Catalog_&_Feature_Implementations
---

# Poll the outbox for events newer than `since_id`. Returns items + new cursor.

## Connections
- [[tail_route()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Node_Catalog_&_Feature_Implementations