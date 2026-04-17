---
source_file: "backend/02_features/03_iam/sub_features/03_users/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L179"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Service_&_Repository_Layer
---

# delete_user()

## Connections
- [[NotFoundError]] - `calls` [INFERRED]
- [[_emit_audit()]] - `calls` [EXTRACTED]
- [[delete_user_route()]] - `calls` [INFERRED]
- [[service.py_19]] - `contains` [EXTRACTED]
- [[soft_delete_user()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Service_&_Repository_Layer