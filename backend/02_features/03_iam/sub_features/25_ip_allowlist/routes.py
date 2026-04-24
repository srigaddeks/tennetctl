"""iam.ip_allowlist — FastAPI routes."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.25_ip_allowlist.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.25_ip_allowlist.schemas"
)
_authz: Any = import_module(
    "backend.02_features.03_iam.sub_features.29_authz_gates.authz_helpers"
)
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")

IpAllowlistCreate = _schemas.IpAllowlistCreate

router = APIRouter(prefix="/v1/iam/ip-allowlist", tags=["iam.ip_allowlist"])


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
        application_id=getattr(request.state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category="setup",
        pool=pool,
        extras={"pool": pool},
    )


@router.get("")
async def list_entries(request: Request) -> Any:
    user_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        # Verify caller belongs to the requested org — prevents cross-org enumeration.
        await _authz.require_org_member_or_raise(conn, user_id, org_id)
        entries = await _service.list_entries(conn, org_id)
    return _resp.success_response([_schemas.IpAllowlistEntry(**e).model_dump(mode="json") for e in entries])


@router.post("", status_code=201)
async def add_entry(request: Request, body: IpAllowlistCreate) -> Any:
    user_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        # Verify caller belongs to the org before mutating its allowlist.
        await _authz.require_org_member_or_raise(conn, user_id, org_id)
        entry = await _service.add_entry(
            pool, conn, ctx, org_id=org_id, cidr=body.cidr, label=body.label,
        )
    return _resp.success_response(_schemas.IpAllowlistEntry(**entry).model_dump(mode="json"), status_code=201)


@router.delete("/{entry_id}", status_code=204)
async def remove_entry(entry_id: str, request: Request) -> None:
    user_id = _require_user(request)
    org_id = _require_org(request)
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        # Verify caller belongs to the org before deleting its allowlist entry.
        await _authz.require_org_member_or_raise(conn, user_id, org_id)
        await _service.remove_entry(pool, conn, ctx, entry_id=entry_id, org_id=org_id)
    return None
