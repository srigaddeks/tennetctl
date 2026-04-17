---
source_file: "backend/02_features/03_iam/sub_features/10_auth/service.py"
type: "code"
community: "Service & Repository Layer"
location: "L126"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Service_&_Repository_Layer
---

# signup()

## Connections
- [[.run()_18]] - `calls` [INFERRED]
- [[ConflictError]] - `calls` [INFERRED]
- [[Create email_password user + credential + session. Returns (token, user, session]] - `rationale_for` [EXTRACTED]
- [[_attach_to_default_org_if_needed()]] - `calls` [EXTRACTED]
- [[_email_exists_any_type()]] - `calls` [EXTRACTED]
- [[_emit_audit()]] - `calls` [EXTRACTED]
- [[create_user()]] - `calls` [INFERRED]
- [[mint_session()]] - `calls` [INFERRED]
- [[service.py_21]] - `contains` [EXTRACTED]
- [[signup_route()]] - `calls` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Service_&_Repository_Layer