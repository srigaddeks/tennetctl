---
source_file: "backend/02_features/03_iam/sub_features/10_auth/routes.py"
type: "code"
community: "Auth Nodes & Routes"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Auth_Nodes_&_Routes
---

# iam.auth FastAPI routes (signup, signin, signout, me, google, github)

## Connections
- [[Node iam.auth.signin (effect node — verify credential + mint session)]] - `conceptually_related_to` [INFERRED]
- [[Node iam.auth.signup (effect node — create email_password user + credential + session)]] - `conceptually_related_to` [INFERRED]
- [[Session token dual delivery JSON envelope for CLIAPI + httpOnly cookie for browser (tennetctl_session)]] - `implements` [EXTRACTED]
- [[Vault dependency for auth password pepper + session signing key (auth.session.signing_key_v1), SWR-cached 60s]] - `references` [EXTRACTED]
- [[iam.auth schemas (SignupBody, SigninBody, OAuthCallbackBody, SessionMeta, AuthResponse)]] - `references` [EXTRACTED]
- [[iam.sessions repository (asyncpg, v_sessions view, 16_fct_sessions, revokeextendlist)]] - `calls` [EXTRACTED]
- [[iam.sessions schemas (SessionRead, SessionPatchBody with extend field)]] - `shares_data_with` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Auth_Nodes_&_Routes