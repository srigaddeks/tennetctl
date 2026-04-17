---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/schemas.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# iam.sessions schemas (SessionRead, SessionPatchBody with extend field)

## Connections
- [[iam.auth FastAPI routes (signup, signin, signout, me, google, github)]] - `shares_data_with` [EXTRACTED]
- [[iam.sessions FastAPI routes (self-service listgetpatch-extenddelete for own sessions)]] - `references` [EXTRACTED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `shares_data_with` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Auth_Nodes_&_Routes