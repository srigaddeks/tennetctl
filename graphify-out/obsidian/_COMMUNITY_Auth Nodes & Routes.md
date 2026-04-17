---
type: community
cohesion: 0.14
members: 22
---

# Auth Nodes & Routes

**Cohesion:** 0.14 - loosely connected
**Members:** 22 nodes

## Members
- [[Groups as RBAC building block org-scoped, code-unique per org, EAV attributes (codelabeldescription)]] - document - backend/02_features/03_iam/sub_features/05_groups/service.py
- [[HMAC-SHA256 opaque session token format session_id.base64url(HMAC(signing_key, session_id))]] - document - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[Node iam.auth.revoke_session (effect node — marks session revoked + emits audit, idempotent)]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_revoke_session.py
- [[Node iam.auth.signin (effect node — verify credential + mint session)]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_signin.py
- [[Node iam.auth.signup (effect node — create email_password user + credential + session)]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_signup.py
- [[Node iam.auth.validate_session (request node — decode + verify opaque token, returns session or None)]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[Node iam.groups.create (effect node — create group via service)]] - code - backend/02_features/03_iam/sub_features/05_groups/nodes/iam_groups_create.py
- [[Node iam.groups.get (control node — fetch group by id)]] - code - backend/02_features/03_iam/sub_features/05_groups/nodes/iam_groups_get.py
- [[OAuth2 provider support Google and GitHub code-exchange flows (OAuthCallbackBody code + redirect_uri)]] - document - backend/02_features/03_iam/sub_features/10_auth/schemas.py
- [[Session lifecycle concept (mint token on signinsignup, validate on every request, revoke on signoutexplicit delete, extend via PATCH)]] - document - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[Session token dual delivery JSON envelope for CLIAPI + httpOnly cookie for browser (tennetctl_session)]] - document - backend/02_features/03_iam/sub_features/10_auth/routes.py
- [[Vault dependency for auth password pepper + session signing key (auth.session.signing_key_v1), SWR-cached 60s]] - document - backend/02_features/03_iam/sub_features/10_auth/routes.py
- [[iam.auth FastAPI routes (signup, signin, signout, me, google, github)]] - code - backend/02_features/03_iam/sub_features/10_auth/routes.py
- [[iam.auth schemas (SignupBody, SigninBody, OAuthCallbackBody, SessionMeta, AuthResponse)]] - code - backend/02_features/03_iam/sub_features/10_auth/schemas.py
- [[iam.groups FastAPI routes (GET list, POST create, GET one, PATCH update, DELETE soft-delete)]] - code - backend/02_features/03_iam/sub_features/05_groups/routes.py
- [[iam.groups repository (asyncpg, entity_type_id=5, v_groups view, 14_fct_groups, EAV attrs)]] - code - backend/02_features/03_iam/sub_features/05_groups/repository.py
- [[iam.groups schemas (GroupCreate, GroupUpdate, GroupRead)]] - code - backend/02_features/03_iam/sub_features/05_groups/schemas.py
- [[iam.groups service (CRUD create, get, list, update, delete with audit emission)]] - code - backend/02_features/03_iam/sub_features/05_groups/service.py
- [[iam.sessions FastAPI routes (self-service listgetpatch-extenddelete for own sessions)]] - code - backend/02_features/03_iam/sub_features/09_sessions/routes.py
- [[iam.sessions repository (asyncpg, v_sessions view, 16_fct_sessions, revokeextendlist)]] - code - backend/02_features/03_iam/sub_features/09_sessions/repository.py
- [[iam.sessions schemas (SessionRead, SessionPatchBody with extend field)]] - code - backend/02_features/03_iam/sub_features/09_sessions/schemas.py
- [[iam.sessions service (mintvalidate HMAC-SHA256 signed tokens, revoke, list, extend)]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Auth_Nodes_&_Routes
SORT file.name ASC
```
