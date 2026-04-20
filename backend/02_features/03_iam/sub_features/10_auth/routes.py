"""
iam.auth — FastAPI routes.

Six routes (all under /v1/auth, no item path needed):
  POST /v1/auth/signup    — email_password user + session
  POST /v1/auth/signin    — verify password + mint session
  POST /v1/auth/signout   — revoke current session (auth-required)
  GET  /v1/auth/me        — return current user (auth-required)
  POST /v1/auth/google    — exchange code, upsert google_oauth user + session
  POST /v1/auth/github    — exchange code, upsert github_oauth user + session

The session token is returned in the JSON envelope AND set as an httpOnly
cookie. The frontend reads it from the cookie; CLI / API clients use the body
token + Authorization header.
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, Request, Response

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.service"
)
_rate_limit: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.rate_limit"
)
_users_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.schemas"
)

SignupBody = _schemas.SignupBody
SigninBody = _schemas.SigninBody
OAuthCallbackBody = _schemas.OAuthCallbackBody
SessionMeta = _schemas.SessionMeta
AuthResponse = _schemas.AuthResponse

router = APIRouter(prefix="/v1/auth", tags=["iam.auth"])

SESSION_COOKIE = "tennetctl_session"


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None)
            or request.headers.get("x-user-id"),
        session_id=getattr(request.state, "session_id", None)
            or request.headers.get("x-session-id"),
        org_id=getattr(request.state, "org_id", None)
            or request.headers.get("x-org-id"),
        workspace_id=getattr(request.state, "workspace_id", None)
            or request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        extras={"pool": pool},
    )


def _request_is_https(request: Request) -> bool:
    """True when the inbound request is HTTPS, either direct or via a TLS-terminating proxy."""
    if request.url.scheme == "https":
        return True
    return request.headers.get("x-forwarded-proto", "").lower() == "https"


def _set_session_cookie(
    request: Request, response: Response, token: str, max_age_seconds: int,
) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=max_age_seconds,
        httponly=True,
        samesite="lax",
        secure=_request_is_https(request),
        path="/",
    )


def _vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError(
            "VAULT_DISABLED",
            "vault module is not enabled; auth requires vault for password pepper + session signing key",
            status_code=503,
        )
    return vault


def _build_response_payload(token: str, user: dict, session: dict) -> dict:
    user_clean = _users_schemas.UserRead(**user).model_dump()
    session_clean = SessionMeta(**session).model_dump()
    return {
        "token": token,
        "user": user_clean,
        "session": session_clean,
    }


def _seconds_until(expires_at: object) -> int:
    from datetime import datetime, timezone
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if not isinstance(expires_at, datetime):
        return 7 * 24 * 3600
    delta = expires_at - datetime.now(timezone.utc).replace(tzinfo=None)
    return max(60, int(delta.total_seconds()))


@router.post("/signup", status_code=201)
async def signup_route(request: Request, body: SignupBody) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            token, user, session = await _service.signup(
                pool, conn, ctx,
                vault_client=vault,
                email=body.email,
                display_name=body.display_name,
                password=body.password,
            )
    payload = _build_response_payload(token, user, session)
    response = _response.success_response(payload, status_code=201)
    _set_session_cookie(request, response, token, _seconds_until(session["expires_at"]))
    return response


@router.post(
    "/signin",
    status_code=200,
    dependencies=[Depends(_rate_limit.auth_rate_limit(
        "auth.signin", max_requests=10, window_seconds=60,
    ))],
)
async def signin_route(request: Request, body: SigninBody) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    # Capture client UA + IP so /account/sessions can show "Chrome on macOS
    # from 10.0.0.4" rather than a raw session-ID prefix.
    ua = request.headers.get("user-agent")
    xff = request.headers.get("x-forwarded-for")
    client_ip = xff.split(",")[0].strip() if xff else (
        request.client.host if request.client else None
    )
    # Session-fixation defense: parse any pre-existing cookie's session_id so
    # the service layer can revoke it after minting a fresh session (Plan 38-01).
    previous_session_id = None
    incoming_cookie = request.cookies.get(SESSION_COOKIE)
    if incoming_cookie:
        try:
            _sessions_service: Any = import_module(
                "backend.02_features.03_iam.sub_features.09_sessions.service"
            )
            signing_key = await _sessions_service._signing_key_bytes(vault)
            previous_session_id = _sessions_service.parse_token(
                incoming_cookie, signing_key,
            )
        except Exception:
            previous_session_id = None  # tampered / invalid cookie — ignore
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            token, user, session = await _service.signin(
                pool, conn, ctx,
                vault_client=vault,
                email=body.email,
                password=body.password,
                source_ip=client_ip,
                user_agent=ua,
                previous_session_id=previous_session_id,
            )
    payload = _build_response_payload(token, user, session)
    response = _response.success_response(payload, status_code=200)
    _set_session_cookie(request, response, token, _seconds_until(session["expires_at"]))
    return response


@router.post("/signout", status_code=200)
async def signout_route(request: Request) -> Response:
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not session_id:
        raise _errors.UnauthorizedError("not signed in")

    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.signout(
                pool, conn, ctx,
                session_id=session_id, user_id=user_id,
            )
    response = _response.success_response({"signed_out": True}, status_code=200)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@router.get("/me", status_code=200)
async def me_route(request: Request) -> dict:
    user_id = getattr(request.state, "user_id", None)
    session_id = getattr(request.state, "session_id", None)
    if not user_id or not session_id:
        raise _errors.UnauthorizedError("not signed in")

    pool = request.app.state.pool
    _sessions_repo: Any = import_module(
        "backend.02_features.03_iam.sub_features.09_sessions.repository"
    )
    _ev_repo: Any = import_module(
        "backend.02_features.03_iam.sub_features.16_email_verification.repository"
    )
    async with pool.acquire() as conn:
        user = await _service.me(conn, user_id=user_id)
        session_row = await _sessions_repo.get_by_id(conn, session_id)
        email_verified_at = await _ev_repo.get_email_verified_at(conn, user_id)
    if user is None:
        raise _errors.UnauthorizedError("session points to a deleted user")
    session_payload = SessionMeta(**session_row).model_dump() if session_row else {
        "id": session_id,
        "user_id": user_id,
        "org_id": getattr(request.state, "org_id", None),
        "workspace_id": getattr(request.state, "workspace_id", None),
        "expires_at": "",
        "revoked_at": None,
        "is_valid": False,
    }
    user_data = _users_schemas.UserRead(**user).model_dump()
    user_data["email_verified"] = email_verified_at is not None
    return _response.success({
        "user": user_data,
        "session": session_payload,
    })


async def _oauth_route(request: Request, body: OAuthCallbackBody, provider: str) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            token, user, session = await _service.oauth_signin(
                pool, conn, ctx,
                vault_client=vault,
                provider=provider,
                code=body.code,
                redirect_uri=body.redirect_uri,
            )
    payload = _build_response_payload(token, user, session)
    response = _response.success_response(payload, status_code=200)
    _set_session_cookie(request, response, token, _seconds_until(session["expires_at"]))
    return response


@router.post("/google", status_code=200)
async def google_oauth_route(request: Request, body: OAuthCallbackBody) -> Response:
    return await _oauth_route(request, body, "google")


@router.post("/github", status_code=200)
async def github_oauth_route(request: Request, body: OAuthCallbackBody) -> Response:
    return await _oauth_route(request, body, "github")
