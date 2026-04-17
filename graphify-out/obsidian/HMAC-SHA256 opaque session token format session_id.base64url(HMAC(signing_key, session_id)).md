---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "document"
community: "Auth Nodes & Routes"
tags:
  - graphify/document
  - graphify/INFERRED
  - community/Auth_Nodes_&_Routes
---

# HMAC-SHA256 opaque session token format: <session_id>.<base64url(HMAC(signing_key, session_id))>

## Connections
- [[Node iam.auth.validate_session (request node — decode + verify opaque token, returns session or None)]] - `implements` [INFERRED]
- [[Vault dependency for auth password pepper + session signing key (auth.session.signing_key_v1), SWR-cached 60s]] - `rationale_for` [INFERRED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `implements` [EXTRACTED]

#graphify/document #graphify/INFERRED #community/Auth_Nodes_&_Routes