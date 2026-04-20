"""
iam.orgs — FastAPI routes (5-endpoint shape).

Routes are the transaction boundary: they acquire a conn from the pool and, for
writes, open a transaction. The NodeContext carries pool into service functions
via extras['pool'] so audit emission (via run_node) can look up handler metadata.

v1 has no auth. Routes extract x-user-id / x-session-id / x-org-id / x-workspace-id
headers with sensible defaults and set audit_category='setup' for mutations so the
evt_audit scope CHECK does not reject unauthenticated boot-time writes. Real
auth / JWT parsing arrives in Phase 5+ (Users).
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.01_orgs.service"
)

OrgCreate = _schemas.OrgCreate
OrgUpdate = _schemas.OrgUpdate
OrgRead = _schemas.OrgRead

router = APIRouter(prefix="/v1/orgs", tags=["iam.orgs"])


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    """
    Construct NodeContext from request headers + app pool.

    `pool` is stashed in extras so downstream audit emission (run_node) can
    look up handler metadata. audit_category='setup' for v1 mutations — the
    evt_audit CHECK constraint bypasses scope requirements for setup rows
    until Phase 5+ lands JWT-backed auth.
    """
    state = request.state
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    session_id = getattr(state, "session_id", None) or request.headers.get("x-session-id")
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    workspace_id = getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id")

    return _catalog_ctx.NodeContext(
        user_id=user_id,
        session_id=session_id,
        org_id=org_id,
        workspace_id=workspace_id,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_orgs_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_orgs(
            conn,
            ctx,
            limit=limit,
            offset=offset,
            is_active=is_active,
        )
    data = [OrgRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_org_route(
    request: Request,
    body: OrgCreate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            org = await _service.create_org(
                pool,
                conn,
                ctx,
                slug=body.slug,
                display_name=body.display_name,
            )
    return _response.success(OrgRead(**org).model_dump())


@router.get("/{org_id}", status_code=200)
async def get_org_route(request: Request, org_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        org = await _service.get_org(conn, ctx, org_id=org_id)
    if org is None:
        raise _errors.NotFoundError(f"Org {org_id!r} not found.")
    return _response.success(OrgRead(**org).model_dump())


@router.patch("/{org_id}", status_code=200)
async def update_org_route(
    request: Request,
    org_id: str,
    body: OrgUpdate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            org = await _service.update_org(
                pool,
                conn,
                ctx,
                org_id=org_id,
                slug=body.slug,
                display_name=body.display_name,
            )
    return _response.success(OrgRead(**org).model_dump())


@router.delete("/{org_id}", status_code=204)
async def delete_org_route(request: Request, org_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_org(pool, conn, ctx, org_id=org_id)
    return Response(status_code=204)
