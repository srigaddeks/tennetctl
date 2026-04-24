"""Kitchens service — CRUD + status state machine + audit emission.

Status state machine (per spec 02_api_design/01_geography.md § Kitchens):
  active <-> paused
  * -> decommissioned (terminal; no reactivation)

Audit key routing:
  - status field changed  -> somaerp.geography.kitchens.status_changed
  - any other field(s)    -> somaerp.geography.kitchens.updated
  - status + other field  -> emit .status_changed (status is the dominant
    signal; other-field changes are covered by metadata.changed_fields)

TODO(56-10): DELETE on a kitchen with active fct_production_batches in the
last 30 days must return 422 DEPENDENCY_VIOLATION. That table does not
exist yet; the guard activates when it lands.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somaerp.backend.02_features.15_kitchens.repository")
_errors = import_module("apps.somaerp.backend.01_core.errors")


# Allowed status transitions. decommissioned is terminal.
_ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "active": {"active", "paused", "decommissioned"},
    "paused": {"active", "paused", "decommissioned"},
    "decommissioned": {"decommissioned"},
}


async def list_kitchens(
    conn: Any,
    *,
    tenant_id: str,
    location_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_kitchens(
        conn,
        tenant_id=tenant_id,
        location_id=location_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_kitchen(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> dict:
    row = await _repo.get_kitchen(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")
    return row


async def create_kitchen(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    # Cross-tenant FK check: the location must exist in this tenant.
    if not await _repo.get_location_exists(
        conn, tenant_id=tenant_id, location_id=data["location_id"],
    ):
        raise _errors.ValidationError(
            f"Location {data['location_id']} not found for this tenant.",
            code="INVALID_LOCATION",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_kitchen(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.geography.kitchens.created",
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
                "entity_kind": "geography.kitchen",
                "location_id": str(data["location_id"]),
                "kitchen_type": data.get("kitchen_type"),
                "status": row.get("status"),
            },
        },
    )
    return row


async def update_kitchen(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_kitchen(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")

    # If location_id is being changed, verify it exists for this tenant.
    if patch.get("location_id") and patch["location_id"] != existing["location_id"]:
        if not await _repo.get_location_exists(
            conn, tenant_id=tenant_id, location_id=patch["location_id"],
        ):
            raise _errors.ValidationError(
                f"Location {patch['location_id']} not found for this tenant.",
                code="INVALID_LOCATION",
            )

    # Status state machine gate.
    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]
    if new_status is not None:
        allowed = _ALLOWED_TRANSITIONS.get(existing["status"], set())
        if new_status not in allowed:
            raise _errors.ValidationError(
                f"Illegal status transition: {existing['status']} -> {new_status}.",
                code="ILLEGAL_STATUS_TRANSITION",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_kitchen(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        kitchen_id=kitchen_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    event_key = (
        "somaerp.geography.kitchens.status_changed"
        if status_changed
        else "somaerp.geography.kitchens.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(kitchen_id),
        "entity_kind": "geography.kitchen",
        "location_id": str(row.get("location_id")),
        "changed_fields": changed_fields,
    }
    if status_changed:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = new_status

    await tennetctl.audit_emit(
        event_key=event_key,
        scope={
            "user_id": actor_user_id,
            "session_id": session_id,
            "org_id": org_id,
            "workspace_id": tenant_id,
        },
        payload={"outcome": "success", "metadata": metadata},
    )
    return row


async def soft_delete_kitchen(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
) -> None:
    existing = await _repo.get_kitchen(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")

    # TODO(56-10): guard against active fct_production_batches in the last
    # 30 days. That table does not exist yet; when it lands, check here and
    # raise ValidationError(code="DEPENDENCY_VIOLATION", status_code=422).

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_kitchen(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        kitchen_id=kitchen_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.kitchens.deleted",
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
                "entity_id": str(kitchen_id),
                "entity_kind": "geography.kitchen",
                "location_id": str(existing.get("location_id")),
            },
        },
    )
