"""Contacts service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.10_contacts.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_contacts(
    conn: Any,
    *,
    tenant_id: str,
    q: str | None = None,
    status: str | None = None,
    organization_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    return await _repo.list_contacts(
        conn,
        tenant_id=tenant_id,
        q=q,
        status=status,
        organization_id=organization_id,
        limit=limit,
        offset=offset,
    )


async def get_contact(conn: Any, *, tenant_id: str, contact_id: str) -> dict:
    row = await _repo.get_contact(conn, tenant_id=tenant_id, contact_id=contact_id)
    if row is None:
        raise _errors.NotFoundError(f"Contact {contact_id} not found.")
    return row


async def create_contact(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_contact(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data,
    )
    await tennetctl.audit_emit(
        event_key="somacrm.contacts.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "contact"}},
    )
    return row


async def update_contact(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    contact_id: str,
    patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_contact(
        conn, tenant_id=tenant_id, actor_user_id=effective_user,
        contact_id=contact_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Contact {contact_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.contacts.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": contact_id, "entity_kind": "contact", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_contact(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    contact_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_contact(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, contact_id=contact_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Contact {contact_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.contacts.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": contact_id, "entity_kind": "contact"}},
    )


async def get_contact_timeline(
    conn: Any,
    *,
    tenant_id: str,
    contact_id: str,
    limit: int = 200,
) -> list[dict]:
    contact = await _repo.get_contact(conn, tenant_id=tenant_id, contact_id=contact_id)
    if not contact:
        raise _errors.NotFoundError(f"Contact {contact_id} not found.")
    rows = await _repo.get_contact_timeline(
        conn, tenant_id=tenant_id, contact_id=contact_id, limit=limit,
    )
    return rows
