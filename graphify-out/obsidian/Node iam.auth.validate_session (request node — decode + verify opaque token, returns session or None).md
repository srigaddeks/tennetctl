---
source_file: "backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Auth_Nodes_&_Routes
---

# Node: iam.auth.validate_session (request node — decode + verify opaque token, returns session or None)

## Connections
- [[HMAC-SHA256 opaque session token format session_id.base64url(HMAC(signing_key, session_id))]] - `implements` [INFERRED]
- [[Session lifecycle concept (mint token on signinsignup, validate on every request, revoke on signoutexplicit delete, extend via PATCH)]] - `conceptually_related_to` [INFERRED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `calls` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Auth_Nodes_&_Routes