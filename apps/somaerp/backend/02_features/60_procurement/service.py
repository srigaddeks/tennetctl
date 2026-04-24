"""Procurement service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.procurement.runs.created / .status_changed / .updated / .deleted
  - somaerp.procurement.lines.created / .updated / .deleted
  - somaerp.inventory.movements.received / .adjusted / .consumed
    (emitted here because line mutations side-effect into evt_inventory_movements)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.60_procurement.repository",
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


# ── Runs ────────────────────────────────────────────────────────────────


async def list_runs(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_runs(conn, **kwargs)


async def get_run(
    conn: Any, *, tenant_id: str, run_id: str,
) -> dict:
    row = await _repo.get_run(conn, tenant_id=tenant_id, run_id=run_id)
    if row is None:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")
    return row


async def create_run(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.kitchen_exists(
        conn, tenant_id=tenant_id, kitchen_id=data["kitchen_id"],
    ):
        raise _errors.ValidationError(
            f"Kitchen {data['kitchen_id']} not found for this tenant.",
            code="INVALID_KITCHEN",
        )
    if not await _repo.supplier_exists(
        conn, tenant_id=tenant_id, supplier_id=data["supplier_id"],
    ):
        raise _errors.ValidationError(
            f"Supplier {data['supplier_id']} not found for this tenant.",
            code="INVALID_SUPPLIER",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_run(
        conn, tenant_id=tenant_id, actor_user_id=effective_user, data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.procurement.runs.created",
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
                "entity_kind": "procurement.run",
                "kitchen_id": str(data["kitchen_id"]),
                "supplier_id": str(data["supplier_id"]),
                "run_date": str(data["run_date"]),
                "currency_code": data["currency_code"],
            },
        },
    )
    return row


async def update_run(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_run(
        conn, tenant_id=tenant_id, run_id=run_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")

    new_status = patch.get("status")
    status_changed = new_status is not None and new_status != existing["status"]
    if status_changed:
        # Enforce allowed transitions: active -> reconciled | cancelled
        allowed = {
            "active": {"reconciled", "cancelled"},
            "reconciled": set(),
            "cancelled": set(),
        }
        current = existing["status"]
        if new_status not in allowed.get(current, set()):
            raise _errors.ValidationError(
                f"Invalid status transition {current} -> {new_status}.",
                code="INVALID_STATUS_TRANSITION",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_run(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run_id=run_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    event_key = (
        "somaerp.procurement.runs.status_changed"
        if status_changed
        else "somaerp.procurement.runs.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(run_id),
        "entity_kind": "procurement.run",
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


async def soft_delete_run(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
) -> None:
    existing = await _repo.get_run(
        conn, tenant_id=tenant_id, run_id=run_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_run(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run_id=run_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.procurement.runs.deleted",
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
                "entity_id": str(run_id),
                "entity_kind": "procurement.run",
            },
        },
    )


# ── Lines ───────────────────────────────────────────────────────────────


async def _require_run(
    conn: Any, *, tenant_id: str, run_id: str,
) -> dict:
    row = await _repo.get_run(conn, tenant_id=tenant_id, run_id=run_id)
    if row is None:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")
    if row.get("status") != "active":
        raise _errors.ValidationError(
            f"Cannot mutate lines on a {row.get('status')} run.",
            code="RUN_NOT_ACTIVE",
        )
    return row


async def list_lines(
    conn: Any, *, tenant_id: str, run_id: str,
    include_deleted: bool = False,
) -> list[dict]:
    # get_run enforces tenant scoping + not-deleted
    row = await _repo.get_run(conn, tenant_id=tenant_id, run_id=run_id)
    if row is None:
        raise _errors.NotFoundError(f"Procurement run {run_id} not found.")
    return await _repo.list_lines(
        conn, tenant_id=tenant_id, run_id=run_id,
        include_deleted=include_deleted,
    )


async def add_line(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
    data: dict,
) -> dict:
    run = await _require_run(conn, tenant_id=tenant_id, run_id=run_id)

    if not await _repo.raw_material_exists(
        conn, tenant_id=tenant_id, raw_material_id=data["raw_material_id"],
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

    line, movement_id = await _repo.add_line(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run=run,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.procurement.lines.created",
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
                "entity_id": str(line.get("id")),
                "entity_kind": "procurement.line",
                "procurement_run_id": str(run_id),
                "raw_material_id": str(data["raw_material_id"]),
                "quantity": str(data["quantity"]),
                "unit_id": int(data["unit_id"]),
            },
        },
    )
    await tennetctl.audit_emit(
        event_key="somaerp.inventory.movements.received",
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
                "entity_id": str(movement_id),
                "entity_kind": "inventory.movement",
                "movement_type": "received",
                "kitchen_id": str(run["kitchen_id"]),
                "raw_material_id": str(data["raw_material_id"]),
                "procurement_run_id": str(run_id),
                "procurement_line_id": str(line.get("id")),
            },
        },
    )
    return line


async def patch_line(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
    line_id: str,
    patch: dict,
) -> dict:
    run = await _require_run(conn, tenant_id=tenant_id, run_id=run_id)
    existing = await _repo.get_line(
        conn, tenant_id=tenant_id, run_id=run_id, line_id=line_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Line {line_id} not found.")

    if patch.get("unit_id") is not None:
        if not await _repo.unit_exists(conn, unit_id=int(patch["unit_id"])):
            raise _errors.ValidationError(
                f"Unknown unit_id={patch['unit_id']}.", code="INVALID_UNIT",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.patch_line(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run=run,
        existing_line=existing,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Line {line_id} not found.")

    # Auto-create inventory movement when a line is being marked received
    # (received_at is set and was not previously set) and quantity is not
    # also changing (quantity-change path already emitted a movement above).
    if (
        patch.get("received_at") is not None
        and existing.get("received_at") is None
        and patch.get("quantity") is None
    ):
        _inv_repo = import_module(
            "apps.somaerp.backend.02_features.65_inventory.repository",
        )
        await _inv_repo.record_movement(
            conn,
            tenant_id=tenant_id,
            performed_by_user_id=effective_user,
            data={
                "kitchen_id": run["kitchen_id"],
                "raw_material_id": existing["raw_material_id"],
                "movement_type": "received",
                "quantity": existing["quantity"],
                "unit_id": existing["unit_id"],
                "lot_number": patch.get("lot_number") or existing.get("lot_number"),
                "metadata": {
                    "source": "procurement_line_received",
                    "procurement_run_id": str(run_id),
                    "line_id": str(line_id),
                },
            },
        )

    changed_fields = sorted([k for k, v in patch.items() if v is not None])
    if changed_fields:
        await tennetctl.audit_emit(
            event_key="somaerp.procurement.lines.updated",
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
                    "entity_kind": "procurement.line",
                    "procurement_run_id": str(run_id),
                    "changed_fields": changed_fields,
                },
            },
        )
    return row


async def delete_line(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    run_id: str,
    line_id: str,
) -> None:
    run = await _require_run(conn, tenant_id=tenant_id, run_id=run_id)
    existing = await _repo.get_line(
        conn, tenant_id=tenant_id, run_id=run_id, line_id=line_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Line {line_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_line(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        run=run,
        existing_line=existing,
    )
    if not ok:
        raise _errors.NotFoundError(f"Line {line_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.procurement.lines.deleted",
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
                "entity_kind": "procurement.line",
                "procurement_run_id": str(run_id),
            },
        },
    )
