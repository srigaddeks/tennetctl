---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L209"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Soft delete + audit. Raises NotFoundError if missing / already deleted.

## Connections
- [[delete_org()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer