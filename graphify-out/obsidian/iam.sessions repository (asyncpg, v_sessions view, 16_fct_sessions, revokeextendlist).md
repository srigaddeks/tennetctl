---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/repository.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# iam.sessions repository (asyncpg, v_sessions view, 16_fct_sessions, revoke/extend/list)

## Connections
- [[Session lifecycle concept (mint token on signinsignup, validate on every request, revoke on signoutexplicit delete, extend via PATCH)]] - `implements` [INFERRED]
- [[iam.auth FastAPI routes (signup, signin, signout, me, google, github)]] - `calls` [EXTRACTED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Auth_Nodes_&_Routes