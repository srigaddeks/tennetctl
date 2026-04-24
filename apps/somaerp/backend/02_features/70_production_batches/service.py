"""Production batches service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.production.batches.created / .started / .completed / .cancelled
  - somaerp.production.batches.updated / .deleted
  - somaerp.production.steps.updated
  - somaerp.production.consumption.updated
  - somaerp.production.qc.recorded
Auto-emission on completion:
  - somaerp.inventory.movements.consumed (one per line actual_qty > 0)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.70_production_batches.repository",
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


# ── Batches ─────────────────────────────────────────────────────────────


async def list_batches(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_batches(conn, **kwargs)


async def get_batch_detail(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> dict:
    batch = await _repo.get_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if batch is None:
        raise _errors.NotFoundError(f"Batch {batch_id} not found.")
    steps = await _repo.list_batch_steps(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    consumption = await _repo.list_batch_consumption(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    qc_results = await _repo.list_batch_qc_results(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    summary = await _repo.get_batch_summary(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    return {
        "batch": batch,
        "steps": steps,
        "consumption": consumption,
        "qc_results": qc_results,
        "summary": summary,
    }


async def get_batch(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> dict:
    row = await _repo.get_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Batch {batch_id} not found.")
    return row


async def create_batch(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    # Validate kitchen + product existence.
    if not await _repo.kitchen_exists(
        conn, tenant_id=tenant_id, kitchen_id=data["kitchen_id"],
    ):
        raise _errors.ValidationError(
            f"Kitchen {data['kitchen_id']} not found for this tenant.",
            code="INVALID_KITCHEN",
        )
    product = await _repo.get_product(
        conn, tenant_id=tenant_id, product_id=data["product_id"],
    )
    if product is None:
        raise _errors.ValidationError(
            f"Product {data['product_id']} not found for this tenant.",
            code="INVALID_PRODUCT",
        )

    # Resolve recipe.
    recipe_id = data.get("recipe_id")
    if recipe_id:
        recipe = await _repo.get_recipe(
            conn, tenant_id=tenant_id, recipe_id=recipe_id,
        )
        if recipe is None:
            raise _errors.ValidationError(
                f"Recipe {recipe_id} not found for this tenant.",
                code="INVALID_RECIPE",
            )
        if recipe["status"] != "active":
            raise _errors.ValidationError(
                f"Recipe {recipe_id} is not active (status={recipe['status']}).",
                code="RECIPE_NOT_ACTIVE",
            )
        if str(recipe["product_id"]) != str(data["product_id"]):
            raise _errors.ValidationError(
                "Recipe does not belong to the specified product.",
                code="RECIPE_PRODUCT_MISMATCH",
            )
    else:
        recipe = await _repo.get_active_recipe_for_product(
            conn, tenant_id=tenant_id, product_id=data["product_id"],
        )
        if recipe is None:
            raise _errors.ValidationError(
                f"No active recipe found for product {data['product_id']}. "
                "Create and activate a recipe before planning a batch.",
                code="NO_ACTIVE_RECIPE",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    currency_code = product.get("currency_code") or "INR"

    create_data = {
        **data,
        "currency_code": currency_code,
        "recipe_row": recipe,
    }

    batch, recipe_row = await _repo.create_batch(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=create_data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.production.batches.created",
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
                "entity_id": str(batch.get("id")),
                "entity_kind": "production.batch",
                "kitchen_id": str(data["kitchen_id"]),
                "product_id": str(data["product_id"]),
                "recipe_id": str(recipe_row["id"]),
                "recipe_version": int(recipe_row.get("version") or 1),
                "planned_qty": str(data["planned_qty"]),
            },
        },
    )
    return batch


async def patch_batch(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    batch_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Batch {batch_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    updated, event_kind, movements = await _repo.patch_batch(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        existing=existing,
        patch=patch,
    )

    event_key_map = {
        "updated": "somaerp.production.batches.updated",
        "started": "somaerp.production.batches.started",
        "completed": "somaerp.production.batches.completed",
        "cancelled": "somaerp.production.batches.cancelled",
    }
    event_key = event_key_map[event_kind]

    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(batch_id),
        "entity_kind": "production.batch",
    }
    if event_kind != "updated":
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = patch.get("status")
        if event_kind == "completed":
            metadata["actual_qty"] = str(updated.get("actual_qty") or "")
            metadata["movements_emitted"] = movements
        if event_kind == "cancelled":
            metadata["cancel_reason"] = patch.get("cancel_reason")

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

    # Per-line movement audits on completion.
    if event_kind == "completed" and movements > 0:
        await tennetctl.audit_emit(
            event_key="somaerp.inventory.movements.consumed",
            scope=_scope(
                actor_user_id=actor_user_id,
                session_id=session_id,
                org_id=org_id,
                tenant_id=tenant_id,
            ),
            payload={
                "outcome": "success",
                "metadata": {
                    "category": "operational",
                    "entity_kind": "inventory.movement",
                    "movement_type": "consumed",
                    "batch_id": str(batch_id),
                    "kitchen_id": str(existing["kitchen_id"]),
                    "lines": movements,
                },
            },
        )

    return updated


async def soft_delete_batch(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    batch_id: str,
) -> None:
    existing = await _repo.get_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Batch {batch_id} not found.")
    # Only planned or cancelled batches may be soft-deleted.
    if existing["status"] not in ("planned", "cancelled"):
        raise _errors.ValidationError(
            f"Cannot delete a batch in status={existing['status']}.",
            code="INVALID_DELETE_STATE",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_batch(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        batch_id=batch_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Batch {batch_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.production.batches.deleted",
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
                "entity_id": str(batch_id),
                "entity_kind": "production.batch",
            },
        },
    )


# ── Steps ───────────────────────────────────────────────────────────────


async def _require_batch(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> dict:
    row = await _repo.get_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Batch {batch_id} not found.")
    return row


async def list_batch_steps(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> list[dict]:
    await _require_batch(conn, tenant_id=tenant_id, batch_id=batch_id)
    return await _repo.list_batch_steps(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )


async def patch_batch_step(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    batch_id: str,
    step_id: str,
    patch: dict,
) -> dict:
    batch = await _require_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if batch["status"] == "completed":
        raise _errors.ValidationError(
            "Cannot modify steps on a completed batch.",
            code="BATCH_ALREADY_COMPLETED",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.patch_step(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        batch_id=batch_id,
        step_id=step_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Step {step_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    await tennetctl.audit_emit(
        event_key="somaerp.production.steps.updated",
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
                "entity_kind": "production.step_log",
                "batch_id": str(batch_id),
                "changed_fields": changed_fields,
            },
        },
    )
    return row


# ── Consumption ─────────────────────────────────────────────────────────


async def list_batch_consumption(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> list[dict]:
    await _require_batch(conn, tenant_id=tenant_id, batch_id=batch_id)
    return await _repo.list_batch_consumption(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )


async def patch_batch_consumption(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    batch_id: str,
    line_id: str,
    patch: dict,
) -> dict:
    batch = await _require_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if batch["status"] == "completed":
        raise _errors.ValidationError(
            "Cannot modify consumption on a completed batch.",
            code="BATCH_ALREADY_COMPLETED",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.patch_consumption(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        batch_id=batch_id,
        line_id=line_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Consumption line {line_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    await tennetctl.audit_emit(
        event_key="somaerp.production.consumption.updated",
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
                "entity_id": str(line_id),
                "entity_kind": "production.consumption",
                "batch_id": str(batch_id),
                "changed_fields": changed_fields,
            },
        },
    )
    return row


# ── QC ──────────────────────────────────────────────────────────────────


async def list_batch_qc_results(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> list[dict]:
    await _require_batch(conn, tenant_id=tenant_id, batch_id=batch_id)
    return await _repo.list_batch_qc_results(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )


async def record_batch_qc(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    batch_id: str,
    data: dict,
) -> dict:
    batch = await _require_batch(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )

    if not await _repo.checkpoint_exists(
        conn, tenant_id=tenant_id, checkpoint_id=data["checkpoint_id"],
    ):
        raise _errors.ValidationError(
            f"Checkpoint {data['checkpoint_id']} not found for this tenant.",
            code="INVALID_CHECKPOINT",
        )
    if not await _repo.outcome_exists(
        conn, outcome_id=int(data["outcome_id"]),
    ):
        raise _errors.ValidationError(
            f"Unknown outcome_id={data['outcome_id']}.",
            code="INVALID_OUTCOME",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row, event_id = await _repo.record_batch_qc(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        batch=batch,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.production.qc.recorded",
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
                "entity_id": str(row.get("id") or ""),
                "entity_kind": "production.qc_result",
                "batch_id": str(batch_id),
                "checkpoint_id": str(data["checkpoint_id"]),
                "outcome_id": int(data["outcome_id"]),
                "event_id": str(event_id),
            },
        },
    )
    return row


# ── Summary ─────────────────────────────────────────────────────────────


async def get_batch_summary(
    conn: Any, *, tenant_id: str, batch_id: str,
) -> dict:
    await _require_batch(conn, tenant_id=tenant_id, batch_id=batch_id)
    row = await _repo.get_batch_summary(
        conn, tenant_id=tenant_id, batch_id=batch_id,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Batch summary not found for {batch_id}.",
        )
    return row


# ── Today's board ──────────────────────────────────────────────────────


async def get_todays_board(
    conn: Any, *, tenant_id: str, on_date: Any,
) -> list[dict]:
    """Return list of {kitchen_id, kitchen_name, batches: [{batch, summary}]}
    for a given date.
    """
    rows = await _repo.list_batches(
        conn,
        tenant_id=tenant_id,
        run_date_from=on_date,
        run_date_to=on_date,
        limit=500,
        offset=0,
    )
    grouped: dict[str, dict] = {}
    for b in rows:
        kid = b["kitchen_id"]
        if kid not in grouped:
            grouped[kid] = {
                "kitchen_id": kid,
                "kitchen_name": b.get("kitchen_name"),
                "batches": [],
            }
        summary = await _repo.get_batch_summary(
            conn, tenant_id=tenant_id, batch_id=b["id"],
        )
        grouped[kid]["batches"].append({"batch": b, "summary": summary})
    return list(grouped.values())
