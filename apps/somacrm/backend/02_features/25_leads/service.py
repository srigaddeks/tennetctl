"""Leads service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.25_leads.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_leads(
    conn: Any, *, tenant_id: str, status: str | None = None,
    q: str | None = None, limit: int = 50, offset: int = 0,
) -> list[dict]:
    return await _repo.list_leads(conn, tenant_id=tenant_id, status=status, q=q, limit=limit, offset=offset)


async def get_lead(conn: Any, *, tenant_id: str, lead_id: str) -> dict:
    row = await _repo.get_lead(conn, tenant_id=tenant_id, lead_id=lead_id)
    if row is None:
        raise _errors.NotFoundError(f"Lead {lead_id} not found.")
    return row


async def create_lead(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_lead(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.leads.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "lead"}},
    )
    return row


async def update_lead(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    lead_id: str, patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_lead(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, lead_id=lead_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Lead {lead_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.leads.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": lead_id, "entity_kind": "lead", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_lead(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, lead_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_lead(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, lead_id=lead_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Lead {lead_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.leads.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": lead_id, "entity_kind": "lead"}},
    )
