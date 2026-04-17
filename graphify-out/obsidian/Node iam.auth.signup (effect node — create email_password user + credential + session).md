---
source_file: "backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_signup.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Auth_Nodes_&_Routes
---

# Node: iam.auth.signup (effect node — create email_password user + credential + session)

## Connections
- [[iam.auth FastAPI routes (signup, signin, signout, me, google, github)]] - `conceptually_related_to` [INFERRED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/Auth_Nodes_&_Routes