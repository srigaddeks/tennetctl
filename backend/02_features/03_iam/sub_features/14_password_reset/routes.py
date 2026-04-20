"""FastAPI routes for iam.password_reset."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.14_password_reset.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.14_password_reset.service"
)
_rate_limit: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.rate_limit"
)
_users_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.schemas"
)
_auth_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.schemas"
)

PasswordResetRequestBody  = _schemas.PasswordResetRequestBody
PasswordResetCompleteBody = _schemas.PasswordResetCompleteBody

router = APIRouter(prefix="/v1/auth/password-reset", tags=["iam.password_reset"])

SESSION_COOKIE = "tennetctl_session"


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        extras={"pool": pool},
    )


def _vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError("VAULT_DISABLED", "Vault not configured.", 503)
    return vault


def _set_session_cookie(request: Request, response: Response, token: str, max_age: int) -> None:
    secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"
    response.set_cookie(
        key=SESSION_COOKIE, value=token, max_age=max_age,
        httponly=True, samesite="lax", secure=secure, path="/",
    )


@router.post(
    "/request",
    status_code=200,
    dependencies=[Depends(_rate_limit.auth_rate_limit(
        "password_reset.request", max_requests=3, window_seconds=60,
    ))],
)
async def request_reset(body: PasswordResetRequestBody, request: Request) -> dict:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    ip = request.client.host if request.client else None
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.request_reset(
                pool, conn, ctx,
                email=str(body.email),
                vault_client=vault,
                ip_address=ip,
            )
    return _response.success({"sent": True, "message": "If that email is registered, a reset link is on its way."})


@router.post("/complete", status_code=200)
async def complete_reset(body: PasswordResetCompleteBody, request: Request) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            session_token, user, session = await _service.complete_reset(
                pool, conn, ctx,
                raw_token=body.token,
                new_password=body.new_password,
                vault_client=vault,
            )
    user_clean = _users_schemas.UserRead(**user).model_dump()
    session_clean = _auth_schemas.SessionMeta(**session).model_dump()
    payload = {"token": session_token, "user": user_clean, "session": session_clean}
    resp = _response.success_response(payload, status_code=200)
    from datetime import datetime, timezone
    exp = session.get("expires_at")
    if isinstance(exp, str):
        delta = datetime.fromisoformat(exp).replace(tzinfo=None) - datetime.now(timezone.utc).replace(tzinfo=None)
        max_age = max(60, int(delta.total_seconds()))
    else:
        max_age = 7 * 24 * 3600
    _set_session_cookie(request, resp, session_token, max_age)
    return resp
