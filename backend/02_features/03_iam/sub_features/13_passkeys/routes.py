"""FastAPI routes for iam.passkeys (WebAuthn)."""

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
    "backend.02_features.03_iam.sub_features.13_passkeys.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.13_passkeys.service"
)
_users_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.schemas"
)
_auth_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.10_auth.schemas"
)

PasskeyRegisterBeginRequest  = _schemas.PasskeyRegisterBeginRequest
PasskeyRegisterCompleteRequest = _schemas.PasskeyRegisterCompleteRequest
PasskeyAuthBeginRequest      = _schemas.PasskeyAuthBeginRequest
PasskeyAuthCompleteRequest   = _schemas.PasskeyAuthCompleteRequest

router = APIRouter(prefix="/v1/auth/passkeys", tags=["iam.passkeys"])

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
        pool=pool,
        extras={"pool": pool},
    )


def _vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError("VAULT_DISABLED", "Vault not configured.", 503)
    return vault


def _require_auth(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHENTICATED", "Authentication required.", 401)
    return user_id


def _set_session_cookie(request: Request, response: Response, token: str, max_age: int) -> None:
    secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto", "").lower() == "https"
    response.set_cookie(
        key=SESSION_COOKIE, value=token, max_age=max_age,
        httponly=True, samesite="lax", secure=secure, path="/",
    )


@router.post("/register/begin", status_code=200)
async def register_begin(body: PasskeyRegisterBeginRequest, request: Request) -> dict:
    user_id = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _service.register_begin(conn, user_id=user_id, device_name=body.device_name)
    return _response.success(result)


@router.post("/register/complete", status_code=201)
async def register_complete(body: PasskeyRegisterCompleteRequest, request: Request) -> dict:
    user_id = _require_auth(request)
    vault = _vault(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            result = await _service.register_complete(
                conn,
                user_id=user_id,
                challenge_id=body.challenge_id,
                credential_json=body.credential_json,
                vault_client=vault,
                pool=pool,
                ctx=ctx,
            )
    return _response.success_response(result, status_code=201)


@router.post("/auth/begin", status_code=200)
async def auth_begin(body: PasskeyAuthBeginRequest, request: Request) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _service.auth_begin(conn, email=body.email)
    return _response.success(result)


@router.post("/auth/complete", status_code=200)
async def auth_complete(body: PasskeyAuthCompleteRequest, request: Request) -> Response:
    vault = _vault(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            session_token, user, session = await _service.auth_complete(
                conn,
                challenge_id=body.challenge_id,
                credential_json=body.credential_json,
                vault_client=vault,
                org_id=ctx.org_id,
                pool=pool,
                ctx=ctx,
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


@router.get("", status_code=200)
async def list_passkeys(request: Request) -> dict:
    user_id = _require_auth(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _service.list_credentials(conn, user_id=user_id)
    return _response.success({"items": rows, "total": len(rows)})


@router.delete("/{cred_id}", status_code=204)
async def delete_passkey(cred_id: str, request: Request) -> Response:
    user_id = _require_auth(request)
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_credential(
                conn, cred_id=cred_id, user_id=user_id,
                pool=pool, ctx=ctx,
            )
    return Response(status_code=204)
