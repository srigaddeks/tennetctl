"""Service zones service — CRUD + active-kitchen validation + audit emit.

Cross-layer behavior (per spec 02_api_design/01_geography.md):
POST / PATCH (when changing kitchen_id) validates that the target kitchen is
status='active'. Decommissioned or paused kitchens reject new/assigned zones
with HTTP 409 (ConflictError mapped to status_code=409).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.17_service_zones.repository",
)
_errors = import_module("apps.somaerp.backend.01_core.errors")


def _conflict(message: str, code: str = "KITCHEN_NOT_ACTIVE") -> _errors.SomaerpError:
    return _errors.SomaerpError(message, code=code, status_code=409)


async def list_zones(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_zones(
        conn,
        tenant_id=tenant_id,
        kitchen_id=kitchen_id,
        status=status,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_zone(
    conn: Any, *, tenant_id: str, zone_id: str,
) -> dict:
    row = await _repo.get_zone(conn, tenant_id=tenant_id, zone_id=zone_id)
    if row is None:
        raise _errors.NotFoundError(f"Service zone {zone_id} not found.")
    return row


async def _require_active_kitchen(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> None:
    status = await _repo.get_kitchen_status(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    )
    if status is None:
        raise _errors.ValidationError(
            f"Kitchen {kitchen_id} not found for this tenant.",
            code="INVALID_KITCHEN",
        )
    if status != "active":
        raise _conflict(
            f"Kitchen {kitchen_id} is status='{status}' — "
            "only active kitchens accept service zones.",
        )


async def create_zone(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    await _require_active_kitchen(
        conn, tenant_id=tenant_id, kitchen_id=data["kitchen_id"],
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_zone(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.geography.service_zones.created",
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "geography.service_zone",
                "kitchen_id": str(data["kitchen_id"]),
            },
        },
    )
    return row


async def update_zone(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    zone_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_zone(
        conn, tenant_id=tenant_id, zone_id=zone_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Service zone {zone_id} not found.")

    # If the zone is being reassigned to a different kitchen, ensure the
    # new kitchen is active.
    new_kitchen = patch.get("kitchen_id")
    if new_kitchen and new_kitchen != existing["kitchen_id"]:
        await _require_active_kitchen(
            conn, tenant_id=tenant_id, kitchen_id=new_kitchen,
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_zone(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        zone_id=zone_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Service zone {zone_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.service_zones.updated",
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(zone_id),
                "entity_kind": "geography.service_zone",
                "kitchen_id": str(row.get("kitchen_id")),
                "changed_fields": sorted(
                    [k for k, v in patch.items() if v is not None],
                ),
            },
        },
    )
    return row


async def soft_delete_zone(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    zone_id: str,
) -> None:
    existing = await _repo.get_zone(
        conn, tenant_id=tenant_id, zone_id=zone_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Service zone {zone_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_zone(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        zone_id=zone_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Service zone {zone_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.service_zones.deleted",
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(zone_id),
                "entity_kind": "geography.service_zone",
                "kitchen_id": str(existing.get("kitchen_id")),
            },
        },
    )
