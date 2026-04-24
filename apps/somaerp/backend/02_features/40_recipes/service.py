"""Recipes service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.recipes.created / .updated / .status_changed / .deleted
  - somaerp.recipes.ingredients.created / .updated / .deleted
  - somaerp.recipes.steps.created / .updated / .deleted
  - somaerp.recipes.step_equipment.linked / .unlinked

Rules:
  - Status transitions to 'active' atomically archive the prior active
    recipe for the same product (handled in repo transaction).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.40_recipes.repository",
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


# ── Recipes ──────────────────────────────────────────────────────────────


async def list_recipes(
    conn: Any,
    *,
    tenant_id: str,
    product_id: str | None = None,
    status: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    return await _repo.list_recipes(
        conn,
        tenant_id=tenant_id,
        product_id=product_id,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_recipe(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> dict:
    row = await _repo.get_recipe(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")
    return row


async def create_recipe(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.product_exists(
        conn, tenant_id=tenant_id, product_id=data["product_id"],
    ):
        raise _errors.ValidationError(
            f"Product {data['product_id']} not found for this tenant.",
            code="INVALID_PRODUCT",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_recipe(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.created",
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
                "entity_kind": "recipes.recipe",
                "product_id": str(data["product_id"]),
                "version": int(row.get("version") or 1),
                "status": row.get("status"),
            },
        },
    )
    return row


async def update_recipe(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_recipe(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")

    new_status = patch.pop("status", None)
    status_changed = (
        new_status is not None and new_status != existing["status"]
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_recipe(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        patch=patch,
        new_status=new_status if status_changed else None,
        existing_product_id=str(existing["product_id"]),
    )
    if row is None:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(recipe_id),
        "entity_kind": "recipes.recipe",
        "changed_fields": changed_fields,
    }
    event_key = "somaerp.recipes.updated"
    if status_changed:
        event_key = "somaerp.recipes.status_changed"
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = new_status

    if changed_fields or status_changed:
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


async def soft_delete_recipe(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
) -> None:
    existing = await _repo.get_recipe(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_recipe(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.deleted",
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
                "entity_id": str(recipe_id),
                "entity_kind": "recipes.recipe",
            },
        },
    )


# ── Ingredients ──────────────────────────────────────────────────────────


async def _require_recipe(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> dict:
    row = await _repo.get_recipe(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")
    return row


async def list_ingredients(
    conn: Any, *, tenant_id: str, recipe_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)
    return await _repo.list_ingredients(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
        include_deleted=include_deleted,
    )


async def create_ingredient(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    data: dict,
) -> dict:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    if not await _repo.raw_material_exists(
        conn, tenant_id=tenant_id, material_id=data["raw_material_id"],
    ):
        raise _errors.ValidationError(
            f"Raw material {data['raw_material_id']} not found for this tenant.",
            code="INVALID_RAW_MATERIAL",
        )
    if not await _repo.unit_exists(conn, unit_id=int(data["unit_id"])):
        raise _errors.ValidationError(
            f"Unknown unit_id={data['unit_id']}.", code="INVALID_UNIT",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_ingredient(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.ingredients.created",
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
                "entity_kind": "recipes.ingredient",
                "recipe_id": str(recipe_id),
                "raw_material_id": str(data["raw_material_id"]),
            },
        },
    )
    return row


async def update_ingredient(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    ingredient_id: str,
    patch: dict,
) -> dict:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    if patch.get("raw_material_id") is not None:
        if not await _repo.raw_material_exists(
            conn, tenant_id=tenant_id, material_id=patch["raw_material_id"],
        ):
            raise _errors.ValidationError(
                f"Raw material {patch['raw_material_id']} not found for this tenant.",
                code="INVALID_RAW_MATERIAL",
            )
    if patch.get("unit_id") is not None:
        if not await _repo.unit_exists(conn, unit_id=int(patch["unit_id"])):
            raise _errors.ValidationError(
                f"Unknown unit_id={patch['unit_id']}.", code="INVALID_UNIT",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_ingredient(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Ingredient {ingredient_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    if changed_fields:
        await tennetctl.audit_emit(
            event_key="somaerp.recipes.ingredients.updated",
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
                    "entity_id": str(ingredient_id),
                    "entity_kind": "recipes.ingredient",
                    "recipe_id": str(recipe_id),
                    "changed_fields": changed_fields,
                },
            },
        )
    return row


async def delete_ingredient(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    ingredient_id: str,
) -> None:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_ingredient(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        ingredient_id=ingredient_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Ingredient {ingredient_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.ingredients.deleted",
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
                "entity_id": str(ingredient_id),
                "entity_kind": "recipes.ingredient",
                "recipe_id": str(recipe_id),
            },
        },
    )


# ── Steps ────────────────────────────────────────────────────────────────


async def list_steps(
    conn: Any, *, tenant_id: str, recipe_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)
    return await _repo.list_steps(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
        include_deleted=include_deleted,
    )


async def create_step(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    data: dict,
) -> dict:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_step(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.steps.created",
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
                "entity_kind": "recipes.step",
                "recipe_id": str(recipe_id),
                "step_number": int(row.get("step_number") or 0),
            },
        },
    )
    return row


async def update_step(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    step_id: str,
    patch: dict,
) -> dict:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_step(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        step_id=step_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Step {step_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    if changed_fields:
        await tennetctl.audit_emit(
            event_key="somaerp.recipes.steps.updated",
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
                    "entity_id": str(step_id),
                    "entity_kind": "recipes.step",
                    "recipe_id": str(recipe_id),
                    "changed_fields": changed_fields,
                },
            },
        )
    return row


async def delete_step(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    step_id: str,
) -> None:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_step(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        recipe_id=recipe_id,
        step_id=step_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Step {step_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.steps.deleted",
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
                "entity_id": str(step_id),
                "entity_kind": "recipes.step",
                "recipe_id": str(recipe_id),
            },
        },
    )


# ── Step <-> Equipment link ─────────────────────────────────────────────


async def list_step_equipment(
    conn: Any, *, tenant_id: str, recipe_id: str, step_id: str,
) -> list[dict]:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)
    step = await _repo.get_step(
        conn, tenant_id=tenant_id, recipe_id=recipe_id, step_id=step_id,
    )
    if step is None:
        raise _errors.NotFoundError(f"Step {step_id} not found.")
    return await _repo.list_step_equipment(
        conn, tenant_id=tenant_id, step_id=step_id,
    )


async def link_step_equipment(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    step_id: str,
    equipment_id: str,
) -> dict:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)
    step = await _repo.get_step(
        conn, tenant_id=tenant_id, recipe_id=recipe_id, step_id=step_id,
    )
    if step is None:
        raise _errors.NotFoundError(f"Step {step_id} not found.")

    if not await _repo.equipment_exists(
        conn, tenant_id=tenant_id, equipment_id=equipment_id,
    ):
        raise _errors.ValidationError(
            f"Equipment {equipment_id} not found for this tenant.",
            code="INVALID_EQUIPMENT",
        )

    existing = await _repo.get_step_equipment_link(
        conn, tenant_id=tenant_id, step_id=step_id, equipment_id=equipment_id,
    )
    if existing is not None:
        raise _errors.ValidationError(
            "Link already exists for this (step, equipment).",
            code="DUPLICATE_LINK",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_step_equipment_link(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        step_id=step_id,
        equipment_id=equipment_id,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.step_equipment.linked",
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
                "entity_kind": "recipes.step_equipment",
                "recipe_id": str(recipe_id),
                "step_id": str(step_id),
                "equipment_id": str(equipment_id),
            },
        },
    )
    return row


async def unlink_step_equipment(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    recipe_id: str,
    step_id: str,
    equipment_id: str,
) -> None:
    await _require_recipe(conn, tenant_id=tenant_id, recipe_id=recipe_id)

    is_setup = actor_user_id is None

    ok = await _repo.delete_step_equipment_link(
        conn, tenant_id=tenant_id, step_id=step_id, equipment_id=equipment_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Link (step={step_id}, equipment={equipment_id}) not found.",
        )

    await tennetctl.audit_emit(
        event_key="somaerp.recipes.step_equipment.unlinked",
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
                "entity_kind": "recipes.step_equipment",
                "recipe_id": str(recipe_id),
                "step_id": str(step_id),
                "equipment_id": str(equipment_id),
            },
        },
    )


# ── Cost ────────────────────────────────────────────────────────────────


async def get_recipe_cost(
    conn: Any, *, tenant_id: str, recipe_id: str,
) -> dict:
    row = await _repo.get_recipe_cost(
        conn, tenant_id=tenant_id, recipe_id=recipe_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Recipe {recipe_id} not found.")
    return row
