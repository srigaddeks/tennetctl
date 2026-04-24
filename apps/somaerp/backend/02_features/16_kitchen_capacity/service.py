"""Kitchen capacity service — create / close / delete with audit emission.

Audit keys (per apps/somaerp/03_docs/01_data_model/01_geography.md):
  - somaerp.geography.kitchen_capacity.created
  - somaerp.geography.kitchen_capacity.closed   (PATCH sets valid_to)
  - somaerp.geography.kitchen_capacity.deleted  (rare soft-delete)

Cross-tenant validation:
  - kitchen_id MUST belong to tenant (404 NotFound if not).
  - product_line_id MUST belong to same tenant (422 CROSS_TENANT_REFERENCE).
  - capacity_unit_id MUST exist in the global dim_units_of_measure.

Overlap safety: the DB partial unique index enforces one active row per
(tenant, kitchen, product_line, time_window). On UniqueViolationError we
translate to 409 CAPACITY_WINDOW_CONFLICT.
"""

from __future__ import annotations

from datetime import date
from importlib import import_module
from typing import Any

import asyncpg

_repo = import_module(
    "apps.somaerp.backend.02_features.16_kitchen_capacity.repository",
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


async def _require_kitchen(
    conn: Any, *, tenant_id: str, kitchen_id: str,
) -> None:
    if not await _repo.kitchen_exists_for_tenant(
        conn, tenant_id=tenant_id, kitchen_id=kitchen_id,
    ):
        raise _errors.NotFoundError(f"Kitchen {kitchen_id} not found.")


async def _validate_refs(
    conn: Any,
    *,
    tenant_id: str,
    product_line_id: str,
    capacity_unit_id: int,
) -> None:
    if not await _repo.product_line_exists_for_tenant(
        conn, tenant_id=tenant_id, product_line_id=product_line_id,
    ):
        raise _errors.SomaerpError(
            f"Product line {product_line_id} not found for this tenant.",
            code="CROSS_TENANT_REFERENCE",
            status_code=422,
        )
    if not await _repo.unit_exists(conn, unit_id=capacity_unit_id):
        raise _errors.ValidationError(
            f"Unknown capacity_unit_id={capacity_unit_id}.",
            code="INVALID_UNIT",
        )


# ── Reads ─────────────────────────────────────────────────────────────


async def list_capacity(
    conn: Any,
    *,
    tenant_id: str,
    kitchen_id: str,
    product_line_id: str | None = None,
    valid_on: date | None = None,
    include_history: bool = False,
    limit: int = 50,
    offset: int = 0,
    include_deleted: bool = False,
) -> list[dict]:
    await _require_kitchen(conn, tenant_id=tenant_id, kitchen_id=kitchen_id)
    return await _repo.list_capacity(
        conn,
        tenant_id=tenant_id,
        kitchen_id=kitchen_id,
        product_line_id=product_line_id,
        valid_on=valid_on,
        include_history=include_history,
        limit=limit,
        offset=offset,
        include_deleted=include_deleted,
    )


async def get_capacity(
    conn: Any, *, tenant_id: str, kitchen_id: str, capacity_id: str,
) -> dict:
    await _require_kitchen(conn, tenant_id=tenant_id, kitchen_id=kitchen_id)
    row = await _repo.get_capacity(
        conn,
        tenant_id=tenant_id,
        kitchen_id=kitchen_id,
        capacity_id=capacity_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Capacity {capacity_id} not found.")
    return row


# ── Writes ────────────────────────────────────────────────────────────


async def create_capacity(
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
    await _require_kitchen(conn, tenant_id=tenant_id, kitchen_id=kitchen_id)
    await _validate_refs(
        conn,
        tenant_id=tenant_id,
        product_line_id=data["product_line_id"],
        capacity_unit_id=int(data["capacity_unit_id"]),
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    try:
        row = await _repo.create_capacity(
            conn,
            tenant_id=tenant_id,
            actor_user_id=effective_user,
            kitchen_id=kitchen_id,
            data=data,
        )
    except asyncpg.UniqueViolationError as exc:
        raise _errors.SomaerpError(
            "A capacity row already exists for this "
            "(kitchen, product_line, time_window). "
            "Close the existing row before adding a new one.",
            code="CAPACITY_WINDOW_CONFLICT",
            status_code=409,
        ) from exc

    await tennetctl.audit_emit(
        event_key="somaerp.geography.kitchen_capacity.created",
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
                "entity_kind": "geography.kitchen_capacity",
                "kitchen_id": str(kitchen_id),
                "product_line_id": str(data["product_line_id"]),
                "time_window_start": str(data["time_window_start"]),
                "time_window_end": str(data["time_window_end"]),
                "valid_from": str(data["valid_from"]),
                "valid_to": str(data["valid_to"]) if data.get("valid_to") else None,
            },
        },
    )
    return row


async def close_capacity(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
    capacity_id: str,
    valid_to: date,
) -> dict:
    await _require_kitchen(conn, tenant_id=tenant_id, kitchen_id=kitchen_id)

    existing = await _repo.get_capacity(
        conn,
        tenant_id=tenant_id,
        kitchen_id=kitchen_id,
        capacity_id=capacity_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Capacity {capacity_id} not found.")

    if existing.get("valid_to") is not None:
        raise _errors.SomaerpError(
            f"Capacity {capacity_id} is already closed "
            f"(valid_to={existing['valid_to']}).",
            code="CAPACITY_ALREADY_CLOSED",
            status_code=409,
        )

    # CHECK constraint requires valid_to > valid_from. Surface a friendly 422
    # instead of letting the DB raise a CheckViolationError.
    if valid_to <= existing["valid_from"]:
        raise _errors.ValidationError(
            f"valid_to ({valid_to}) must be greater than "
            f"valid_from ({existing['valid_from']}).",
            code="INVALID_VALID_TO",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.close_capacity(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        kitchen_id=kitchen_id,
        capacity_id=capacity_id,
        valid_to=valid_to,
    )
    if row is None:
        raise _errors.NotFoundError(f"Capacity {capacity_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.kitchen_capacity.closed",
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
                "entity_id": str(capacity_id),
                "entity_kind": "geography.kitchen_capacity",
                "kitchen_id": str(kitchen_id),
                "product_line_id": str(row.get("product_line_id")),
                "time_window_start": str(row.get("time_window_start")),
                "time_window_end": str(row.get("time_window_end")),
                "valid_from": str(row.get("valid_from")),
                "valid_to": str(row.get("valid_to")),
            },
        },
    )
    return row


async def soft_delete_capacity(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    kitchen_id: str,
    capacity_id: str,
) -> None:
    await _require_kitchen(conn, tenant_id=tenant_id, kitchen_id=kitchen_id)

    existing = await _repo.get_capacity(
        conn,
        tenant_id=tenant_id,
        kitchen_id=kitchen_id,
        capacity_id=capacity_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Capacity {capacity_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_capacity(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        kitchen_id=kitchen_id,
        capacity_id=capacity_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Capacity {capacity_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.geography.kitchen_capacity.deleted",
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
                "entity_id": str(capacity_id),
                "entity_kind": "geography.kitchen_capacity",
                "kitchen_id": str(kitchen_id),
                "product_line_id": str(existing.get("product_line_id")),
            },
        },
    )
