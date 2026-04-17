---
source_file: "backend/02_features/03_iam/sub_features/10_auth/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L107"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# _attach_to_default_org_if_needed()

## Connections
- [[In single-tenant mode, ensure user is a member of the default org and return org]] - `rationale_for` [EXTRACTED]
- [[_ensure_default_org()]] - `calls` [EXTRACTED]
- [[assign_org()]] - `calls` [INFERRED]
- [[get_org_membership_by_pair()]] - `calls` [INFERRED]
- [[load_config()]] - `calls` [INFERRED]
- [[oauth_signin()]] - `calls` [EXTRACTED]
- [[service.py_21]] - `contains` [EXTRACTED]
- [[signin()]] - `calls` [EXTRACTED]
- [[signup()]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer