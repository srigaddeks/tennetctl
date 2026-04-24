"""Inventory service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.inventory.movements.{received|consumed|wasted|adjusted|expired}
  - somaerp.inventory.plan.computed
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.65_inventory.repository",
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


# ── Read-only ───────────────────────────────────────────────────────────


async def list_current(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_current(conn, **kwargs)


async def list_movements(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_movements(conn, **kwargs)


# ── Record movement (manual adjustments) ────────────────────────────────


async def record_movement(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if actor_user_id is None:
        raise _errors.AuthError(
            "Recording an inventory movement requires an authenticated user.",
        )

    if not await _repo.kitchen_exists(
        conn, tenant_id=tenant_id, kitchen_id=data["kitchen_id"],
    ):
        raise _errors.ValidationError(
            f"Kitchen {data['kitchen_id']} not found for this tenant.",
            code="INVALID_KITCHEN",
        )
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

    # Reason required for waste/adjusted/expired.
    if data["movement_type"] in ("wasted", "adjusted", "expired") and not data.get("reason"):
        raise _errors.ValidationError(
            f"`reason` is required for movement_type={data['movement_type']}.",
            code="MISSING_REASON",
        )

    row = await _repo.record_movement(
        conn,
        tenant_id=tenant_id,
        performed_by_user_id=actor_user_id,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key=f"somaerp.inventory.movements.{data['movement_type']}",
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
                "entity_id": str(row.get("id")),
                "entity_kind": "inventory.movement",
                "movement_type": data["movement_type"],
                "kitchen_id": str(data["kitchen_id"]),
                "raw_material_id": str(data["raw_material_id"]),
                "quantity": str(data["quantity"]),
                "unit_id": int(data["unit_id"]),
                "reason": data.get("reason"),
            },
        },
    )
    return row


# ── MRP-lite planner ────────────────────────────────────────────────────


async def compute_plan(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
    demand: list[dict],
) -> dict:
    result = await _repo.compute_plan(
        conn,
        tenant_id=tenant_id,
        kitchen_id=kitchen_id,
        demand=demand,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.inventory.plan.computed",
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
                "entity_kind": "inventory.plan",
                "kitchen_id": str(kitchen_id),
                "demand_count": len(demand),
                "requirements_count": len(result.get("requirements", [])),
                "error_count": len(result.get("errors", [])),
                "unconvertible_count": len(result.get("unconvertible_units", [])),
            },
        },
    )
    return result
