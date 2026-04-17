---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Session Auth & Middleware"
location: "L154"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# get_my_session()

## Connections
- [[Return the session iff it belongs to the caller. Else None (so route can 404).]] - `rationale_for` [EXTRACTED]
- [[extend_my_session()]] - `calls` [EXTRACTED]
- [[get_by_id()]] - `calls` [INFERRED]
- [[get_my_session_route()]] - `calls` [INFERRED]
- [[revoke_my_session()]] - `calls` [EXTRACTED]
- [[service.py_23]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Session_Auth_&_Middleware