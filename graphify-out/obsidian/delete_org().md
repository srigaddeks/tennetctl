---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L202"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# delete_org()

## Connections
- [[NotFoundError]] - `calls` [INFERRED]
- [[Soft delete + audit. Raises NotFoundError if missing  already deleted.]] - `rationale_for` [EXTRACTED]
- [[_emit_audit()]] - `calls` [EXTRACTED]
- [[delete_org_route()]] - `calls` [INFERRED]
- [[service.py_16]] - `contains` [EXTRACTED]
- [[soft_delete_org()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer