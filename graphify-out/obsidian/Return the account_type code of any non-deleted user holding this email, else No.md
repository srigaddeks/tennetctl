---
source_file: "backend/02_features/03_iam/sub_features/10_auth/service.py"
type: "rationale"
community: "Service & Repository Layer"
location: "L85"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# Return the account_type code of any non-deleted user holding this email, else No

## Connections
- [[_email_exists_any_type()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Service_&_Repository_Layer