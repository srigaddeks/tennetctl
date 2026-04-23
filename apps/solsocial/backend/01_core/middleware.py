"""
Request ID, session resolution (via tennetctl), and error-envelope middleware.

No local session/user/api-key tables. The inbound bearer token is forwarded
to tennetctl `/v1/auth/me`, and the returned identity is cached on
request.state for the duration of the request.
"""

from __future__ import annotations

from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_errors = import_module("apps.solsocial.backend.01_core.errors")
_response = import_module("apps.solsocial.backend.01_core.response")
_id = import_module("apps.solsocial.backend.01_core.id")


async def _app_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    app_exc = exc  # _errors.AppError at runtime; typed as Exception for FastAPI handler shape
    return _response.error_response(app_exc.code, app_exc.message, app_exc.status_code)  # type: ignore[attr-defined]


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = _id.uuid7()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def _extract_token(request: Request) -> str | None:
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip() or None
    explicit = request.headers.get("x-session-token")
    if explicit:
        return explicit.strip() or None
    return None


class SessionProxyMiddleware(BaseHTTPMiddleware):
    """Forward the inbound bearer token to tennetctl /v1/auth/me.

    Open by default — never rejects. Protected routes call
    `require_user(request)` below to enforce auth.
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
                me = await client.whoami(token)
                user = me.get("user") or {}
                session = me.get("session") or {}
                request.state.user_id = user.get("id")
                request.state.session_id = session.get("id")
                request.state.org_id = session.get("org_id")
                request.state.workspace_id = session.get("workspace_id")
                request.state.auth_token = token
            except _errors.AppError:
                # Treat invalid tokens as anonymous — routes guard themselves.
                pass
            except Exception:
                pass

        return await call_next(request)


def require_user(request: Request) -> dict:
    """Dependency-style guard. Returns identity dict or raises."""
    if not request.state.user_id:
        raise _errors.UnauthorizedError("Authentication required.")
    return {
        "user_id": request.state.user_id,
        "session_id": request.state.session_id,
        "org_id": request.state.org_id,
        "workspace_id": request.state.workspace_id,
        "token": request.state.auth_token,
    }


def register(app: FastAPI) -> None:
    app.add_exception_handler(_errors.AppError, _app_error_handler)
    app.add_middleware(SessionProxyMiddleware)
    app.add_middleware(RequestIdMiddleware)
