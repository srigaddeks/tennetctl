---
source_file: "backend/02_features/03_iam/sub_features/02_workspaces/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L43"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# _assert_org_exists()

## Connections
- [[NotFoundError]] - `calls` [INFERRED]
- [[Raise ForbiddenError if caller lacks `required` permission on flag_id.      `req]] - `rationale_for` [EXTRACTED]
- [[create_workspace()]] - `calls` [EXTRACTED]
- [[get()_1]] - `calls` [INFERRED]
- [[run_node()]] - `calls` [INFERRED]
- [[service.py_15]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer