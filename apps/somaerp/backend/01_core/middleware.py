"""
Middleware stack:

* RequestIdMiddleware    — attach uuid7 request id, echo as X-Request-ID
* SessionProxyMiddleware — extract bearer token, resolve via tennetctl_client.whoami
* AuditScopeMiddleware   — bind user_id/session_id/org_id/workspace_id to request.state
* error_envelope         — registered as exception handler; SomaerpError → ok:false envelope

`SessionProxyMiddleware` and `AuditScopeMiddleware` are merged into a single
pass to avoid double-resolving the session per request. The split is
conceptual (session_proxy resolves identity, audit_scope binds it).
"""

from __future__ import annotations

from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_errors = import_module("apps.somaerp.backend.01_core.errors")
_response = import_module("apps.somaerp.backend.01_core.response")
_id = import_module("apps.somaerp.backend.01_core.id")


async def _somaerp_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    err = exc  # SomaerpError at runtime
    return _response.error_response(
        err.code,        # type: ignore[attr-defined]
        err.message,     # type: ignore[attr-defined]
        err.status_code, # type: ignore[attr-defined]
    )


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or _id.uuid7()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip() or None
    return None


class SessionProxyMiddleware(BaseHTTPMiddleware):
    """Forward inbound bearer to tennetctl /v1/auth/me; bind identity to request.state.

    Open by default — never rejects. Protected routes call require_user(request).
    Also serves the audit_scope role: the four-tuple
    (user_id, session_id, org_id, workspace_id) is bound to request.state for
    downstream audit emissions.
    """

    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None
        request.state.session_id = None
        request.state.org_id = None
        request.state.workspace_id = None
        request.state.auth_token = None

        token = _extract_token(request)
        client = getattr(request.app.state, "tennetctl", None)
        if token and client is not None:
            try:
                me = await client.get_me(token)
                user = me.get("user") or {}
                session = me.get("session") or {}
                request.state.user_id = user.get("id")
                request.state.session_id = session.get("id")
                request.state.org_id = session.get("org_id")
                request.state.workspace_id = session.get("workspace_id")
                request.state.auth_token = token
            except _errors.SomaerpError:
                pass
            except Exception:
                pass

        return await call_next(request)


def require_user(request: Request) -> dict:
    """Dependency-style guard. Returns identity dict or raises AuthError."""
    if not request.state.user_id:
        raise _errors.AuthError("Authentication required.")
    return {
        "user_id": request.state.user_id,
        "session_id": request.state.session_id,
        "org_id": request.state.org_id,
        "workspace_id": request.state.workspace_id,
        "token": request.state.auth_token,
    }


def register(app: FastAPI) -> None:
    app.add_exception_handler(_errors.SomaerpError, _somaerp_error_handler)
    app.add_middleware(SessionProxyMiddleware)
    app.add_middleware(RequestIdMiddleware)
