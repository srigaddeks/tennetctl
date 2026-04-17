---
source_file: "backend/02_features/03_iam/sub_features/10_auth/routes.py"
type: "document"
community: "Auth Nodes & Routes"
tags:
  - graphify/document
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# Vault dependency for auth: password pepper + session signing key (auth.session.signing_key_v1), SWR-cached 60s

## Connections
- [[HMAC-SHA256 opaque session token format session_id.base64url(HMAC(signing_key, session_id))]] - `rationale_for` [INFERRED]
- [[iam.auth FastAPI routes (signup, signin, signout, me, google, github)]] - `references` [EXTRACTED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `references` [EXTRACTED]

#graphify/document #graphify/EXTRACTED #community/Auth_Nodes_&_Routes