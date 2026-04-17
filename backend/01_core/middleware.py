"""
FastAPI middleware — error handling, request ID, and session injection.

Registers:
  - AppError exception handler → standard error envelope
  - Request ID middleware → X-Request-ID on every response
  - Session middleware → optional auth: extracts Bearer/x-session-token/cookie,
    validates via iam.sessions, and injects (user_id, session_id, org_id,
    workspace_id) into request.state. Does NOT reject — protected routes guard
    themselves by inspecting request.state.user_id (e.g. /v1/auth/me).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_errors = import_module("backend.01_core.errors")
_response = import_module("backend.01_core.response")
_id = import_module("backend.01_core.id")

SESSION_COOKIE = "tennetctl_session"


async def _app_error_handler(_request: Request, exc: _errors.AppError) -> JSONResponse:
    """Convert AppError into standard error envelope response."""
    return _response.error_response(exc.code, exc.message, exc.status_code)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID header to every response and stash it on request.state."""

    async def dispatch(self, request: Request, call_next):
        request_id = _id.uuid7()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def _extract_token(request: Request) -> str | None:
    """Pull the session token from Bearer header, x-session-token, or cookie."""
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip() or None
    explicit = request.headers.get("x-session-token")
    if explicit:
        return explicit.strip() or None
    cookie = request.cookies.get(SESSION_COOKIE)
    return cookie or None


class SessionMiddleware(BaseHTTPMiddleware):
    """Validate the inbound session token and inject scope onto request.state.

    Open by default — never rejects. Routes that require auth check
    `request.state.user_id` themselves (see iam.auth.routes).
    """

    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None
        request.state.session_id = None
        request.state.org_id = None
        request.state.workspace_id = None

        token = _extract_token(request)
        vault = getattr(request.app.state, "vault", None)
        pool = getattr(request.app.state, "pool", None)
        if token and vault is not None and pool is not None:
            try:
                _sessions: Any = import_module(
                    "backend.02_features.03_iam.sub_features.09_sessions.service"
                )
                async with pool.acquire() as conn:
                    row = await _sessions.validate_token(
                        conn, vault_client=vault, token=token,
                    )
            except Exception:
                row = None
            if row is not None:
                request.state.user_id = row["user_id"]
                request.state.session_id = row["id"]
                request.state.org_id = row.get("org_id")
                request.state.workspace_id = row.get("workspace_id")

        return await call_next(request)


def register_middleware(app: FastAPI) -> None:
    """Register all middleware and exception handlers on the app."""
    app.add_exception_handler(_errors.AppError, _app_error_handler)
    # Order: SessionMiddleware first (innermost — runs after RequestId set),
    # so request.state.request_id is available inside session resolution.
    app.add_middleware(SessionMiddleware)
    app.add_middleware(RequestIdMiddleware)
