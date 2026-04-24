"""Notes service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.45_notes.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_notes(
    conn: Any, *, tenant_id: str, entity_type: str | None = None,
    entity_id: str | None = None, limit: int = 50, offset: int = 0,
) -> list[dict]:
    return await _repo.list_notes(
        conn, tenant_id=tenant_id, entity_type=entity_type,
        entity_id=entity_id, limit=limit, offset=offset,
    )


async def get_note(conn: Any, *, tenant_id: str, note_id: str) -> dict:
    row = await _repo.get_note(conn, tenant_id=tenant_id, note_id=note_id)
    if row is None:
        raise _errors.NotFoundError(f"Note {note_id} not found.")
    return row


async def create_note(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_note(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.notes.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "note"}},
    )
    return row


async def update_note(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    note_id: str, patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_note(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, note_id=note_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Note {note_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.notes.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": note_id, "entity_kind": "note", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_note(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, note_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_note(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, note_id=note_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Note {note_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.notes.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": note_id, "entity_kind": "note"}},
    )
