"""Delivery routes service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.delivery.routes.created / .updated / .status_changed / .deleted
  - somaerp.delivery.route_customers.attached / .detached / .reordered
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.90_delivery_routes.repository",
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


# ── Routes ─────────────────────────────────────────────────────────────


async def list_routes(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_routes(conn, **kwargs)


async def get_route(
    conn: Any, *, tenant_id: str, route_id: str,
) -> dict:
    row = await _repo.get_route(
        conn, tenant_id=tenant_id, route_id=route_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Route {route_id} not found.")
    return row


async def create_route(
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

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_route(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.routes.created",
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
                "entity_kind": "delivery.route",
                "kitchen_id": str(data["kitchen_id"]),
                "slug": data.get("slug"),
            },
        },
    )
    return row


async def update_route(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    route_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_route(
        conn, tenant_id=tenant_id, route_id=route_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Route {route_id} not found.")

    if patch.get("kitchen_id") is not None:
        if not await _repo.kitchen_exists(
            conn, tenant_id=tenant_id, kitchen_id=patch["kitchen_id"],
        ):
            raise _errors.ValidationError(
                f"Kitchen {patch['kitchen_id']} not found for this tenant.",
                code="INVALID_KITCHEN",
            )

    status_changed = (
        "status" in patch
        and patch["status"] is not None
        and patch["status"] != existing["status"]
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_route(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        route_id=route_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Route {route_id} not found.")

    event_key = (
        "somaerp.delivery.routes.status_changed"
        if status_changed
        else "somaerp.delivery.routes.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(route_id),
        "entity_kind": "delivery.route",
        "changed_fields": sorted([k for k, v in patch.items() if v is not None]),
    }
    if status_changed:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = patch["status"]

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


async def soft_delete_route(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    route_id: str,
) -> None:
    existing = await _repo.get_route(
        conn, tenant_id=tenant_id, route_id=route_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Route {route_id} not found.")

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_route(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        route_id=route_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Route {route_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.delivery.routes.deleted",
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
                "entity_id": str(route_id),
                "entity_kind": "delivery.route",
            },
        },
    )


# ── Route customers ───────────────────────────────────────────────────


async def _require_route(
    conn: Any, *, tenant_id: str, route_id: str,
) -> dict:
    row = await _repo.get_route(
        conn, tenant_id=tenant_id, route_id=route_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Route {route_id} not found.")
    return row


async def list_route_customers(
    conn: Any, *, tenant_id: str, route_id: str,
) -> list[dict]:
    await _require_route(conn, tenant_id=tenant_id, route_id=route_id)
    return await _repo.list_route_customers(
        conn, tenant_id=tenant_id, route_id=route_id,
    )


async def attach_route_customer(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    route_id: str,
    data: dict,
) -> dict:
    await _require_route(conn, tenant_id=tenant_id, route_id=route_id)
    if not await _repo.customer_exists(
        conn, tenant_id=tenant_id, customer_id=data["customer_id"],
    ):
        raise _errors.ValidationError(
            f"Customer {data['customer_id']} not found for this tenant.",
            code="INVALID_CUSTOMER",
        )
    if await _repo.link_exists(
        conn,
        tenant_id=tenant_id,
        route_id=route_id,
        customer_id=data["customer_id"],
    ):
        raise _errors.ValidationError(
            "Customer is already on this route.",
            code="CUSTOMER_ALREADY_ATTACHED",
            status_code=409,
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.attach_customer(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        route_id=route_id,
        customer_id=data["customer_id"],
        sequence_position=data.get("sequence_position"),
    )
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.route_customers.attached",
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
                "entity_kind": "delivery.route_customer",
                "route_id": str(route_id),
                "customer_id": str(data["customer_id"]),
                "sequence_position": int(row.get("sequence_position") or 0),
            },
        },
    )
    return row


async def detach_route_customer(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    route_id: str,
    customer_id: str,
) -> None:
    await _require_route(conn, tenant_id=tenant_id, route_id=route_id)
    ok = await _repo.detach_customer(
        conn,
        tenant_id=tenant_id,
        route_id=route_id,
        customer_id=customer_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Customer {customer_id} not on route {route_id}.",
        )
    is_setup = actor_user_id is None
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.route_customers.detached",
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
                "entity_kind": "delivery.route_customer",
                "route_id": str(route_id),
                "customer_id": str(customer_id),
            },
        },
    )


async def reorder_route_customers(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    route_id: str,
    customer_ids: list[str],
) -> list[dict]:
    await _require_route(conn, tenant_id=tenant_id, route_id=route_id)
    # Validate all customers exist for this tenant.
    for cid in customer_ids:
        if not await _repo.customer_exists(
            conn, tenant_id=tenant_id, customer_id=cid,
        ):
            raise _errors.ValidationError(
                f"Customer {cid} not found for this tenant.",
                code="INVALID_CUSTOMER",
            )
    # Detect duplicates.
    if len(set(customer_ids)) != len(customer_ids):
        raise _errors.ValidationError(
            "Duplicate customer_id in reorder payload.",
            code="DUPLICATE_CUSTOMER_ID",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    rows = await _repo.reorder_customers(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        route_id=route_id,
        customer_ids=customer_ids,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.delivery.route_customers.reordered",
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
                "entity_kind": "delivery.route_customer",
                "route_id": str(route_id),
                "new_count": len(customer_ids),
            },
        },
    )
    return rows
