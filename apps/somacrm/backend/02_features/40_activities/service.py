"""Activities service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.40_activities.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_activities(
    conn: Any, *, tenant_id: str, activity_type_id: int | None = None,
    status_id: int | None = None, entity_type: str | None = None,
    entity_id: str | None = None, due_from: str | None = None,
    due_to: str | None = None, limit: int = 50, offset: int = 0,
) -> list[dict]:
    return await _repo.list_activities(
        conn, tenant_id=tenant_id, activity_type_id=activity_type_id,
        status_id=status_id, entity_type=entity_type, entity_id=entity_id,
        due_from=due_from, due_to=due_to, limit=limit, offset=offset,
    )


async def get_activity(conn: Any, *, tenant_id: str, activity_id: str) -> dict:
    row = await _repo.get_activity(conn, tenant_id=tenant_id, activity_id=activity_id)
    if row is None:
        raise _errors.NotFoundError(f"Activity {activity_id} not found.")
    return row


async def create_activity(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_activity(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.activities.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "activity"}},
    )
    return row


async def update_activity(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    activity_id: str, patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_activity(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, activity_id=activity_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Activity {activity_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.activities.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": activity_id, "entity_kind": "activity", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_activity(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, activity_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_activity(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, activity_id=activity_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Activity {activity_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.activities.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": activity_id, "entity_kind": "activity"}},
    )
