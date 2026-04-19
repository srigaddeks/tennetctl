# 28-01 SUMMARY — Python SDK core + auth module

**Status:** ✅ Complete (2026-04-18)
**Plan:** `.paul/phases/28-sdk-core-auth/28-01-PLAN.md`

## What shipped

Python SDK at `sdk/python/` — installable with `pip install -e sdk/python[dev]`.

### Public surface (`from tennetctl import ...`)

```
Tennetctl                 # main client class
Auth, Sessions, ApiKeys   # auth namespace classes

# Error hierarchy — all descend from TennetctlError
TennetctlError  (base)
├── AuthError            (401 / 403)
├── ValidationError      (400 / 422)
├── NotFoundError        (404)
├── ConflictError        (409)
├── RateLimitError       (429)
├── ServerError          (5xx after retries)
└── NetworkError         (connection / timeout before response)

__version__ = "0.1.0"
```

### URL paths wrapped

Discovered by reading the live backend routes:

| SDK call | HTTP |
|---|---|
| `client.auth.signin(email=, password=)` | `POST /v1/auth/signin` |
| `client.auth.signout()` | `POST /v1/auth/signout` |
| `client.auth.me()` | `GET /v1/auth/me` |
| `client.auth.signup(email=, password=, **extra)` | `POST /v1/auth/signup` |
| `client.auth.sessions.list()` | `GET /v1/sessions` |
| `client.auth.sessions.get(id)` | `GET /v1/sessions/{id}` |
| `client.auth.sessions.update(id, **patch)` | `PATCH /v1/sessions/{id}` |
| `client.auth.sessions.revoke(id)` | `DELETE /v1/sessions/{id}` |
| `client.auth.api_keys.list()` | `GET /v1/api-keys` |
| `client.auth.api_keys.create(name=, scopes=, expires_at=?)` | `POST /v1/api-keys` |
| `client.auth.api_keys.revoke(id)` | `DELETE /v1/api-keys/{id}` |
| `client.auth.api_keys.rotate(id)` | `POST /v1/api-keys/{id}/rotate` |

### Error mapping (status → exception)

```
200–299 with ok:true    → returns .data
204                      → returns None
400, 422                 → ValidationError
401, 403                 → AuthError
404                      → NotFoundError
409                      → ConflictError
429                      → RateLimitError
5xx (after retries)      → ServerError
unmapped status          → TennetctlError (base)
connect/read error       → NetworkError (after retries exhausted)
```

### Retry policy (bound for TS mirror)

- Retryable: `NetworkError` + HTTP `502 / 503 / 504`
- Backoff schedule: `0.5s, 1s, 2s` (exponential)
- Max attempts: 4 total (1 initial + 3 retries)
- No retry on any 4xx (fail fast)

### Decisions that bind 28-02 (TS mirror)

1. **Auth flow shape:** `signin()` returns a dict with `{token, user, session}`; SDK extracts token from `data.token` first, falls back to `data.session.token`. TS mirror must handle both shapes identically.
2. **Session-token storage:** stored on both the Transport (for outgoing requests) and exposed via `client.session_token` property (readonly). Cookie name: `tnt_session`. TS SDK in browser must use the same cookie name.
3. **API shape:** property-based sub-namespaces, not method chains. `client.auth.sessions.list()` — `sessions` is a property returning a `Sessions` instance. TS SDK uses the same shape (properties returning namespace instances, not factories).
4. **`signout()` clears session token even on server error** (try/finally). TS must do the same.
5. **`signup()` also stores session token on success** (same code path as signin).
6. **No Pydantic response models in this phase** — return types are dicts. Typed models arrive in 29-01 when the response surface is broader and worth the cost.
7. **Bearer auth header preferred over cookie** — if `api_key` is set, the client always sends `Authorization: Bearer …`. Cookie path is for session-token flows only.
8. **Create returns one-time token in `data.token`** — UI + SDK consumers must capture it immediately; it is never retrievable again.

## Verification

```bash
cd sdk/python && ../../.venv/bin/pytest --cov=tennetctl --cov-report=term-missing
```

Result:
```
33 passed in 0.25s

Name                      Stmts   Miss Branch BrPart  Cover
tennetctl/__init__.py         5      0      0      0   100%
tennetctl/_transport.py      70      8     22      4    87%
tennetctl/auth.py            62      1     14      5    92%
tennetctl/client.py          18      2      0      0    89%
tennetctl/errors.py          31      1      6      2    92%
TOTAL                       186     12     42     11    90%
```

- ≥80% coverage on `_transport.py` ✅ (87%)
- ≥80% coverage on `auth.py` ✅ (92%)
- All 33 tests pass ✅

## Acceptance Criteria

- **AC-1** Package installs and exposes a client — ✅
- **AC-2** Transport enforces bearer auth, envelope parsing, retry — ✅ (tests: `test_bearer_header_set`, `test_ok_envelope_returns_data`, `test_error_envelope_maps_to_typed_exception`, `test_retry_on_503_then_success`, `test_no_retry_on_400`, `test_network_error_raises_after_retries`)
- **AC-3** `client.auth` covers signin/signout/me/sessions/api_keys — ✅ (tests: `test_signin_stores_session_token`, `test_signout_clears_session_token`, `test_me_returns_user`, `test_sessions_list/get/revoke/update`, `test_api_keys_list/create/revoke/rotate`)
- **AC-4** Tests + docs ship — ✅ (33/33 pass, 90% total cov, quickstart at `03_docs/00_main/09_guides/sdk-quickstart.md`)

## Files created (11)

| File | Lines |
|---|---|
| `sdk/python/pyproject.toml` | 35 |
| `sdk/python/README.md` | 82 |
| `sdk/python/tennetctl/__init__.py` | 30 |
| `sdk/python/tennetctl/errors.py` | 81 |
| `sdk/python/tennetctl/_transport.py` | 123 |
| `sdk/python/tennetctl/client.py` | 49 |
| `sdk/python/tennetctl/auth.py` | 94 |
| `sdk/python/tests/conftest.py` | 37 |
| `sdk/python/tests/test_transport.py` | 150 |
| `sdk/python/tests/test_auth.py` | 157 |
| `03_docs/00_main/09_guides/sdk-quickstart.md` | 118 |

## Deferred to 28-02 (explicit)

- Everything in this file but rewritten for TypeScript + native fetch
- Same API shape, same error hierarchy, same URL paths, same retry policy

## Follow-on work unlocked

- 29-01 can layer `client.flags`, `client.iam`, `client.audit`, `client.notify` on top of `Transport` + error hierarchy already in place
- v0.2.2 observability modules inherit the same transport + retry + envelope plumbing
- v0.2.4 admin UI can adopt the SDK immediately once 28-02 lands
