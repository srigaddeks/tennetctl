"""Raw materials + variants + category/unit reads — service orchestration.

Audit keys:
  - somaerp.raw_materials.materials.created / .updated / .status_changed / .deleted
  - somaerp.raw_materials.variants.created / .updated / .deleted

Cross-layer validation:
  - create/update_material: category_id + default_unit_id must exist in dims (422).
  - create/update_variant : parent material must exist for tenant (404/422).

TODO(56-07): DELETE material with active recipes must return 422
DEPENDENCY_VIOLATION. fct_recipes does not exist yet.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.30_raw_materials.repository",
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


# ── Dim reads (no audit) ─────────────────────────────────────────────────


async def list_categories(conn: Any) -> list[dict]:
    return await _repo.list_categories(conn)


async def list_units(conn: Any) -> list[dict]:
    return await _repo.list_units(conn)


# ── Raw materials ────────────────────────────────────────────────────────


async def list_materials(
    conn: Any,
    *,
    tenant_id: str,
    category_id: int | None = None,
    status: str | None = None,
    q: str | None = None,
    requires_lot_tracking: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_materials(
        conn,
        tenant_id=tenant_id,
        category_id=category_id,
        status=status,
        q=q,
        requires_lot_tracking=requires_lot_tracking,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_material(
    conn: Any, *, tenant_id: str, material_id: str,
) -> dict:
    row = await _repo.get_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")
    return row


async def _validate_refs(
    conn: Any, *, category_id: int | None, default_unit_id: int | None,
) -> None:
    if category_id is not None:
        cat = await _repo.get_category(conn, category_id=category_id)
        if cat is None:
            raise _errors.ValidationError(
                f"Unknown category_id={category_id}.",
                code="INVALID_CATEGORY",
            )
    if default_unit_id is not None:
        unit = await _repo.get_unit(conn, unit_id=default_unit_id)
        if unit is None:
            raise _errors.ValidationError(
                f"Unknown default_unit_id={default_unit_id}.",
                code="INVALID_UNIT",
            )


async def create_material(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    await _validate_refs(
        conn,
        category_id=data["category_id"],
        default_unit_id=data["default_unit_id"],
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_material(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.materials.created",
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
                "entity_kind": "raw_materials.material",
                "category_code": row.get("category_code"),
                "default_unit_code": row.get("default_unit_code"),
                "slug": data["slug"],
                "currency_code": data["currency_code"],
            },
        },
    )
    return row


async def update_material(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")

    await _validate_refs(
        conn,
        category_id=patch.get("category_id"),
        default_unit_id=patch.get("default_unit_id"),
    )

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_material(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    event_key = (
        "somaerp.raw_materials.materials.status_changed"
        if status_changed
        else "somaerp.raw_materials.materials.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(material_id),
        "entity_kind": "raw_materials.material",
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


async def soft_delete_material(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
) -> None:
    existing = await _repo.get_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")

    # TODO(56-07): block delete if active fct_recipes reference this material.

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_material(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.materials.deleted",
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
                "entity_id": str(material_id),
                "entity_kind": "raw_materials.material",
                "category_code": existing.get("category_code"),
            },
        },
    )


# ── Raw material variants ────────────────────────────────────────────────


async def list_variants(
    conn: Any,
    *,
    tenant_id: str,
    material_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    parent = await _repo.get_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )
    if parent is None:
        raise _errors.NotFoundError(f"Raw material {material_id} not found.")
    return await _repo.list_variants(
        conn,
        tenant_id=tenant_id,
        material_id=material_id,
        include_deleted=include_deleted,
    )


async def get_variant(
    conn: Any, *, tenant_id: str, material_id: str, variant_id: str,
) -> dict:
    row = await _repo.get_variant(
        conn, tenant_id=tenant_id, material_id=material_id,
        variant_id=variant_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")
    return row


async def create_variant(
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
    parent = await _repo.get_material(
        conn, tenant_id=tenant_id, material_id=material_id,
    )
    if parent is None:
        raise _errors.ValidationError(
            f"Raw material {material_id} not found for this tenant.",
            code="INVALID_RAW_MATERIAL",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_variant(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.variants.created",
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
                "entity_kind": "raw_materials.variant",
                "raw_material_id": str(material_id),
                "is_default": bool(row.get("is_default")),
            },
        },
    )
    return row


async def update_variant(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
    variant_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_variant(
        conn, tenant_id=tenant_id, material_id=material_id,
        variant_id=variant_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_variant(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
        variant_id=variant_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    if changed_fields:
        await tennetctl.audit_emit(
            event_key="somaerp.raw_materials.variants.updated",
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
                    "entity_id": str(variant_id),
                    "entity_kind": "raw_materials.variant",
                    "raw_material_id": str(material_id),
                    "changed_fields": changed_fields,
                },
            },
        )
    return row


async def soft_delete_variant(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    material_id: str,
    variant_id: str,
) -> None:
    existing = await _repo.get_variant(
        conn, tenant_id=tenant_id, material_id=material_id,
        variant_id=variant_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_variant(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        material_id=material_id,
        variant_id=variant_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Variant {variant_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.raw_materials.variants.deleted",
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
                "entity_id": str(variant_id),
                "entity_kind": "raw_materials.variant",
                "raw_material_id": str(material_id),
            },
        },
    )
