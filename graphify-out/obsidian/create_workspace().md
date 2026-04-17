---
source_file: "backend/02_features/03_iam/sub_features/02_workspaces/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L56"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Service_&_Repository_Layer
---

# create_workspace()

## Connections
- [[.run()_6]] - `calls` [INFERRED]
- [[ConflictError]] - `calls` [INFERRED]
- [[Validate parent org exists, enforce per-org slug uniqueness, insert fct +     dt]] - `rationale_for` [EXTRACTED]
- [[_assert_org_exists()]] - `calls` [EXTRACTED]
- [[_emit_audit()]] - `calls` [EXTRACTED]
- [[create_workspace_route()]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[get_by_org_slug()]] - `calls` [INFERRED]
- [[insert_workspace()]] - `calls` [INFERRED]
- [[service.py_15]] - `contains` [EXTRACTED]
- [[set_display_name()]] - `calls` [INFERRED]
- [[uuid7()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Service_&_Repository_Layer