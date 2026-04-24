"""Suppliers + material<->supplier link — service orchestration.

Audit keys:
  - somaerp.raw_materials.suppliers.created / .updated / .status_changed / .deleted
  - somaerp.raw_materials.material_supplier.linked / .unlinked / .primary_changed
    (NOTE: .primary_changed fires when is_primary toggles on update; .updated
    fires for cost/notes/currency changes that do not toggle primary.)

Cross-layer validation:
  - location_id on supplier must exist in fct_locations (same tenant) or be null.
  - Link create/update requires both raw_material_id + supplier_id to exist
    for the tenant.

NOTE: spec deviation per 05_raw_materials.md — lnk_raw_material_suppliers
is mutable (has updated_at / updated_by) for is_primary + cost refresh.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.35_suppliers.repository",
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


# ── Source types (read-only) ─────────────────────────────────────────────


async def list_source_types(conn: Any) -> list[dict]:
    return await _repo.list_source_types(conn)


# ── Suppliers ────────────────────────────────────────────────────────────


async def list_suppliers(
    conn: Any,
    *,
    tenant_id: str,
    source_type_id: int | None = None,
    location_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_suppliers(
        conn,
        tenant_id=tenant_id,
        source_type_id=source_type_id,
        location_id=location_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_supplier(
    conn: Any, *, tenant_id: str, supplier_id: str,
) -> dict:
    row = await _repo.get_supplier(
        conn, tenant_id=tenant_id, supplier_id=supplier_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Supplier {supplier_id} not found.")
    return row


async def _validate_supplier_refs(
    conn: Any,
    *,
    tenant_id: str,
    source_type_id: int | None,
    location_id: str | None,
) -> None:
    if source_type_id is not None:
        st = await _repo.get_source_type(conn, source_type_id=source_type_id)
        if st is None:
            raise _errors.ValidationError(
                f"Unknown source_type_id={source_type_id}.",
                code="INVALID_SOURCE_TYPE",
            )
    if location_id is not None:
        ok = await _repo.location_exists(
            conn, tenant_id=tenant_id, location_id=location_id,
        )
        if not ok:
            raise _errors.ValidationError(
                f"Location {location_id} not found for this tenant.",
                code="INVALID_LOCATION",
            )


async def create_supplier(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    await _validate_supplier_refs(
        conn,
        tenant_id=tenant_id,
        source_type_id=data["source_type_id"],
        location_id=data.get("location_id"),
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_supplier(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.suppliers.created",
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
                "entity_kind": "raw_materials.supplier",
                "source_type_code": row.get("source_type_code"),
                "location_id": str(data["location_id"]) if data.get("location_id") else None,
                "slug": data["slug"],
            },
        },
    )
    return row


async def update_supplier(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    supplier_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_supplier(
        conn, tenant_id=tenant_id, supplier_id=supplier_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Supplier {supplier_id} not found.")

    await _validate_supplier_refs(
        conn,
        tenant_id=tenant_id,
        source_type_id=patch.get("source_type_id"),
        location_id=patch.get("location_id"),
    )

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_supplier(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        supplier_id=supplier_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Supplier {supplier_id} not found.")

    changed_fields = sorted([k for k in patch.keys()])
    event_key = (
        "somaerp.raw_materials.suppliers.status_changed"
        if status_changed
        else "somaerp.raw_materials.suppliers.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(supplier_id),
        "entity_kind": "raw_materials.supplier",
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


async def soft_delete_supplier(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    supplier_id: str,
) -> None:
    existing = await _repo.get_supplier(
        conn, tenant_id=tenant_id, supplier_id=supplier_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Supplier {supplier_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_supplier(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        supplier_id=supplier_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Supplier {supplier_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.suppliers.deleted",
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
                "entity_id": str(supplier_id),
                "entity_kind": "raw_materials.supplier",
                "source_type_code": existing.get("source_type_code"),
            },
        },
    )


# ── Material <-> Supplier link ───────────────────────────────────────────


async def list_supplier_links_for_material(
    conn: Any, *, tenant_id: str, material_id: str,
) -> list[dict]:
    ok = await _repo.raw_material_exists(
        conn, tenant_id=tenant_id, material_id=material_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")
    return await _repo.list_supplier_links_for_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )


async def list_material_links_for_supplier(
    conn: Any, *, tenant_id: str, supplier_id: str,
) -> list[dict]:
    existing = await _repo.get_supplier(
        conn, tenant_id=tenant_id, supplier_id=supplier_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Supplier {supplier_id} not found.")
    return await _repo.list_material_links_for_supplier(
        conn, tenant_id=tenant_id, supplier_id=supplier_id,
    )


async def create_link(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
    data: dict,
) -> dict:
    # Validate both FKs exist for this tenant.
    if not await _repo.raw_material_exists(
        conn, tenant_id=tenant_id, material_id=material_id,
    ):
        raise _errors.ValidationError(
            f"Raw material {material_id} not found for this tenant.",
            code="INVALID_RAW_MATERIAL",
        )
    supplier = await _repo.get_supplier(
        conn, tenant_id=tenant_id, supplier_id=data["supplier_id"],
    )
    if supplier is None:
        raise _errors.ValidationError(
            f"Supplier {data['supplier_id']} not found for this tenant.",
            code="INVALID_SUPPLIER",
        )

    # Reject duplicate link.
    existing_link = await _repo.get_link_raw(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        supplier_id=data["supplier_id"],
    )
    if existing_link is not None:
        raise _errors.ValidationError(
            "Link already exists for this (raw_material, supplier).",
            code="DUPLICATE_LINK",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_link(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.material_supplier.linked",
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
                "entity_kind": "raw_materials.material_supplier",
                "raw_material_id": str(material_id),
                "supplier_id": str(data["supplier_id"]),
                "is_primary": bool(row.get("is_primary")),
            },
        },
    )
    return row


async def update_link(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
    supplier_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_link_raw(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        supplier_id=supplier_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Link (material={material_id}, supplier={supplier_id}) not found.",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_link(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
        supplier_id=supplier_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Link (material={material_id}, supplier={supplier_id}) not found.",
        )

    primary_toggled = (
        "is_primary" in patch
        and patch["is_primary"] is not None
        and bool(patch["is_primary"]) != bool(existing["is_primary"])
    )
    changed_fields = sorted([k for k, v in patch.items() if v is not None])

    if primary_toggled:
        event_key = "somaerp.raw_materials.material_supplier.primary_changed"
        metadata: dict[str, Any] = {
            "category": "setup" if is_setup else "operational",
            "entity_id": str(row.get("id")),
            "entity_kind": "raw_materials.material_supplier",
            "raw_material_id": str(material_id),
            "supplier_id": str(supplier_id),
            "is_primary": bool(patch["is_primary"]),
            "previous_is_primary": bool(existing["is_primary"]),
        }
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
    elif changed_fields:
        await tennetctl.audit_emit(
            event_key="somaerp.raw_materials.material_supplier.updated",
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
                    "entity_kind": "raw_materials.material_supplier",
                    "raw_material_id": str(material_id),
                    "supplier_id": str(supplier_id),
                    "changed_fields": changed_fields,
                },
            },
        )
    return row


async def delete_link(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
    supplier_id: str,
) -> None:
    existing = await _repo.get_link_raw(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        supplier_id=supplier_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Link (material={material_id}, supplier={supplier_id}) not found.",
        )

    is_setup = actor_user_id is None

    ok = await _repo.delete_link(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        supplier_id=supplier_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Link (material={material_id}, supplier={supplier_id}) not found.",
        )

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.material_supplier.unlinked",
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
                "entity_id": str(existing["id"]),
                "entity_kind": "raw_materials.material_supplier",
                "raw_material_id": str(material_id),
                "supplier_id": str(supplier_id),
                "was_primary": bool(existing["is_primary"]),
            },
        },
    )
