---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "document"
community: "Auth Nodes & Routes"
tags:
  - graphify/document
  - graphify/INFERRED
  - community/Auth_Nodes_&_Routes
---

# Session lifecycle concept (mint token on signin/signup, validate on every request, revoke on signout/explicit delete, extend via PATCH)

## Connections
- [[Node iam.auth.revoke_session (effect node — marks session revoked + emits audit, idempotent)]] - `conceptually_related_to` [INFERRED]
- [[Node iam.auth.validate_session (request node — decode + verify opaque token, returns session or None)]] - `conceptually_related_to` [INFERRED]
- [[iam.sessions repository (asyncpg, v_sessions view, 16_fct_sessions, revokeextendlist)]] - `implements` [INFERRED]
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - `implements` [EXTRACTED]

#graphify/document #graphify/INFERRED #community/Auth_Nodes_&_Routes