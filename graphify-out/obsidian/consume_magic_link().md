---
source_file: "backend/02_features/03_iam/sub_features/11_magic_link/service.py"
type: "code"
community: "Session Auth & Middleware"
location: "L169"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Session_Auth_&_Middleware
---

# consume_magic_link()

## Connections
- [[AppError]] - `calls` [INFERRED]
- [[Validate token, mark consumed, return (session_token, user, session).]] - `rationale_for` [EXTRACTED]
- [[_hash_token()]] - `calls` [EXTRACTED]
- [[_signing_key_bytes()]] - `calls` [EXTRACTED]
- [[consume_magic_link_route()]] - `calls` [INFERRED]
- [[get_by_hash()]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[mark_consumed()]] - `calls` [INFERRED]
- [[mint_session()]] - `calls` [INFERRED]
- [[run_node()]] - `calls` [INFERRED]
- [[service.py_12]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Session_Auth_&_Middleware