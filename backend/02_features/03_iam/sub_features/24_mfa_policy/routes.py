"""iam.mfa_policy — FastAPI routes."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.24_mfa_policy.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.24_mfa_policy.schemas"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

MfaPolicyUpdate = _schemas.MfaPolicyUpdate

router = APIRouter(prefix="/v1/iam/mfa-policy", tags=["iam.mfa_policy"])


def _require_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return user_id


def _require_org(request: Request) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "Org context required.", 401)
    return org_id


def _build_ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


@router.get("")
async def get_mfa_policy(request: Request) -> Any:
    user_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        required = await _service.get_mfa_required(conn, org_id)
        totp_enrolled = await _service.is_totp_enrolled(conn, user_id)
    return _resp.success_response({
        "org_id": org_id,
        "required": required,
        "totp_enrolled": totp_enrolled,
    })


@router.put("")
async def set_mfa_policy(request: Request, body: MfaPolicyUpdate) -> Any:
    _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        await _service.set_mfa_required(pool, conn, ctx, org_id=org_id, required=body.required)
    return _resp.success_response({"org_id": org_id, "required": body.required})
