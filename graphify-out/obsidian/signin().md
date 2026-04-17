---
source_file: "backend/02_features/03_iam/sub_features/10_auth/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L175"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# signin()

## Connections
- [[.run()_17]] - `calls` [INFERRED]
- [[UnauthorizedError]] - `calls` [INFERRED]
- [[_attach_to_default_org_if_needed()]] - `calls` [EXTRACTED]
- [[_emit_audit()]] - `calls` [EXTRACTED]
- [[_find_user_by_email_and_type()]] - `calls` [EXTRACTED]
- [[mint_session()]] - `calls` [INFERRED]
- [[service.py_21]] - `contains` [EXTRACTED]
- [[signin_route()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer