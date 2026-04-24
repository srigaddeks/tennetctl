"""Note routes — /v1/somacrm/notes."""

from __future__ import annotations

from importlib import import_module

from fastapi import APIRouter, Query, Request, Response

_service = import_module("apps.somacrm.backend.02_features.45_notes.service")
_schemas = import_module("apps.somacrm.backend.02_features.45_notes.schemas")
_response = import_module("apps.somacrm.backend.01_core.response")
_errors = import_module("apps.somacrm.backend.01_core.errors")

router = APIRouter(prefix="/v1/somacrm/notes", tags=["notes"])


def _require_workspace(request: Request) -> str:
    ws = getattr(request.state, "workspace_id", None)
    if not ws:
        raise _errors.AuthError("Authentication required (no workspace_id).")
    return ws


@router.get("")
async def list_notes(
    request: Request,
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        rows = await _service.list_notes(
            conn, tenant_id=workspace_id, entity_type=entity_type,
            entity_id=entity_id, limit=limit, offset=offset,
        )
    return _response.ok([_schemas.NoteOut(**r).model_dump(mode="json") for r in rows])


@router.post("", status_code=201)
async def create_note(request: Request, payload: _schemas.NoteCreate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.create_note(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            data=payload.model_dump(),
        )
    return _response.ok(_schemas.NoteOut(**row).model_dump(mode="json"))


@router.get("/{note_id}")
async def get_note(request: Request, note_id: str) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.get_note(conn, tenant_id=workspace_id, note_id=note_id)
    return _response.ok(_schemas.NoteOut(**row).model_dump(mode="json"))


@router.patch("/{note_id}")
async def patch_note(request: Request, note_id: str, payload: _schemas.NoteUpdate) -> dict:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        row = await _service.update_note(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            note_id=note_id,
            patch=payload.model_dump(exclude_unset=True),
        )
    return _response.ok(_schemas.NoteOut(**row).model_dump(mode="json"))


@router.delete("/{note_id}", status_code=204, response_class=Response)
async def delete_note(request: Request, note_id: str) -> Response:
    workspace_id = _require_workspace(request)
    async with request.app.state.pool.acquire() as conn:
        await _service.soft_delete_note(
            conn,
            tennetctl=request.app.state.tennetctl,
            tenant_id=workspace_id,
            actor_user_id=getattr(request.state, "user_id", None),
            org_id=getattr(request.state, "org_id", None),
            session_id=getattr(request.state, "session_id", None),
            note_id=note_id,
        )
    return Response(status_code=204)
