"""iam.siem_export — FastAPI routes."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module("backend.02_features.03_iam.sub_features.26_siem_export.service")
_schemas: Any = import_module("backend.02_features.03_iam.sub_features.26_siem_export.schemas")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

router = APIRouter(prefix="/v1/iam/siem-destinations", tags=["iam.siem_export"])


def _require_user(request: Request) -> str:
    uid = getattr(request.state, "user_id", None)
    if not uid:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return uid


def _require_org(request: Request) -> str:
    org_id = getattr(request.state, "org_id", None)
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "Org context required.", 401)
    return org_id


def _ctx(request: Request, pool: Any) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=getattr(request.state, "workspace_id", None),
        trace_id=_core_id.uuid7(), span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


@router.get("")
async def list_destinations(request: Request) -> Any:
    _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        dests = await _service.list_destinations(conn, org_id)
    return _resp.success_response([_schemas.SiemDestination(**d).model_dump(mode="json") for d in dests])


@router.post("", status_code=201)
async def create_destination(request: Request, body: _schemas.SiemDestinationCreate) -> Any:
    _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    ctx = _ctx(request, pool)
    async with pool.acquire() as conn:
        dest = await _service.create_destination(
            pool, conn, ctx, org_id=org_id, kind=body.kind, label=body.label,
            config_jsonb=body.config_jsonb, credentials_vault_key=body.credentials_vault_key,
        )
    return _resp.success_response(_schemas.SiemDestination(**dest).model_dump(mode="json"), status_code=201)


@router.patch("/{dest_id}")
async def update_destination(dest_id: str, request: Request, body: _schemas.SiemDestinationUpdate) -> Any:
    _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    ctx = _ctx(request, pool)
    async with pool.acquire() as conn:
        dest = await _service.update_destination(
            pool, conn, ctx, dest_id=dest_id, org_id=org_id,
            label=body.label, config_jsonb=body.config_jsonb, is_active=body.is_active,
        )
    return _resp.success_response(_schemas.SiemDestination(**dest).model_dump(mode="json"))


@router.delete("/{dest_id}", status_code=204)
async def delete_destination(dest_id: str, request: Request) -> None:
    _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    ctx = _ctx(request, pool)
    async with pool.acquire() as conn:
        await _service.delete_destination(pool, conn, ctx, dest_id=dest_id, org_id=org_id)
    return None
