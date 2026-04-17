---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L122"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Return the session row iff signature matches AND row is_valid. Else None.

## Connections
- [[validate_token()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware