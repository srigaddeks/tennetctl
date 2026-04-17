---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Session Auth & Middleware"
location: "L193"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Session_Auth_&_Middleware
---

# extend_my_session()

## Connections
- [[NotFoundError]] - `calls` [INFERRED]
- [[Push expires_at out by the configured TTL. Session must be owned + still live.]] - `rationale_for` [EXTRACTED]
- [[UnauthorizedError]] - `calls` [INFERRED]
- [[_resolve_ttl_days()]] - `calls` [EXTRACTED]
- [[extend_expires()]] - `calls` [INFERRED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[get_my_session()]] - `calls` [EXTRACTED]
- [[patch_my_session_route()]] - `calls` [INFERRED]
- [[run_node()]] - `calls` [INFERRED]
- [[service.py_23]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Session_Auth_&_Middleware