---
source_file: "backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_revoke_session.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# Node: iam.auth.revoke_session (effect node — marks session revoked + emits audit, idempotent)

## Connections
- [[Session lifecycle concept (mint token on signinsignup, validate on every request, revoke on signoutexplicit delete, extend via PATCH)]] - `conceptually_related_to` [INFERRED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `calls` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Auth_Nodes_&_Routes