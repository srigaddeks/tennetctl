"""
iam.memberships — FastAPI routes.

Two resource types:
- /v1/org-members      — POST create / GET list / DELETE /{id}
- /v1/workspace-members — POST create / GET list / DELETE /{id}

Lnk rows are immutable (no PATCH), so the individual-GET path is omitted — lists
with (user_id, org_id) or (user_id, workspace_id) filters are the lookup primitive.
"""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.07_memberships.service"
)

OrgMembershipCreate = _schemas.OrgMembershipCreate
OrgMembershipRead = _schemas.OrgMembershipRead
WorkspaceMembershipCreate = _schemas.WorkspaceMembershipCreate
WorkspaceMembershipRead = _schemas.WorkspaceMembershipRead


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    state = request.state
    return _catalog_ctx.NodeContext(
        user_id=getattr(state, "user_id", None) or request.headers.get("x-user-id"),
        session_id=getattr(state, "session_id", None) or request.headers.get("x-session-id"),
        org_id=getattr(state, "org_id", None) or request.headers.get("x-org-id"),
        workspace_id=getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
        application_id=getattr(state, "application_id", None) or request.headers.get("x-application-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


# ── Org membership router ────────────────────────────────────────────

org_router = APIRouter(prefix="/v1/org-members", tags=["iam.memberships.org"])


@org_router.get("", status_code=200)
async def list_org_memberships_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user_id: str | None = None,
    org_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_org(
            conn, ctx, limit=limit, offset=offset, user_id=user_id, org_id=org_id,
        )
    data = [OrgMembershipRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@org_router.post("", status_code=201)
async def create_org_membership_route(
    request: Request, body: OrgMembershipCreate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            m = await _service.assign_org(
                pool, conn, ctx,
                user_id=body.user_id, org_id=body.org_id,
            )
    return _response.success(OrgMembershipRead(**m).model_dump())


@org_router.delete("/{membership_id}", status_code=204)
async def delete_org_membership_route(
    request: Request, membership_id: str,
) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.revoke_org(pool, conn, ctx, membership_id=membership_id)
    return Response(status_code=204)


# ── Workspace membership router ──────────────────────────────────────

ws_router = APIRouter(prefix="/v1/workspace-members", tags=["iam.memberships.workspace"])


@ws_router.get("", status_code=200)
async def list_workspace_memberships_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    user_id: str | None = None,
    workspace_id: str | None = None,
    org_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_workspace(
            conn, ctx,
            limit=limit, offset=offset,
            user_id=user_id, workspace_id=workspace_id, org_id=org_id,
        )
    data = [WorkspaceMembershipRead(**row).model_dump() for row in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@ws_router.post("", status_code=201)
async def create_workspace_membership_route(
    request: Request, body: WorkspaceMembershipCreate,
) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            m = await _service.assign_workspace(
                pool, conn, ctx,
                user_id=body.user_id, workspace_id=body.workspace_id,
            )
    return _response.success(WorkspaceMembershipRead(**m).model_dump())


@ws_router.delete("/{membership_id}", status_code=204)
async def delete_workspace_membership_route(
    request: Request, membership_id: str,
) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.revoke_workspace(pool, conn, ctx, membership_id=membership_id)
    return Response(status_code=204)


# ── Combined sub-feature router ──────────────────────────────────────

router = APIRouter()
router.include_router(org_router)
router.include_router(ws_router)
