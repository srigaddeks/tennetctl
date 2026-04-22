"""HTTP routes for flows sub-feature."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from . import repository as repo
from . import service
from .schemas import FlowCreate, FlowUpdate

# Audit shim defined alongside service.py.
_audit = service._audit

router = APIRouter(prefix="/v1/flows", tags=["flows"])


def _scope(request: Request) -> tuple[str, str, str | None, str | None]:
    """Return (org_id, user_id, session_id, workspace_id) from request.state.

    Raises 401 if org_id or user_id aren't populated (no auth).
    """
    state = request.state
    org_id = getattr(state, "org_id", None)
    user_id = getattr(state, "user_id", None)
    if not org_id or not user_id:
        raise HTTPException(status_code=401, detail={"code": "UNAUTHORIZED"})
    return (
        org_id,
        user_id,
        getattr(state, "session_id", None),
        getattr(state, "workspace_id", None),
    )


@router.get("")
async def list_flows(
    request: Request,
    status: str | None = None,
    q: str | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """List flows in org."""
    org_id, _user, _sess, _ws = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        flows = await repo.list_flows(
            conn, org_id,
            status=status, q=q, workspace_id=workspace_id,
        )
    return {"ok": True, "data": [dict(f) for f in flows]}


@router.post("")
async def create_flow(request: Request, body: FlowCreate) -> dict[str, Any]:
    """Create a new flow."""
    org_id, user_id, session_id, workspace_id = _scope(request)
    if not workspace_id:
        raise HTTPException(status_code=400, detail={"code": "WORKSPACE_REQUIRED"})
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await service.create_flow(
            conn, org_id, workspace_id, body, user_id, session_id or "",
        )
    return {"ok": True, "data": result}


@router.get("/{id}")
async def get_flow(request: Request, id: str) -> dict[str, Any]:
    """Get a single flow."""
    _scope(request)  # auth check
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        flow = await repo.get_flow(conn, id)
    if not flow:
        raise HTTPException(status_code=404, detail="Flow not found")
    return {"ok": True, "data": {"flow": dict(flow)}}


@router.patch("/{id}")
async def update_flow(request: Request, id: str, body: FlowUpdate) -> dict[str, Any]:
    """Update a flow (rename, archive, publish)."""
    org_id, user_id, session_id, workspace_id = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await service.update_flow(
            conn, id, org_id, workspace_id or "",
            body, user_id, session_id or "",
        )
    if isinstance(result, dict) and result.get("ok") is False:
        raise HTTPException(status_code=422, detail=result)
    return {"ok": True, "data": result}


@router.delete("/{id}")
async def delete_flow(request: Request, id: str) -> dict[str, Any]:
    """Soft-delete a flow."""
    org_id, user_id, session_id, workspace_id = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        flow = await repo.get_flow(conn, id)
        if not flow:
            raise HTTPException(status_code=404, detail="Flow not found")
        await repo.soft_delete(conn, id, user_id)
        await _audit.emit_audit(
            conn,
            category="product",
            event_key="flows.deleted",
            user_id=user_id,
            session_id=session_id,
            org_id=org_id,
            workspace_id=workspace_id,
            target_id=id,
            metadata={"slug": flow.get("slug")},
        )
    return {"ok": True, "data": None}


@router.get("/{id}/versions/{version_id}")
async def get_version(request: Request, id: str, version_id: str) -> dict[str, Any]:
    """Get a flow version with full DAG."""
    _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        version = await repo.get_version(conn, version_id)
    if not version or version["flow_id"] != id:
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
    org_id, user_id, session_id, workspace_id = _scope(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        version = await repo.get_version(conn, version_id)
        if not version or version["flow_id"] != id:
            raise HTTPException(status_code=404, detail="Version not found")
        result = await service.replace_version_dag(
            conn, id, version_id,
            org_id, workspace_id or "",
            body.get("nodes", []), body.get("edges", []),
            user_id, session_id or "",
        )
    if isinstance(result, dict) and result.get("ok") is False:
        status_code = 409 if result.get("code") == "VERSION_FROZEN" else 422
        raise HTTPException(status_code=status_code, detail=result)
    return {"ok": True, "data": result}
