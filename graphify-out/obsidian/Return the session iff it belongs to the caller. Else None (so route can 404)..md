---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L155"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Return the session iff it belongs to the caller. Else None (so route can 404).

## Connections
- [[get_my_session()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware