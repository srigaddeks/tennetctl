"""HTTP routes for flows sub-feature."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from . import repository as repo
from . import service
from .schemas import FlowCreate, FlowUpdate

router = APIRouter(prefix="/v1/flows", tags=["flows"])


@router.get("")
async def list_flows(
    request: Request,
    status: str | None = None,
    q: str | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """List flows in org."""
    ctx = request.state.ctx
    org_id = ctx.org_id

    flows = await repo.list_flows(
        ctx.conn,
        org_id,
        status=status,
        q=q,
        workspace_id=workspace_id,
    )

    return {"ok": True, "data": flows}


@router.post("")
async def create_flow(request: Request, body: FlowCreate) -> dict[str, Any]:
    """Create a new flow."""
    ctx = request.state.ctx

    result = await service.create_flow(
        ctx.conn,
        ctx.org_id,
        ctx.workspace_id,
        body,
        ctx.user_id,
        ctx.session_id,
    )

    return {"ok": True, "data": result}


@router.get("/{id}")
async def get_flow(request: Request, id: str) -> dict[str, Any]:
    """Get a single flow."""
    ctx = request.state.ctx

    flow = await repo.get_flow(ctx.conn, id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    return {"ok": True, "data": {"flow": flow}}


@router.patch("/{id}")
async def update_flow(request: Request, id: str, body: FlowUpdate) -> dict[str, Any]:
    """Update a flow (rename, archive, publish)."""
    ctx = request.state.ctx

    result = await service.update_flow(
        ctx.conn,
        id,
        ctx.org_id,
        ctx.workspace_id,
        body,
        ctx.user_id,
        ctx.session_id,
    )

    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result)

    return {"ok": True, "data": result}


@router.delete("/{id}")
async def delete_flow(request: Request, id: str) -> dict[str, Any]:
    """Soft-delete a flow."""
    ctx = request.state.ctx

    flow = await repo.get_flow(ctx.conn, id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")

    await repo.soft_delete(ctx.conn, id, ctx.user_id)

    # Emit audit
    _audit = __import__("importlib").import_module(
        "backend.02_features.04_audit.sub_features.01_events.service"
    )
    await _audit.emit_audit(
        ctx.conn,
        category="product",
        event_key="flows.deleted",
        user_id=ctx.user_id,
        session_id=ctx.session_id,
        org_id=ctx.org_id,
        workspace_id=ctx.workspace_id,
        target_id=id,
        metadata={"slug": flow["slug"]},
    )

    return {"ok": True, "data": None}


@router.get("/{id}/versions/{version_id}")
async def get_version(request: Request, id: str, version_id: str) -> dict[str, Any]:
    """Get a flow version with full DAG."""
    ctx = request.state.ctx

    version = await repo.get_version(ctx.conn, version_id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")

    # Verify version belongs to flow
    if version["flow_id"] != id:
        raise HTTPException(status_code=404, detail="Version not found")

    return {"ok": True, "data": {"version": version}}


@router.patch("/{id}/versions/{version_id}")
async def update_version_dag(
    request: Request,
    id: str,
    version_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Update a draft version DAG."""
    ctx = request.state.ctx

    # Verify version belongs to flow
    version = await repo.get_version(ctx.conn, version_id)
    if not version or version["flow_id"] != id:
        raise HTTPException(status_code=404, detail="Version not found")

    result = await service.replace_version_dag(
        ctx.conn,
        id,
        version_id,
        ctx.org_id,
        ctx.workspace_id,
        body.get("nodes", []),
        body.get("edges", []),
        ctx.user_id,
        ctx.session_id,
    )

    if not result.get("ok"):
        # Return error response
        status_code = 409 if result.get("code") == "VERSION_FROZEN" else 422
        raise HTTPException(status_code=status_code, detail=result)

    return {"ok": True, "data": result}
