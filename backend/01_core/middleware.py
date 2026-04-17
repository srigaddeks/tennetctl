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
    """Validate the inbound session token or API key and inject scope onto state.

    Two authentication paths are recognised, in priority order:

      1. API key — Authorization: Bearer nk_<key_id>.<secret>
         → state.user_id + org_id populated from the key's owner
         → state.session_id stays None
         → state.api_key_id + state.scopes populated
         → require_scope() enforces per-route scope requirements

      2. Session token — session cookie, x-session-token header, or
         Bearer (non-nk_) header.
         → state.{user_id, session_id, org_id, workspace_id} populated
         → state.scopes = None (session users have all scopes)

    Open by default — never rejects. Routes guard themselves via
    request.state.user_id or require_scope().
    """

    async def dispatch(self, request: Request, call_next):
        request.state.user_id = None
        request.state.session_id = None
        request.state.org_id = None
        request.state.workspace_id = None
        request.state.api_key_id = None
        request.state.scopes = None  # None = session auth = all scopes

        vault = getattr(request.app.state, "vault", None)
        pool = getattr(request.app.state, "pool", None)

        # Path 1: API key (Bearer with "nk_" prefix).
        auth = request.headers.get("authorization") or ""
        raw_auth = auth.split(" ", 1)[1].strip() if auth.lower().startswith("bearer ") else ""
        if (
            raw_auth.startswith("nk_")
            and vault is not None
            and pool is not None
        ):
            try:
                _api_keys: Any = import_module(
                    "backend.02_features.03_iam.sub_features.15_api_keys.service"
                )
                _api_keys_repo: Any = import_module(
                    "backend.02_features.03_iam.sub_features.15_api_keys.repository"
                )
                async with pool.acquire() as conn:
                    key_row = await _api_keys.validate_token(
                        conn, vault, token=raw_auth,
                    )
                    if key_row is not None:
                        request.state.user_id = key_row["user_id"]
                        request.state.org_id = key_row["org_id"]
                        request.state.api_key_id = key_row["id"]
                        request.state.scopes = list(key_row.get("scopes") or [])
                        # Best-effort — do not block the request on this.
                        try:
                            await _api_keys_repo.touch_last_used(
                                conn, key_id=key_row["key_id"],
                            )
                        except Exception:
                            pass
            except Exception:
                pass
            return await call_next(request)

        # Path 2: Session token (cookie / x-session-token / plain Bearer).
        token = _extract_token(request)
        session_expired = False
        row = None
        if token and vault is not None and pool is not None:
            try:
                _sessions: Any = import_module(
                    "backend.02_features.03_iam.sub_features.09_sessions.service"
                )
                async with pool.acquire() as conn:
                    row = await _sessions.validate_token(
                        conn, vault_client=vault, token=token,
                    )
                    if row is not None:
                        # Plan 20-04: check idle + absolute TTL timeouts.
                        auth_policy = getattr(request.app.state, "auth_policy", None)
                        if auth_policy is not None:
                            try:
                                _ctx_mod: Any = import_module("backend.01_catalog.context")
                                ctx = _ctx_mod.NodeContext(
                                    audit_category="setup",
                                    trace_id=_id.uuid7(),
                                    span_id=_id.uuid7(),
                                    user_id=row.get("user_id"),
                                    session_id=row["id"],
                                    org_id=row.get("org_id"),
                                )
                                reason = await _sessions.check_session_timeouts(
                                    pool, conn, ctx,
                                    session_id=row["id"],
                                    auth_policy=auth_policy,
                                    org_id=row.get("org_id"),
                                )
                                if reason is not None:
                                    row = None
                                    session_expired = True
                            except Exception:
                                pass
            except Exception:
                row = None
            if row is not None:
                request.state.user_id = row["user_id"]
                request.state.session_id = row["id"]
                request.state.org_id = row.get("org_id")
                request.state.workspace_id = row.get("workspace_id")
                # Plan 20-04: bump last_activity_at fire-and-forget.
                import asyncio as _asyncio
                _sessions_repo: Any = import_module(
                    "backend.02_features.03_iam.sub_features.09_sessions.repository"
                )
                session_id_for_bump = row["id"]

                async def _bump_activity():
                    try:
                        async with pool.acquire() as bump_conn:
                            await _sessions_repo.bump_last_activity(
                                bump_conn, session_id=session_id_for_bump,
                            )
                    except Exception:
                        pass
                _asyncio.create_task(_bump_activity())

        if session_expired:
            return _response.error_response("SESSION_EXPIRED", "Session expired.", 401)

        return await call_next(request)


def require_scope(request: Request, scope: str) -> None:
    """Raise 403 if the caller is API-key-authenticated and lacks `scope`.

    Session users (state.scopes == None) pass through — their permission model
    is the session cookie and route-level checks already applied. API keys
    must hold `scope` explicitly.

    Call at the top of any protected route:
        require_scope(request, "notify:send")
    """
    if getattr(request.state, "user_id", None) is None:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    scopes = getattr(request.state, "scopes", None)
    if scopes is None:
        return  # session user
    if scope not in scopes:
        raise _errors.AppError(
            "FORBIDDEN",
            f"API key missing required scope: {scope}",
            403,
        )


def register_middleware(app: FastAPI) -> None:
    """Register all middleware and exception handlers on the app."""
    app.add_exception_handler(_errors.AppError, _app_error_handler)
    # Order: SessionMiddleware first (innermost — runs after RequestId set),
    # so request.state.request_id is available inside session resolution.
    app.add_middleware(SessionMiddleware)
    app.add_middleware(RequestIdMiddleware)
