"""Customers service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.customers.created
  - somaerp.customers.updated            (any non-status field patch)
  - somaerp.customers.status_changed     (status patch transitions)
  - somaerp.customers.deleted
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module("apps.somaerp.backend.02_features.80_customers.repository")
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


async def list_customers(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_customers(conn, **kwargs)


async def get_customer(
    conn: Any, *, tenant_id: str, customer_id: str,
) -> dict:
    row = await _repo.get_customer(
        conn, tenant_id=tenant_id, customer_id=customer_id,
    )
    if row is None:
        raise _errors.NotFoundError(f"Customer {customer_id} not found.")
    return row


async def create_customer(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    # Validate location belongs to tenant (if provided).
    if data.get("location_id"):
        if not await _repo.location_exists(
            conn, tenant_id=tenant_id, location_id=data["location_id"],
        ):
            raise _errors.ValidationError(
                f"Location {data['location_id']} not found for this tenant.",
                code="INVALID_LOCATION",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_customer(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.customers.created",
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
                "entity_kind": "customers.customer",
                "slug": data.get("slug"),
                "status": data.get("status") or "active",
                "location_id": data.get("location_id"),
            },
        },
    )
    return row


async def update_customer(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    customer_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_customer(
        conn, tenant_id=tenant_id, customer_id=customer_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Customer {customer_id} not found.")

    if patch.get("location_id"):
        if not await _repo.location_exists(
            conn, tenant_id=tenant_id, location_id=patch["location_id"],
        ):
            raise _errors.ValidationError(
                f"Location {patch['location_id']} not found for this tenant.",
                code="INVALID_LOCATION",
            )

    status_changed = (
        "status" in patch
        and patch["status"] is not None
        and patch["status"] != existing["status"]
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_customer(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        customer_id=customer_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Customer {customer_id} not found.")

    event_key = (
        "somaerp.customers.status_changed"
        if status_changed
        else "somaerp.customers.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(customer_id),
        "entity_kind": "customers.customer",
        "changed_fields": sorted(
            [k for k, v in patch.items() if v is not None],
        ),
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


async def soft_delete_customer(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    customer_id: str,
) -> None:
    existing = await _repo.get_customer(
        conn, tenant_id=tenant_id, customer_id=customer_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Customer {customer_id} not found.")

    active_subs = await _repo.count_active_subscriptions_for_customer(
        conn, tenant_id=tenant_id, customer_id=customer_id,
    )
    if active_subs > 0:
        raise _errors.ValidationError(
            f"Cannot delete customer with {active_subs} active subscription(s). "
            "Cancel them first.",
            code="DEPENDENCY_VIOLATION",
            status_code=422,
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_customer(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        customer_id=customer_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Customer {customer_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.customers.deleted",
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
                "entity_id": str(customer_id),
                "entity_kind": "customers.customer",
            },
        },
    )
