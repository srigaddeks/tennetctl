---
source_file: "backend/02_features/06_notify/sub_features/16_suppression/repository.py"
type: "rationale"
community: "Auth & Error Handling"
location: "L30"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Auth_&_Error_Handling
---

# Insert or skip on conflict (org_id, email). Returns the row or None if dup.

## Connections
- [[add_suppression()_1]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Auth_&_Error_Handling