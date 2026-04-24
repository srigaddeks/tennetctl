"""Pipeline stages service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.30_pipeline_stages.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_pipeline_stages(
    conn: Any, *, tenant_id: str, limit: int = 200, offset: int = 0,
) -> list[dict]:
    return await _repo.list_pipeline_stages(conn, tenant_id=tenant_id, limit=limit, offset=offset)


async def get_pipeline_stage(conn: Any, *, tenant_id: str, stage_id: str) -> dict:
    row = await _repo.get_pipeline_stage(conn, tenant_id=tenant_id, stage_id=stage_id)
    if row is None:
        raise _errors.NotFoundError(f"Pipeline stage {stage_id} not found.")
    return row


async def create_pipeline_stage(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_pipeline_stage(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.pipeline_stages.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "pipeline_stage"}},
    )
    return row


async def update_pipeline_stage(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    stage_id: str, patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_pipeline_stage(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, stage_id=stage_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Pipeline stage {stage_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.pipeline_stages.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": stage_id, "entity_kind": "pipeline_stage", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_pipeline_stage(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, stage_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_pipeline_stage(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, stage_id=stage_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Pipeline stage {stage_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.pipeline_stages.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": stage_id, "entity_kind": "pipeline_stage"}},
    )
