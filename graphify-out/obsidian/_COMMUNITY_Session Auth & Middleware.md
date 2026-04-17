---
type: community
cohesion: 0.03
members: 111
---

# Session Auth & Middleware

**Cohesion:** 0.03 - loosely connected
**Members:** 111 nodes

## Members
- [[.dispatch()_1]] - code - backend/01_core/middleware.py
- [[.dispatch()_2]] - code - backend/01_core/middleware.py
- [[.run()_20]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[Add X-Request-ID header to every response and stash it on request.state.]] - rationale - backend/01_core/middleware.py
- [[AuthValidateSession]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[BaseHTTPMiddleware]] - code
- [[Best-effort update — do not fail the caller if this errors.]] - rationale - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[Convert AppError into standard error envelope response.]] - rationale - backend/01_core/middleware.py
- [[Count tokens created for this email in the last N minutes (rate-limit check).]] - rationale - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[Create a key; return the sanitized row with `token` attached exactly once.]] - rationale - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[Create a magic-link token and enqueue delivery. Always returns (no user enumerat]] - rationale - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[FastAPI middleware — error handling, request ID, and session injection.  Registe]] - rationale - backend/01_core/middleware.py
- [[Fetch + base64-decode the signing key. Cached upstream by VaultClient (60s).]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[Generate WebAuthn authentication options for a given email.]] - rationale - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[Input_20]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[Look up + verify a Bearer token. Returns the key row on success, else None.]] - rationale - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[Output_20]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[Pull the session token from Bearer header, x-session-token, or cookie.]] - rationale - backend/01_core/middleware.py
- [[Push expires_at to `new_expires_at` iff the session is still live + unrevoked.]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/repository.py
- [[Raise 403 if the caller is API-key-authenticated and lacks `scope`.      Session]] - rationale - backend/01_core/middleware.py
- [[Register all middleware and exception handlers on the app.]] - rationale - backend/01_core/middleware.py
- [[RequestIdMiddleware]] - code - backend/01_core/middleware.py
- [[Return (user_id, org_id) from the session — API keys can't mint keys.      `org_]] - rationale - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[Return a JSONResponse with error envelope.]] - rationale - backend/01_core/response.py
- [[Return the session iff it belongs to the caller. Else None (so route can 404).]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[Return the session row iff signature matches AND row is_valid. Else None.]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[Revoke a session owned by `user_id`. Emits iam.sessions.revoked audit.]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[SessionMiddleware]] - code - backend/01_core/middleware.py
- [[Split nk_key_id.secret into (key_id, secret). Returns None if malformed.]] - rationale - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[Used by the Bearer middleware. Includes secret_hash for argon2 verify.]] - rationale - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[Validate signature + return embedded session_id, or None if tampered.]] - rationale - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[Validate the inbound session token or API key and inject scope onto state.]] - rationale - backend/01_core/middleware.py
- [[Validate token, mark consumed, return (session_token, user, session).]] - rationale - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[Verify authentication assertion; mint session.]] - rationale - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[_app_error_handler()]] - code - backend/01_core/middleware.py
- [[_b64url()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[_b64url_decode()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[_b64url_encode()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[_extract_token()]] - code - backend/01_core/middleware.py
- [[_hash_token()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[_new_key_id()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[_new_secret()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[_origin()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[_require_session()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[_resolve_ttl_days()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[_rp_id()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[_rp_name()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[_sign()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[_signing_key_bytes()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[add_suppression()]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[auth_begin()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[auth_complete()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[consume_magic_link()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[count_recent_by_email()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[create_api_key_route()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[create_challenge()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[create_credential()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[create_token()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[delete_credential()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[error_response()]] - code - backend/01_core/response.py
- [[extend_expires()]] - code - backend/02_features/03_iam/sub_features/09_sessions/repository.py
- [[extend_my_session()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[get_active_by_key_id()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[get_by_hash()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[get_challenge()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[get_credential_by_raw_id()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[get_credentials_for_user()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[get_my_session()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[iam.auth.validate_session — request node.  Stateless validation hook used by the]] - rationale - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[iam_auth_validate_session.py]] - code - backend/02_features/03_iam/sub_features/10_auth/nodes/iam_auth_validate_session.py
- [[insert_api_key()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[is_suppressed()]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[list_api_keys()_1]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[list_api_keys()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[list_api_keys_route()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[list_by_user()]] - code - backend/02_features/03_iam/sub_features/09_sessions/repository.py
- [[list_credentials()_1]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[list_credentials()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[list_my_sessions()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[list_suppressions()]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[make_token()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[make_unsubscribe_token()]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[mark_challenge_consumed()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[mark_consumed()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[middleware.py]] - code - backend/01_core/middleware.py
- [[mint_api_key()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[parse_token()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[parse_unsubscribe_token()]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[register_begin()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[register_complete()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[register_middleware()]] - code - backend/01_core/middleware.py
- [[remove_suppression()]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[repository.py_12]] - code - backend/02_features/03_iam/sub_features/11_magic_link/repository.py
- [[repository.py_13]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[repository.py_14]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[request_magic_link()]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[require_scope()]] - code - backend/01_core/middleware.py
- [[revoke_api_key()_1]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[revoke_api_key()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[revoke_api_key_route()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[revoke_my_session()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[revoke_session()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[routes.py_17]] - code - backend/02_features/03_iam/sub_features/15_api_keys/routes.py
- [[service.py_23]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py
- [[service.py_12]] - code - backend/02_features/03_iam/sub_features/11_magic_link/service.py
- [[service.py_13]] - code - backend/02_features/03_iam/sub_features/13_passkeys/service.py
- [[service.py_14]] - code - backend/02_features/03_iam/sub_features/15_api_keys/service.py
- [[service.py_1]] - code - backend/02_features/06_notify/sub_features/16_suppression/service.py
- [[touch_last_used()]] - code - backend/02_features/03_iam/sub_features/15_api_keys/repository.py
- [[update_sign_count()]] - code - backend/02_features/03_iam/sub_features/13_passkeys/repository.py
- [[validate_token()]] - code - backend/02_features/03_iam/sub_features/09_sessions/service.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Session_Auth_&_Middleware
SORT file.name ASC
```

## Connections to other communities
- 52 edges to [[_COMMUNITY_Service & Repository Layer]]
- 20 edges to [[_COMMUNITY_API Routes & Response Handling]]
- 12 edges to [[_COMMUNITY_Auth & Error Handling]]
- 4 edges to [[_COMMUNITY_Node Catalog & Feature Implementations]]
- 3 edges to [[_COMMUNITY_Notify Templates & Email Delivery]]
- 2 edges to [[_COMMUNITY_Core Infrastructure]]
- 1 edge to [[_COMMUNITY_Admin Routes & DLQ]]

## Top bridge nodes
- [[_signing_key_bytes()]] - degree 15, connects to 4 communities
- [[consume_magic_link()]] - degree 11, connects to 3 communities
- [[extend_my_session()]] - degree 10, connects to 3 communities
- [[request_magic_link()]] - degree 10, connects to 3 communities
- [[auth_complete()]] - degree 13, connects to 2 communities