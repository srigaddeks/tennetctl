"""Equipment + kitchen-equipment service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.equipment.created / .updated / .status_changed / .deleted
  - somaerp.kitchen_equipment.attached / .detached
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.45_equipment.repository",
)
_errors = import_module("apps.somaerp.backend.01_core.errors")


def _scope(
    *, actor_user_id: str | None, session_id: str | None,
    org_id: str | None, tenant_id: str,
) -> dict:
    return {
        "user_id": actor_user_id,
        "session_id": session_id,
        "org_id": org_id,
        "workspace_id": tenant_id,
    }


# ── Categories ──────────────────────────────────────────────────────────


async def list_categories(conn: Any) -> list[dict]:
    return await _repo.list_categories(conn)


# ── Equipment ───────────────────────────────────────────────────────────


async def list_equipment(
    conn: Any,
    *,
    tenant_id: str,
    category_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_equipment(
        conn,
        tenant_id=tenant_id,
        category_id=category_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_equipment(
    conn: Any, *, tenant_id: str, equipment_id: str,
) -> dict:
    row = await _repo.get_equipment(
        conn, tenant_id=tenant_id, equipment_id=equipment_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Equipment {equipment_id} not found.")
    return row


async def create_equipment(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.category_exists(
        conn, category_id=int(data["category_id"]),
    ):
        raise _errors.ValidationError(
            f"Unknown category_id={data['category_id']}.",
            code="INVALID_CATEGORY",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_equipment(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.equipment.created",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "equipment.equipment",
                "category_code": row.get("category_code"),
                "slug": data["slug"],
            },
        },
    )
    return row


async def update_equipment(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    equipment_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_equipment(
        conn, tenant_id=tenant_id, equipment_id=equipment_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Equipment {equipment_id} not found.")

    if patch.get("category_id") is not None:
        if not await _repo.category_exists(
            conn, category_id=int(patch["category_id"]),
        ):
            raise _errors.ValidationError(
                f"Unknown category_id={patch['category_id']}.",
                code="INVALID_CATEGORY",
            )

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_equipment(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        equipment_id=equipment_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Equipment {equipment_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    event_key = (
        "somaerp.equipment.status_changed"
        if status_changed
        else "somaerp.equipment.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(equipment_id),
        "entity_kind": "equipment.equipment",
        "changed_fields": changed_fields,
    }
    if status_changed:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = new_status

    if changed_fields:
        await tennetctl.audit_emit(
            event_key=event_key,
            scope=_scope(
                actor_user_id=actor_user_id,
                session_id=session_id,
                org_id=org_id,
                tenant_id=tenant_id,
            ),
            payload={"outcome": "success", "metadata": metadata},
        )
    return row


async def soft_delete_equipment(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    equipment_id: str,
) -> None:
    existing = await _repo.get_equipment(
        conn, tenant_id=tenant_id, equipment_id=equipment_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Equipment {equipment_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_equipment(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        equipment_id=equipment_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Equipment {equipment_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.equipment.deleted",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(equipment_id),
                "entity_kind": "equipment.equipment",
            },
        },
    )


# ── Kitchen <-> Equipment link ──────────────────────────────────────────


async def list_kitchen_equipment(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> list[dict]:
    if not await _repo.kitchen_exists_for_tenant(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    ):
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")
    return await _repo.list_kitchen_equipment(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    )


async def attach_equipment_to_kitchen(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
    data: dict,
) -> dict:
    if not await _repo.kitchen_exists_for_tenant(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    ):
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")

    eq = await _repo.get_equipment(
        conn, tenant_id=tenant_id, equipment_id=data["equipment_id"],
    )
    if eq is None:
        raise _errors.ValidationError(
            f"Equipment {data['equipment_id']} not found for this tenant.",
            code="INVALID_EQUIPMENT",
        )

    existing = await _repo.get_kitchen_equipment_link(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
        equipment_id=data["equipment_id"],
    )
    if existing is not None:
        raise _errors.ValidationError(
            "Link already exists for this (kitchen, equipment).",
            code="DUPLICATE_LINK",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.attach_equipment_to_kitchen(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        kitchen_id=kitchen_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.kitchen_equipment.attached",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_id": str(row.get("id")),
                "entity_kind": "equipment.kitchen_equipment",
                "kitchen_id": str(kitchen_id),
                "equipment_id": str(data["equipment_id"]),
                "quantity": int(data.get("quantity") or 1),
            },
        },
    )
    return row


async def detach_equipment_from_kitchen(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
    equipment_id: str,
) -> None:
    if not await _repo.kitchen_exists_for_tenant(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    ):
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")

    is_setup = actor_user_id is None

    ok = await _repo.detach_equipment_from_kitchen(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
        equipment_id=equipment_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Link (kitchen={kitchen_id}, equipment={equipment_id}) not found.",
        )

    await tennetctl.audit_emit(
        event_key="somaerp.kitchen_equipment.detached",
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={
            "outcome": "success",
            "metadata": {
                "category": "setup" if is_setup else "operational",
                "entity_kind": "equipment.kitchen_equipment",
                "kitchen_id": str(kitchen_id),
                "equipment_id": str(equipment_id),
            },
        },
    )
