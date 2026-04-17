"""
audit.saved_views — FastAPI routes.

CRUD for persisted audit-explorer filter presets, scoped to the
caller's org_id (injected from session middleware).

  GET    /v1/audit-saved-views          list views for org
  POST   /v1/audit-saved-views          create a saved view
  DELETE /v1/audit-saved-views/{id}     delete (204)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

_errors: Any  = import_module("backend.01_core.errors")
_resp: Any    = import_module("backend.01_core.response")
_schemas: Any = import_module(
    "backend.02_features.04_audit.sub_features.02_saved_views.schemas"
)
_service: Any = import_module(
    "backend.02_features.04_audit.sub_features.02_saved_views.service"
)

AuditSavedViewCreate = _schemas.AuditSavedViewCreate
AuditSavedViewRow    = _schemas.AuditSavedViewRow

router = APIRouter(tags=["audit.saved_views"])


def _session_scope(request: Request) -> dict:
    state = request.state
    return {
        "user_id":      getattr(state, "user_id", None)      or request.headers.get("x-user-id"),
        "session_id":   getattr(state, "session_id", None)   or request.headers.get("x-session-id"),
        "org_id":       getattr(state, "org_id", None)       or request.headers.get("x-org-id"),
        "workspace_id": getattr(state, "workspace_id", None) or request.headers.get("x-workspace-id"),
    }


def _require_org(request: Request) -> str:
    org_id = _session_scope(request)["org_id"]
    if not org_id:
        raise HTTPException(
            status_code=401,
            detail={"ok": False, "error": {"code": "UNAUTHENTICATED", "message": "session required"}},
        )
    return org_id


@router.get("/v1/audit-saved-views", status_code=200)
async def list_saved_views_route(request: Request) -> dict:
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_views(conn, org_id=org_id)
    rows = [AuditSavedViewRow(**r).model_dump() for r in items]
    return _resp.success({"items": rows, "total": len(rows)})


@router.post("/v1/audit-saved-views", status_code=201)
async def create_saved_view_route(request: Request, body: AuditSavedViewCreate) -> dict:
    org_id = _require_org(request)
    user_id = _session_scope(request)["user_id"]
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.create_view(
            conn,
            org_id=org_id,
            user_id=user_id,
            name=body.name,
            filter_json=body.filter_json,
            bucket=body.bucket,
        )
    return _resp.success(AuditSavedViewRow(**row).model_dump())


@router.delete("/v1/audit-saved-views/{view_id}", status_code=204)
async def delete_saved_view_route(request: Request, view_id: str) -> Response:
    org_id = _require_org(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        deleted = await _service.delete_view(conn, view_id=view_id, org_id=org_id)
    if not deleted:
        raise _errors.NotFoundError(f"saved view {view_id!r} not found.")
    return Response(status_code=204)
