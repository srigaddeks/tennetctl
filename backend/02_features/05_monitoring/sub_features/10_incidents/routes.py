"""Routes for incidents sub-feature."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends
from importlib import import_module

from . import service, schemas

_resp = import_module("backend.01_core.response")
_middleware = import_module("backend.01_core.middleware")

router = APIRouter(prefix="/v1/monitoring", tags=["monitoring.incidents"])


@router.get("/incidents", status_code=200)
async def list_incidents_route(
    state: int | None = None,
    severity: int | None = None,
    rule_id: str | None = None,
    label_search: str | None = None,
    opened_after: str | None = None,
    limit: int = 50,
    offset: int = 0,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """List incidents with optional filters."""
    async with pool.acquire() as conn:
        rows, total = await service.list_incidents(
            conn,
            org_id=ctx.org_id,
            state_id=state,
            severity_id=severity,
            rule_id=rule_id,
            label_search=label_search,
            opened_after=opened_after,
            limit=limit,
            offset=offset,
        )
    return _resp.success_list_response(rows, total=total, limit=limit, offset=offset)


@router.get("/incidents/{id}", status_code=200)
async def get_incident_route(
    id: str,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """Get incident detail with linked alerts and timeline."""
    async with pool.acquire() as conn:
        incident = await service.get_incident_detail(conn, org_id=ctx.org_id, incident_id=id)
    return _resp.success_response(incident)


@router.patch("/incidents/{id}", status_code=200)
async def update_incident_route(
    id: str,
    req: schemas.IncidentStateTransition,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """Update incident state (acknowledged, resolved, closed)."""
    async with pool.acquire() as conn:
        incident = await service.update_incident_state(
            conn,
            org_id=ctx.org_id,
            incident_id=id,
            user_id=ctx.user_id,
            req=req,
        )
    return _resp.success_response(incident)


@router.post("/incidents/{id}/comments", status_code=201)
async def add_incident_comment_route(
    id: str,
    req: schemas.IncidentCommentCreate,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """Add comment to incident timeline."""
    async with pool.acquire() as conn:
        event = await service.add_incident_comment(
            conn,
            org_id=ctx.org_id,
            incident_id=id,
            user_id=ctx.user_id,
            req=req,
        )
    return _resp.success_response(event)


@router.get("/incidents/{id}/timeline", status_code=200)
async def get_incident_timeline_route(
    id: str,
    limit: int = 100,
    offset: int = 0,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """Get incident timeline events."""
    async with pool.acquire() as conn:
        # Verify incident exists in this org
        incident = await service.get_incident_detail(conn, org_id=ctx.org_id, incident_id=id)
        # Get timeline
        from . import repository
        events = await repository.get_incident_timeline(conn, id, limit=limit, offset=offset)
    return _resp.success_list_response(events, total=len(events), limit=limit, offset=offset)


@router.post("/alert-rules/{id}/grouping", status_code=200)
async def create_grouping_rule_route(
    id: str,
    req: schemas.GroupingRuleCreate,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """Create or update grouping rule for alert rule."""
    async with pool.acquire() as conn:
        rule = await service.create_or_update_grouping_rule(
            conn,
            org_id=ctx.org_id,
            user_id=ctx.user_id,
            rule_id=id,
            req=req,
        )
    return _resp.success_response(rule)


@router.get("/alert-rules/{id}/grouping", status_code=200)
async def get_grouping_rule_route(
    id: str,
    pool: Any = Depends(_middleware.get_pool),
    ctx: Any = Depends(_middleware.get_node_context),
) -> dict[str, Any]:
    """Get grouping rule for alert rule."""
    async with pool.acquire() as conn:
        # Verify rule exists in this org
        rule = await conn.fetchrow(
            'SELECT * FROM "05_monitoring".v_monitoring_alert_rules WHERE id = $1',
            id,
        )
        if not rule:
            from importlib import import_module
            _errors = import_module("backend.01_core.errors")
            raise _errors.AppError("NOT_FOUND", f"Alert rule '{id}' not found.", 404)
        if rule["org_id"] != ctx.org_id:
            from importlib import import_module
            _errors = import_module("backend.01_core.errors")
            raise _errors.AppError("FORBIDDEN", "Cannot access rule from another org.", 403)

        grouping = await service.get_grouping_rule(conn, id)
    return _resp.success_response(grouping or {})
