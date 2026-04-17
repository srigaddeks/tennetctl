---
source_file: "backend/02_features/09_featureflags/sub_features/02_permissions/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L44"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Raise ForbiddenError if caller lacks `required` permission on flag_id.      `req

## Connections
- [[_assert_org_exists()]] - `rationale_for` [EXTRACTED]
- [[check_flag_permission()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer