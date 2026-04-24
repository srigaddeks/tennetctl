"""Deals service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.35_deals.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_deals(
    conn: Any, *, tenant_id: str, status: str | None = None, stage_id: str | None = None,
    contact_id: str | None = None, organization_id: str | None = None,
    q: str | None = None, limit: int = 50, offset: int = 0,
) -> list[dict]:
    return await _repo.list_deals(
        conn, tenant_id=tenant_id, status=status, stage_id=stage_id,
        contact_id=contact_id, organization_id=organization_id,
        q=q, limit=limit, offset=offset,
    )


async def get_deal(conn: Any, *, tenant_id: str, deal_id: str) -> dict:
    row = await _repo.get_deal(conn, tenant_id=tenant_id, deal_id=deal_id)
    if row is None:
        raise _errors.NotFoundError(f"Deal {deal_id} not found.")
    return row


async def create_deal(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_deal(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.deals.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "deal"}},
    )
    return row


async def update_deal(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    deal_id: str, patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_deal(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, deal_id=deal_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Deal {deal_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.deals.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": deal_id, "entity_kind": "deal", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_deal(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, deal_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_deal(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, deal_id=deal_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Deal {deal_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.deals.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": deal_id, "entity_kind": "deal"}},
    )
