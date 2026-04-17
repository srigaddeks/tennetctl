---
source_file: "backend/02_features/03_iam/sub_features/06_applications/repository.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L150"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Atomic REPLACE: delete existing rows + insert the new set. Caller must hold a tx

## Connections
- [[replace_application_scopes()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer