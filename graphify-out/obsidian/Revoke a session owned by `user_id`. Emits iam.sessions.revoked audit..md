---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "rationale"
community: "Session Auth & Middleware"
location: "L170"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/Session_Auth_&_Middleware
---

# Revoke a session owned by `user_id`. Emits iam.sessions.revoked audit.

## Connections
- [[revoke_my_session()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/Session_Auth_&_Middleware