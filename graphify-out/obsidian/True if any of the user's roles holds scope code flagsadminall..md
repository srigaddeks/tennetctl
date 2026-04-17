---
source_file: "backend/02_features/09_featureflags/sub_features/02_permissions/repository.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L132"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# True if any of the user's roles holds scope code flags:admin:all.

## Connections
- [[user_has_admin_all_scope()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer