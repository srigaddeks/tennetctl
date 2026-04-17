---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L138"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# PATCH — only provided fields change. Raises NotFoundError if missing / deleted.

## Connections
- [[update_org()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer