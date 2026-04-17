---
source_file: "backend/02_features/09_featureflags/sub_features/02_permissions/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L41"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Service_&_Repository_Layer
---

# check_flag_permission()

## Connections
- [[ForbiddenError]] - `calls` [INFERRED]
- [[Raise ForbiddenError if caller lacks `required` permission on flag_id.      `req]] - `rationale_for` [EXTRACTED]
- [[ValidationError]] - `calls` [INFERRED]
- [[get()_1]] - `calls` [INFERRED]
- [[max_rank_for_user_on_flag()]] - `calls` [INFERRED]
- [[service.py_32]] - `contains` [EXTRACTED]
- [[user_has_admin_all_scope()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Service_&_Repository_Layer