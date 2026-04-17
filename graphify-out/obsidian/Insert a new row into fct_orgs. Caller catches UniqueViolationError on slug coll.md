---
source_file: "backend/02_features/03_iam/sub_features/01_orgs/repository.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L101"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Insert a new row into fct_orgs. Caller catches UniqueViolationError on slug coll

## Connections
- [[insert_org()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer