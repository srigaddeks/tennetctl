"""Organizations service — orchestrates repo writes + audit emission."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somacrm.backend.02_features.15_organizations.repository")
_errors = import_module("apps.somacrm.backend.01_core.errors")


async def list_organizations(
    conn: Any, *, tenant_id: str, q: str | None = None, limit: int = 50, offset: int = 0,
) -> list[dict]:
    return await _repo.list_organizations(conn, tenant_id=tenant_id, q=q, limit=limit, offset=offset)


async def get_organization(conn: Any, *, tenant_id: str, org_id: str) -> dict:
    row = await _repo.get_organization(conn, tenant_id=tenant_id, org_id=org_id)
    if row is None:
        raise _errors.NotFoundError(f"Organization {org_id} not found.")
    return row


async def create_organization(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None, data: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.create_organization(conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data)
    await tennetctl.audit_emit(
        event_key="somacrm.organizations.created",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": str(row.get("id")), "entity_kind": "organization"}},
    )
    return row


async def update_organization(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    organization_id: str, patch: dict,
) -> dict:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    row = await _repo.update_organization(
        conn, tenant_id=tenant_id, actor_user_id=effective_user,
        org_id=organization_id, patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Organization {organization_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.organizations.updated",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": organization_id, "entity_kind": "organization", "changed_fields": sorted(patch.keys())}},
    )
    return row


async def soft_delete_organization(
    conn: Any, *, tennetctl: Any, tenant_id: str,
    actor_user_id: str | None, org_id: str | None, session_id: str | None,
    organization_id: str,
) -> None:
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"
    deleted = await _repo.soft_delete_organization(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, org_id=organization_id,
    )
    if not deleted:
        raise _errors.NotFoundError(f"Organization {organization_id} not found.")
    await tennetctl.audit_emit(
        event_key="somacrm.organizations.deleted",
        scope={"user_id": actor_user_id, "session_id": session_id, "org_id": org_id, "workspace_id": tenant_id},
        payload={"outcome": "success", "metadata": {"entity_id": organization_id, "entity_kind": "organization"}},
    )
