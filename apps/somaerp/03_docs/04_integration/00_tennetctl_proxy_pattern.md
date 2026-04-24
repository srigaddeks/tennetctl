# tennetctl Proxy Pattern (somaerp)

This doc specifies how `apps/somaerp/backend` talks to tennetctl. It is the somaerp adaptation of the proven solsocial pattern (`apps/solsocial/backend/01_core/tennetctl_client.py`). Read solsocial's client first if you have not — it is the reference implementation.

## Two auth modes, by call type

| Mode | Used for | Auth header | Identity carried |
| --- | --- | --- | --- |
| End-user identity | resolving the current session into a user + workspace | `Authorization: Bearer {user_session_token}` | session-bound user_id, session_id, org_id, workspace_id |
| Service-to-service | audit emit, notify send, vault read/write/rotate, flag evaluation, role/flag listings, application lookup | `Authorization: Bearer {SOMAERP_SERVICE_API_KEY}` plus `x-application-id: {somaerp_application_id}` | service identity; user/workspace context passed explicitly per call |

The user session token is forwarded ONLY for `whoami`. Every other call uses the service API key. End-user context (actor_user_id, org_id, workspace_id) for service calls is extracted from `whoami` and passed explicitly per call (audit emission, notify, etc.).

## Boot sequence

1. somaerp reads `SOMAERP_TENNETCTL_BASE_URL` and `SOMAERP_TENNETCTL_KEY_FILE` from env.
2. somaerp instantiates `TennetCTLClient(base_url, service_api_key)`, calls `await client.start()` to open the httpx pool.
3. somaerp calls `await client.resolve_application(code="somaerp", org_id=PLATFORM_ORG_ID)`. This caches `application_id` and `org_id` on the client; every outbound call thereafter auto-stamps `x-application-id`.
4. App is ready; FastAPI lifespan completes.

On shutdown: `await client.stop()` closes the httpx pool.

## Request-time pattern (per HTTP request to somaerp)

```text
incoming request to apps/somaerp
    │
    ├─ middleware extracts session bearer from Authorization header
    │
    ├─ middleware calls client.whoami(session_bearer)
    │      → returns {user, session, org, workspace}
    │
    ├─ middleware attaches user_id/session_id/org_id/workspace_id to request.state
    │
    ├─ route handler runs business logic; calls service layer with conn + scope
    │
    ├─ service layer calls client.emit_audit(...) on every mutation,
    │      passing actor_user_id/org_id/workspace_id from request.state
    │
    └─ response wrapped in {ok, data, error} envelope
```

## Envelope unwrapping

tennetctl returns every response in the canonical envelope:

```json
{ "ok": true,  "data": {...} }
{ "ok": false, "error": { "code": "NOT_FOUND", "message": "..." } }
```

The proxy client unwraps this on every response. Non-JSON or `ok: false` responses raise typed errors:

| HTTP status | Typed error |
| --- | --- |
| 401 | `UnauthorizedError(code, message)` |
| 403 | `ForbiddenError(code, message)` |
| 404 | `NotFoundError(code, message)` |
| 4xx (other) | `AppError(code, message, status_code)` |
| 5xx | `UpstreamError(code, message, status_code=502)` |
| non-JSON | `UpstreamError("tennetctl returned non-JSON: {status}")` |

These typed errors are mapped by somaerp's error middleware back into the `{ok: false, error}` envelope returned to the somaerp client.

## Audit scope propagation (mandatory four-tuple)

Every mutation in somaerp emits an audit event. The four-tuple (user_id, session_id, org_id, workspace_id) is mandatory per the project-wide audit-scope rule. The proxy client method signature for `emit_audit` makes the explicit-pass requirement obvious:

```python
async def emit_audit(
    self,
    *,
    event_key: str,
    outcome: str,                           # "success" | "failure"
    metadata: dict | None = None,
    actor_user_id: str | None = None,       # from request.state.user_id
    org_id: str | None = None,              # from request.state.org_id (defaults to client._org_id)
    workspace_id: str | None = None,        # from request.state.workspace_id
) -> None:
    """Best-effort audit emission — never raises into the business flow."""
```

`session_id` is carried by tennetctl's audit ingest middleware via the service API key header chain; somaerp does not pass it explicitly per call. The setup-mode bypass (no user_id required) is invoked by passing `actor_user_id=None` and `metadata={"category": "setup"}` during tenant bootstrap (see `04_integration/02_audit_emission.md`).

## Method signatures (somaerp client surface)

The somaerp `TennetCTLClient` exposes:

```python
class TennetCTLClient:
    async def start(self) -> None: ...
    async def stop(self) -> None: ...

    # Boot
    async def resolve_application(self, *, code: str, org_id: str) -> dict | None: ...

    # End-user identity (session token)
    async def whoami(self, user_token: str) -> dict: ...

    # Audit
    async def emit_audit(self, *, event_key: str, outcome: str,
                         metadata: dict | None = None,
                         actor_user_id: str | None = None,
                         org_id: str | None = None,
                         workspace_id: str | None = None) -> None: ...

    # Vault — secrets and (future) blobs
    async def vault_put(self, payload: dict) -> dict: ...
    async def vault_reveal(self, key: str, *, scope: str = "workspace",
                           org_id: str | None = None,
                           workspace_id: str | None = None) -> str: ...
    async def vault_rotate(self, key: str, payload: dict, *, scope: str = "workspace",
                           org_id: str | None = None,
                           workspace_id: str | None = None) -> dict: ...
    async def vault_delete(self, key: str, *, scope: str, org_id: str) -> None: ...
    async def vault_list(self, *, scope: str = "workspace",
                         org_id: str | None = None,
                         workspace_id: str | None = None) -> list[dict]: ...

    # Notify
    async def notify_send(self, payload: dict) -> dict: ...

    # Feature flags
    async def feature_flag(self, key: str, context: dict | None = None) -> Any: ...
    async def list_my_flags(self) -> list[dict]: ...

    # IAM (read-only from somaerp)
    async def list_my_roles(self) -> list[dict]: ...
```

These are signatures only — actual implementation is shipped in plan 56-02. The only difference from the solsocial client is the default vault scope (`workspace` for somaerp because tenant_id = workspace_id; solsocial defaults to `org`).

## Failure handling

- `whoami` failure → 401 returned to the somaerp caller (session invalid).
- `emit_audit` failure → swallowed; never breaks the business flow. Logged at warning level. Audit reliability is tennetctl's responsibility.
- `notify_send` failure → returned as a typed error; the calling service layer decides whether to retry or surface.
- `vault_reveal` failure → typed error propagates; somaerp routes return 502 (UpstreamError) or 404 (NotFoundError) accordingly.
- `feature_flag` failure → swallowed; default value returned. Treat flags as advisory.

## Deployment configuration

| Env var | Purpose |
| --- | --- |
| `SOMAERP_TENNETCTL_BASE_URL` | tennetctl base URL (e.g. `http://127.0.0.1:51734`) |
| `SOMAERP_TENNETCTL_KEY_FILE` | absolute path to a file containing the service API key (`nk_...`) |
| `SOMAERP_PLATFORM_ORG_ID` | the platform org UUID for `resolve_application` |

The service API key is minted in tennetctl via `POST /v1/api-keys` with the scopes somaerp needs:

- `audit:write`
- `notify:send`
- `vault:read:workspace`, `vault:write:workspace`, `vault:reveal:workspace`, `vault:list:workspace`
- `flags:read`
- `iam:roles:read`
- `iam:applications:read`

## Related documents

- `apps/solsocial/backend/01_core/tennetctl_client.py` — the reference implementation
- `apps/somaerp/03_docs/00_main/08_decisions/008_tennetctl_primitive_consumption.md`
- `apps/somaerp/03_docs/04_integration/01_auth_iam_consumption.md` (Task 3)
- `apps/somaerp/03_docs/04_integration/02_audit_emission.md` (Task 3)
- `apps/somaerp/03_docs/04_integration/03_vault_for_secrets_and_blobs.md` (Task 3)
- `apps/somaerp/03_docs/04_integration/04_notify_integration.md` (Task 3)
- `apps/somaerp/03_docs/04_integration/05_flows_for_workflows.md` (Task 3)
