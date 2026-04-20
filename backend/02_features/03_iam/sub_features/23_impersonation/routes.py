"""iam.impersonation — FastAPI routes."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.23_impersonation.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.23_impersonation.schemas"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

StartImpersonationBody = _schemas.StartImpersonationBody

router = APIRouter(prefix="/v1/iam/impersonation", tags=["iam.impersonation"])


def _require_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return user_id


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="admin",
        pool=pool,
        extras={"pool": pool},
    )


@router.get("")
async def get_impersonation_status(request: Request) -> Any:
    _require_user(request)
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        return _resp.success_response({"active": False})
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        status = await _service.get_active_impersonation_status(conn, session_id=session_id)
    return _resp.success_response(status)


@router.post("", status_code=201)
async def start_impersonation(request: Request, body: StartImpersonationBody) -> Any:
    user_id = _require_user(request)
    session_id = getattr(request.state, "session_id", None)
    org_id = getattr(request.state, "org_id", None)
    pool = request.app.state.pool
    vault = request.app.state.vault
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        token, imp = await _service.start_impersonation(
            pool, conn, ctx, vault,
            impersonator_user_id=user_id,
            target_user_id=body.target_user_id,
            org_id=org_id or "",
            current_session_id=session_id or "",
        )
    data = {
        "session_token": token,
        "impersonation_id": imp["id"],
        "impersonated_user_id": imp["impersonated_user_id"],
        "expires_at": imp["expires_at"],
    }
    return JSONResponse(content=_resp.success(data), status_code=201)


@router.delete("", status_code=204)
async def end_impersonation(request: Request) -> None:
    user_id = _require_user(request)
    session_id = getattr(request.state, "session_id", None)
    if not session_id:
        raise _errors.NotFoundError("No active session.")
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        await _service.end_impersonation(
            pool, conn, ctx,
            current_session_id=session_id,
            impersonator_user_id=user_id,
        )
    return None
