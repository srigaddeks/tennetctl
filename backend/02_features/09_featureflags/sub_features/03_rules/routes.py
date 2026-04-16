"""featureflags.rules — FastAPI routes."""
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
    "backend.02_features.09_featureflags.sub_features.03_rules.schemas"
)
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.03_rules.service"
)

RuleCreate = _schemas.RuleCreate
RuleUpdate = _schemas.RuleUpdate
RuleRead = _schemas.RuleRead

router = APIRouter(prefix="/v1/flag-rules", tags=["featureflags.rules"])


def _build_ctx(request: Request, pool: Any, *, audit_category: str) -> Any:
    return _catalog_ctx.NodeContext(
        user_id=request.headers.get("x-user-id"),
        session_id=request.headers.get("x-session-id"),
        org_id=request.headers.get("x-org-id"),
        workspace_id=request.headers.get("x-workspace-id"),
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        extras={"pool": pool},
    )


@router.get("", status_code=200)
async def list_rules_route(
    request: Request,
    limit: int = 100,
    offset: int = 0,
    flag_id: str | None = None,
    environment: str | None = None,
    is_active: bool | None = None,
) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        items, total = await _service.list_rules(
            conn, ctx, limit=limit, offset=offset,
            flag_id=flag_id, environment=environment, is_active=is_active,
        )
    data = [RuleRead(**r).model_dump() for r in items]
    return _response.paginated(data, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_rule_route(request: Request, body: RuleCreate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            rule = await _service.create_rule(
                pool, conn, ctx,
                flag_id=body.flag_id,
                environment=body.environment,
                priority=body.priority,
                conditions=body.conditions,
                value=body.value,
                rollout_percentage=body.rollout_percentage,
            )
    return _response.success(RuleRead(**rule).model_dump())


@router.get("/{rule_id}", status_code=200)
async def get_rule_route(request: Request, rule_id: str) -> dict:
    pool = request.app.state.pool
    ctx = _build_ctx(request, pool, audit_category="system")
    async with pool.acquire() as conn:
        r = await _service.get_rule(conn, ctx, rule_id=rule_id)
    if r is None:
        raise _errors.NotFoundError(f"Rule {rule_id!r} not found.")
    return _response.success(RuleRead(**r).model_dump())


@router.patch("/{rule_id}", status_code=200)
async def update_rule_route(request: Request, rule_id: str, body: RuleUpdate) -> dict:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            kw: dict[str, Any] = {}
            if body.priority is not None:
                kw["priority"] = body.priority
            if body.conditions is not None:
                kw["conditions"] = body.conditions
            if body.value is not None:
                kw["value"] = body.value
            if body.rollout_percentage is not None:
                kw["rollout_percentage"] = body.rollout_percentage
            if body.is_active is not None:
                kw["is_active"] = body.is_active
            r = await _service.update_rule(pool, conn, ctx, rule_id=rule_id, **kw)
    return _response.success(RuleRead(**r).model_dump())


@router.delete("/{rule_id}", status_code=204)
async def delete_rule_route(request: Request, rule_id: str) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.delete_rule(pool, conn, ctx, rule_id=rule_id)
    return Response(status_code=204)
