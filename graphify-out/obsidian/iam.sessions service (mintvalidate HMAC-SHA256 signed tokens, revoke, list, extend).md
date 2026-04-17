---
source_file: "backend/02_features/03_iam/sub_features/09_sessions/service.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# iam.sessions service (mint/validate HMAC-SHA256 signed tokens, revoke, list, extend)

## Connections
- [[HMAC-SHA256 opaque session token format session_id.base64url(HMAC(signing_key, session_id))]] - `implements` [EXTRACTED]
- [[Node iam.auth.revoke_session (effect node — marks session revoked + emits audit, idempotent)]] - `calls` [EXTRACTED]
- [[Node iam.auth.signin (effect node — verify credential + mint session)]] - `calls` [INFERRED]
- [[Node iam.auth.signup (effect node — create email_password user + credential + session)]] - `calls` [INFERRED]
- [[Node iam.auth.validate_session (request node — decode + verify opaque token, returns session or None)]] - `calls` [EXTRACTED]
- [[Session lifecycle concept (mint token on signinsignup, validate on every request, revoke on signoutexplicit delete, extend via PATCH)]] - `implements` [EXTRACTED]
- [[Vault dependency for auth password pepper + session signing key (auth.session.signing_key_v1), SWR-cached 60s]] - `references` [EXTRACTED]
- [[iam.groups service (CRUD create, get, list, update, delete with audit emission)]] - `conceptually_related_to` [INFERRED]
- [[iam.sessions FastAPI routes (self-service listgetpatch-extenddelete for own sessions)]] - `calls` [EXTRACTED]
- [[iam.sessions repository (asyncpg, v_sessions view, 16_fct_sessions, revokeextendlist)]] - `calls` [EXTRACTED]
- [[iam.sessions schemas (SessionRead, SessionPatchBody with extend field)]] - `shares_data_with` [INFERRED]

#graphify/code #graphify/EXTRACTED #community/Auth_Nodes_&_Routes