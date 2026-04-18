"""iam.tos — FastAPI routes."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module("backend.02_features.03_iam.sub_features.27_tos.service")
_schemas: Any = import_module("backend.02_features.03_iam.sub_features.27_tos.schemas")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

router = APIRouter(prefix="/v1/tos", tags=["iam.tos"])


def _ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup", extras={"pool": pool},
    )


@router.get("/current")
async def get_current(request: Request) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        v = await _service.get_current(conn)
    if v is None:
        return _resp.success_response(None)
    return _resp.success_response(_schemas.TosVersion(**v).model_dump(mode="json"))


@router.get("")
async def list_versions(request: Request) -> Any:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        versions = await _service.list_versions(conn)
    return _resp.success_response([_schemas.TosVersion(**v).model_dump(mode="json") for v in versions])


@router.post("", status_code=201)
async def create_version(request: Request, body: _schemas.TosVersionCreate) -> Any:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    pool = request.app.state.pool
    ctx = _ctx(request, pool)
    async with pool.acquire() as conn:
        v = await _service.create_version(
            pool, conn, ctx, version=body.version, title=body.title, body_markdown=body.body_markdown,
        )
    return _resp.success_response(_schemas.TosVersion(**v).model_dump(mode="json"), status_code=201)


@router.post("/{version_id}/effective")
async def mark_effective(version_id: str, request: Request, body: _schemas.TosVersionPublish) -> Any:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    pool = request.app.state.pool
    ctx = _ctx(request, pool)
    async with pool.acquire() as conn:
        v = await _service.mark_effective(pool, conn, ctx, version_id=version_id, effective_at=body.effective_at)
    return _resp.success_response(_schemas.TosVersion(**v).model_dump(mode="json"))


@router.post("/accept")
async def accept_tos(request: Request, body: _schemas.TosAcceptBody) -> Any:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    pool = request.app.state.pool
    ctx = _ctx(request, pool)
    forwarded_for = request.headers.get("x-forwarded-for")
    client_ip = (forwarded_for.split(",")[0].strip() if forwarded_for
                 else (request.client.host if request.client else None))
    async with pool.acquire() as conn:
        await _service.accept_tos(
            pool, conn, ctx, user_id=uid, version_id=body.version_id, client_ip=client_ip,
        )
    return _resp.success_response({"accepted": True})
