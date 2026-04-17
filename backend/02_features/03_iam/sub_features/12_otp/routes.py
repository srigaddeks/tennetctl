"""FastAPI routes for iam.otp (email OTP + TOTP)."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.12_otp.service"
)
_users_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.schemas"
)
_auth_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.schemas"
)
OtpRequest = _schemas.OtpRequest
OtpVerify = _schemas.OtpVerify
TotpSetupRequest = _schemas.TotpSetupRequest
TotpVerify = _schemas.TotpVerify

router = APIRouter(prefix="/v1/auth", tags=["iam.otp"])

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


# ─── Email OTP ────────────────────────────────────────────────────────────────

@router.post("/otp/request", status_code=200)
async def request_otp_route(body: OtpRequest, request: Request) -> dict:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.request_otp(pool, conn, ctx, email=str(body.email), vault_client=vault)
    return _response.success({"sent": True, "message": "If that email is registered, a code is on its way."})


@router.post("/otp/verify", status_code=200)
async def verify_otp_route(body: OtpVerify, request: Request) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            session_token, user, session = await _service.verify_otp(
                pool, conn, ctx, email=str(body.email), code=body.code, vault_client=vault,
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


# ─── TOTP ─────────────────────────────────────────────────────────────────────

@router.post("/totp/setup", status_code=201)
async def setup_totp_route(body: TotpSetupRequest, request: Request) -> dict:
    pool = request.app.state.pool
    vault = _vault(request)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHENTICATED", "Authentication required.", 401)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _service.setup_totp(
                pool, conn, ctx,
                user_id=user_id, device_name=body.device_name, vault_client=vault,
            )
    return _response.success_response(result, status_code=201)


@router.post("/totp/verify", status_code=200)
async def verify_totp_route(body: TotpVerify, request: Request) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            session_token, user, session = await _service.verify_totp(
                pool, conn, ctx, credential_id=body.credential_id, code=body.code, vault_client=vault,
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


@router.get("/totp", status_code=200)
async def list_totp_route(request: Request) -> dict:
    pool = request.app.state.pool
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHENTICATED", "Authentication required.", 401)
    async with pool.acquire() as conn:
        rows = await _service.list_totp(conn, user_id=user_id)
    return _response.success({"items": rows, "total": len(rows)})


@router.delete("/totp/{credential_id}", status_code=204)
async def delete_totp_route(credential_id: str, request: Request) -> Response:
    pool = request.app.state.pool
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHENTICATED", "Authentication required.", 401)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            from dataclasses import replace as _replace
            ctx = _replace(ctx_base, conn=conn)
            await _service.delete_totp(conn, credential_id=credential_id, user_id=user_id, pool=pool, ctx=ctx)
    return Response(status_code=204)
