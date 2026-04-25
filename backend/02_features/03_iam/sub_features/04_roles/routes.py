"""iam.roles — FastAPI routes (5-endpoint shape + role assignment)."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel, ConfigDict

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.repository"
)

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.04_roles.service"
)

RoleCreate = _schemas.RoleCreate
RoleUpdate = _schemas.RoleUpdate
RoleRead = _schemas.RoleRead

router = APIRouter(prefix="/v1/roles", tags=["iam.roles"])


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
async def list_roles_route(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    org_id: str | None = None,
    role_type: str | None = None,
    is_active: bool | None = None,
    application_id: str | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_roles(
            conn, ctx,
            limit=limit, offset=offset,
            org_id=org_id, role_type=role_type, is_active=is_active,
            application_id=application_id,
        )
    data = [RoleRead(**r).model_dump() for r in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_role_route(request: Request, body: RoleCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            role = await _service.create_role(
                pool, conn, ctx,
                org_id=body.org_id,
                application_id=body.application_id,
                role_type=body.role_type,
                code=body.code,
                label=body.label,
                description=body.description,
            )
    return _response.success(RoleRead(**role).model_dump())


@router.get("/{role_id}", status_code=200)
async def get_role_route(request: Request, role_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        role = await _service.get_role(conn, ctx, role_id=role_id)
    if role is None:
        raise _errors.NotFoundError(f"Role {role_id!r} not found.")
    return _response.success(RoleRead(**role).model_dump())


@router.patch("/{role_id}", status_code=200)
async def update_role_route(request: Request, role_id: str, body: RoleUpdate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            role = await _service.update_role(
                pool, conn, ctx,
                role_id=role_id,
                label=body.label,
                description=body.description,
                is_active=body.is_active,
            )
    return _response.success(RoleRead(**role).model_dump())


@router.delete("/{role_id}", status_code=204)
async def delete_role_route(request: Request, role_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_role(pool, conn, ctx, role_id=role_id)
    return Response(status_code=204)


# ── User-role assignment ──────────────────────────────────────────────────


class _AssignBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role_id: str
    org_id: str | None = None
    expires_at: datetime | None = None


user_role_router = APIRouter(prefix="/v1/users", tags=["iam.user_roles"])


@user_role_router.get("/{user_id}/roles", status_code=200)
async def list_user_roles_route(request: Request, user_id: str) -> dict:
    """List active role assignments for a user."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        rows = await _repo.list_roles_for_user(conn, user_id=user_id)
    items = [
        {
            "assignment_id": r["assignment_id"],
            "user_id": r["user_id"],
            "role_id": r["role_id"],
            "role_code": r["role_code"] or None,
            "role_label": r["role_label"] or None,
            "role_description": r["role_description"] or None,
            "org_id": r["org_id"],
            "application_id": r["application_id"],
            "expires_at": r["expires_at"].isoformat() if r["expires_at"] else None,
            "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        }
        for r in rows
    ]
    return _response.success(items)


@user_role_router.post("/{user_id}/roles", status_code=201)
async def grant_user_role_route(
    request: Request, user_id: str, body: _AssignBody,
) -> dict:
    """Grant a role to a user. Idempotent: re-granting a revoked assignment
    re-activates it (revoked_at = NULL)."""
    pool = request.app.state.pool
    actor_id = getattr(request.state, "user_id", None) or user_id
    state_org = getattr(request.state, "org_id", None)
    org_id = body.org_id or state_org
    if not org_id:
        raise _errors.AppError("BAD_REQUEST", "org_id is required (no session org bound).", 400)
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await _repo.assign_role(
                conn,
                id=_core_id.uuid7(),
                user_id=user_id,
                role_id=body.role_id,
                org_id=org_id,
                created_by=actor_id,
                expires_at=body.expires_at,
            )
    return _response.success(
        {
            "assignment_id": row["id"],
            "user_id": row["user_id"],
            "role_id": row["role_id"],
            "org_id": row["org_id"],
            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
            "revoked_at": row["revoked_at"].isoformat() if row["revoked_at"] else None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        }
    )


@user_role_router.delete("/{user_id}/roles/{role_id}", status_code=204)
async def revoke_user_role_route(
    request: Request, user_id: str, role_id: str,
) -> Response:
    pool = request.app.state.pool
    state_org = getattr(request.state, "org_id", None)
    org_id = request.query_params.get("org_id") or state_org
    if not org_id:
        raise _errors.AppError("BAD_REQUEST", "org_id is required.", 400)
    async with pool.acquire() as conn:
        ok = await _repo.revoke_role(
            conn, user_id=user_id, role_id=role_id, org_id=org_id,
        )
    if not ok:
        raise _errors.AppError("NOT_FOUND", "Role assignment not found or already revoked.", 404)
    return Response(status_code=204)
