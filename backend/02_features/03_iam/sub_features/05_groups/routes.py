"""iam.groups — FastAPI routes."""

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
    "backend.02_features.03_iam.sub_features.05_groups.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.service"
)

GroupCreate = _schemas.GroupCreate
GroupUpdate = _schemas.GroupUpdate
GroupRead = _schemas.GroupRead

router = APIRouter(prefix="/v1/groups", tags=["iam.groups"])


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


@router.get("", status_code=200)
async def list_groups_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    org_id: str | None = None,
    is_active: bool | None = None,
    application_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_groups(
            conn, ctx, limit=limit, offset=offset,
            org_id=org_id, is_active=is_active, application_id=application_id,
        )
    data = [GroupRead(**r).model_dump() for r in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_group_route(request: Request, body: GroupCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            g = await _service.create_group(
                pool, conn, ctx,
                org_id=body.org_id,
                application_id=body.application_id,
                code=body.code,
                label=body.label,
                description=body.description,
            )
    return _response.success(GroupRead(**g).model_dump())


@router.get("/{group_id}", status_code=200)
async def get_group_route(request: Request, group_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        g = await _service.get_group(conn, ctx, group_id=group_id)
    if g is None:
        raise _errors.NotFoundError(f"Group {group_id!r} not found.")
    return _response.success(GroupRead(**g).model_dump())


@router.patch("/{group_id}", status_code=200)
async def update_group_route(request: Request, group_id: str, body: GroupUpdate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            g = await _service.update_group(
                pool, conn, ctx,
                group_id=group_id,
                label=body.label,
                description=body.description,
                is_active=body.is_active,
            )
    return _response.success(GroupRead(**g).model_dump())


@router.delete("/{group_id}", status_code=204)
async def delete_group_route(request: Request, group_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_group(pool, conn, ctx, group_id=group_id)
    return Response(status_code=204)


# ── Membership routes ────────────────────────────────────────────────────


from pydantic import BaseModel as _BaseModel, ConfigDict as _ConfigDict  # noqa: E402

_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.05_groups.repository"
)


class _AddMember(_BaseModel):
    model_config = _ConfigDict(extra="forbid")
    user_id: str


@router.get("/{group_id}/members", status_code=200)
async def list_group_members_route(request: Request, group_id: str) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _repo.list_members(conn, group_id=group_id)
    items = [
        {
            "membership_id": r["membership_id"],
            "user_id": r["user_id"],
            "group_id": r["group_id"],
            "org_id": r["org_id"],
            "user_email": r["user_email"] or None,
            "user_display_name": r["user_display_name"] or None,
            "account_type_code": r["account_type_code"],
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
    return _response.success(items)


@router.post("/{group_id}/members", status_code=201)
async def add_group_member_route(
    request: Request, group_id: str, body: _AddMember,
) -> dict:
    pool = request.app.state.pool
    actor_id = getattr(request.state, "user_id", None) or body.user_id
    state_org = getattr(request.state, "org_id", None)
    async with pool.acquire() as conn:
        async with conn.transaction():
            grp = await _repo.get_by_id(conn, group_id)
            if grp is None:
                raise _errors.AppError(
                    "NOT_FOUND", f"Group {group_id!r} not found.", 404,
                )
            org_id = grp["org_id"] or state_org
            if not org_id:
                raise _errors.AppError(
                    "BAD_REQUEST", "Group has no org and session has none either.", 400,
                )
            row = await _repo.add_member(
                conn,
                id=_core_id.uuid7(),
                user_id=body.user_id,
                group_id=group_id,
                org_id=org_id,
                created_by=actor_id,
            )
    return _response.success(
        {
            "membership_id": row["id"],
            "user_id": row["user_id"],
            "group_id": row["group_id"],
            "org_id": row["org_id"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
    )


@router.delete("/{group_id}/members/{user_id}", status_code=204)
async def remove_group_member_route(
    request: Request, group_id: str, user_id: str,
) -> Response:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        grp = await _repo.get_by_id(conn, group_id)
        if grp is None:
            raise _errors.AppError(
                "NOT_FOUND", f"Group {group_id!r} not found.", 404,
            )
        ok = await _repo.remove_member(
            conn, user_id=user_id, group_id=group_id, org_id=grp["org_id"],
        )
    if not ok:
        raise _errors.AppError(
            "NOT_FOUND", "Membership not found.", 404,
        )
    return Response(status_code=204)
