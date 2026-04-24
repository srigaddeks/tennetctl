"""Tags service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.50_tags.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_tags(conn: Any, *, tenant_id: str, limit: int = 200, offset: int = 0) -> list[dict]:
    return await _repo.list_tags(conn, tenant_id=tenant_id, limit=limit, offset=offset)


async def create_tag(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_tag(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.tags.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "tag"}},
    )
    return row


async def soft_delete_tag(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, tag_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_tag(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, tag_id=tag_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Tag {tag_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.tags.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": tag_id, "entity_kind": "tag"}},
    )


async def create_entity_tag(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_entity_tag(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.entity_tags.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "entity_tag"}},
    )
    return row


async def delete_entity_tag(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, entity_tag_id: str,
) -> None:
    deleted = await _repo.delete_entity_tag(conn, tenant_id=tenant_id, entity_tag_id=entity_tag_id)
    if not deleted:
        raise _errors.NotFoundError(f"Entity tag {entity_tag_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.entity_tags.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": entity_tag_id, "entity_kind": "entity_tag"}},
    )
