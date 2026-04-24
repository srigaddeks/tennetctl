"""Subscriptions service — orchestrates repo + audit emission.

Audit keys:
  - somaerp.subscriptions.plans.created / .updated / .status_changed / .deleted
  - somaerp.subscriptions.plan_items.created / .updated / .deleted
  - somaerp.subscriptions.subscriptions.created / .updated / .paused /
    .resumed / .cancelled / .ended / .deleted
  - somaerp.subscriptions.events.logged   (every transition emits this too)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo = import_module(
    "apps.somaerp.backend.02_features.85_subscriptions.repository",
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


# ── Frequencies ────────────────────────────────────────────────────────

async def list_frequencies(conn: Any) -> list[dict]:
    return await _repo.list_frequencies(conn)


# ── Plans ──────────────────────────────────────────────────────────────

async def list_plans(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_plans(conn, **kwargs)


async def get_plan_detail(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> dict:
    plan = await _repo.get_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    if plan is None:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")
    items = await _repo.list_plan_items(
        conn, tenant_id=tenant_id, plan_id=plan_id,
    )
    return {"plan": plan, "items": items}


async def get_plan(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> dict:
    row = await _repo.get_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    if row is None:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")
    return row


async def create_plan(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.frequency_exists(
        conn, frequency_id=int(data["frequency_id"]),
    ):
        raise _errors.ValidationError(
            f"Unknown frequency_id={data['frequency_id']}.",
            code="INVALID_FREQUENCY",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_plan(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.plans.created",
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
                "entity_kind": "subscriptions.plan",
                "slug": data.get("slug"),
                "frequency_id": int(data["frequency_id"]),
                "status": data.get("status") or "active",
            },
        },
    )
    return row


async def update_plan(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    plan_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_plan(
        conn, tenant_id=tenant_id, plan_id=plan_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")

    if patch.get("frequency_id") is not None:
        if not await _repo.frequency_exists(
            conn, frequency_id=int(patch["frequency_id"]),
        ):
            raise _errors.ValidationError(
                f"Unknown frequency_id={patch['frequency_id']}.",
                code="INVALID_FREQUENCY",
            )

    status_changed = (
        "status" in patch
        and patch["status"] is not None
        and patch["status"] != existing["status"]
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_plan(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        plan_id=plan_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")

    event_key = (
        "somaerp.subscriptions.plans.status_changed"
        if status_changed
        else "somaerp.subscriptions.plans.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(plan_id),
        "entity_kind": "subscriptions.plan",
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


async def soft_delete_plan(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    plan_id: str,
) -> None:
    existing = await _repo.get_plan(
        conn, tenant_id=tenant_id, plan_id=plan_id,
    )
    if existing is None:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")

    active = await _repo.count_active_subscriptions_for_plan(
        conn, tenant_id=tenant_id, plan_id=plan_id,
    )
    if active > 0:
        raise _errors.ValidationError(
            f"Cannot delete plan with {active} active subscription(s). "
            "Cancel or move them first.",
            code="DEPENDENCY_VIOLATION",
            status_code=422,
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_plan(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        plan_id=plan_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")

    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.plans.deleted",
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
                "entity_id": str(plan_id),
                "entity_kind": "subscriptions.plan",
            },
        },
    )


# ── Plan items ────────────────────────────────────────────────────────

async def _require_plan(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> dict:
    plan = await _repo.get_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    if plan is None:
        raise _errors.NotFoundError(f"Plan {plan_id} not found.")
    return plan


async def list_plan_items(
    conn: Any, *, tenant_id: str, plan_id: str,
) -> list[dict]:
    await _require_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    return await _repo.list_plan_items(
        conn, tenant_id=tenant_id, plan_id=plan_id,
    )


async def _validate_item_refs(
    conn: Any, *, tenant_id: str, product_id: str, variant_id: str | None,
) -> None:
    if not await _repo.product_exists(
        conn, tenant_id=tenant_id, product_id=product_id,
    ):
        raise _errors.ValidationError(
            f"Product {product_id} not found for this tenant.",
            code="INVALID_PRODUCT",
        )
    if variant_id is not None:
        if not await _repo.variant_exists_for_product(
            conn,
            tenant_id=tenant_id,
            variant_id=variant_id,
            product_id=product_id,
        ):
            raise _errors.ValidationError(
                f"Variant {variant_id} does not belong to product {product_id}.",
                code="INVALID_VARIANT",
            )


async def create_plan_item(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    plan_id: str,
    data: dict,
) -> dict:
    await _require_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    await _validate_item_refs(
        conn,
        tenant_id=tenant_id,
        product_id=data["product_id"],
        variant_id=data.get("variant_id"),
    )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.create_plan_item(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        plan_id=plan_id,
        data=data,
    )
    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.plan_items.created",
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
                "entity_kind": "subscriptions.plan_item",
                "plan_id": plan_id,
                "product_id": data["product_id"],
                "variant_id": data.get("variant_id"),
            },
        },
    )
    return row


async def update_plan_item(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    plan_id: str,
    item_id: str,
    patch: dict,
) -> dict:
    await _require_plan(conn, tenant_id=tenant_id, plan_id=plan_id)
    if patch.get("product_id") is not None:
        # If product changed and variant present, re-validate compat.
        await _validate_item_refs(
            conn,
            tenant_id=tenant_id,
            product_id=patch["product_id"],
            variant_id=patch.get("variant_id"),
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row = await _repo.update_plan_item(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        plan_id=plan_id,
        item_id=item_id,
        patch=patch,
    )
    if row is None:
        raise _errors.NotFoundError(f"Plan item {item_id} not found.")
    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.plan_items.updated",
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
                "entity_id": str(item_id),
                "entity_kind": "subscriptions.plan_item",
                "plan_id": plan_id,
                "changed_fields": sorted(
                    [k for k, v in patch.items() if v is not None],
                ),
            },
        },
    )
    return row


async def soft_delete_plan_item(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    plan_id: str,
    item_id: str,
) -> None:
    await _require_plan(conn, tenant_id=tenant_id, plan_id=plan_id)

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_plan_item(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        plan_id=plan_id,
        item_id=item_id,
    )
    if not ok:
        raise _errors.NotFoundError(f"Plan item {item_id} not found.")
    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.plan_items.deleted",
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
                "entity_id": str(item_id),
                "entity_kind": "subscriptions.plan_item",
                "plan_id": plan_id,
            },
        },
    )


# ── Subscriptions ─────────────────────────────────────────────────────

async def list_subscriptions(conn: Any, **kwargs: Any) -> list[dict]:
    return await _repo.list_subscriptions(conn, **kwargs)


async def get_subscription(
    conn: Any, *, tenant_id: str, subscription_id: str,
) -> dict:
    row = await _repo.get_subscription(
        conn, tenant_id=tenant_id, subscription_id=subscription_id,
    )
    if row is None:
        raise _errors.NotFoundError(
            f"Subscription {subscription_id} not found.",
        )
    return row


async def create_subscription(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    data: dict,
) -> dict:
    if not await _repo.customer_exists(
        conn, tenant_id=tenant_id, customer_id=data["customer_id"],
    ):
        raise _errors.ValidationError(
            f"Customer {data['customer_id']} not found for this tenant.",
            code="INVALID_CUSTOMER",
        )
    plan = await _repo.get_plan(
        conn, tenant_id=tenant_id, plan_id=data["plan_id"],
    )
    if plan is None:
        raise _errors.ValidationError(
            f"Plan {data['plan_id']} not found for this tenant.",
            code="INVALID_PLAN",
        )
    if plan["status"] != "active":
        raise _errors.ValidationError(
            f"Plan {data['plan_id']} is not active (status={plan['status']}).",
            code="PLAN_NOT_ACTIVE",
        )
    if data.get("service_zone_id"):
        if not await _repo.service_zone_exists(
            conn,
            tenant_id=tenant_id,
            service_zone_id=data["service_zone_id"],
        ):
            raise _errors.ValidationError(
                f"Service zone {data['service_zone_id']} not found for this tenant.",
                code="INVALID_SERVICE_ZONE",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row, event_id = await _repo.create_subscription(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        data=data,
    )

    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.subscriptions.created",
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
                "entity_kind": "subscriptions.subscription",
                "customer_id": data["customer_id"],
                "plan_id": data["plan_id"],
                "service_zone_id": data.get("service_zone_id"),
                "start_date": str(data["start_date"]),
                "billing_cycle": data.get("billing_cycle"),
            },
        },
    )
    # Companion event audit.
    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.events.logged",
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
                "entity_id": str(event_id),
                "entity_kind": "subscriptions.event",
                "subscription_id": str(row.get("id")),
                "event_type": "started",
            },
        },
    )
    return row


async def update_subscription(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    subscription_id: str,
    patch: dict,
) -> dict:
    existing = await _repo.get_subscription(
        conn, tenant_id=tenant_id, subscription_id=subscription_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Subscription {subscription_id} not found.",
        )

    # Block mutations on terminal states.
    if existing["status"] in ("cancelled", "ended") and patch.get("status") is None:
        raise _errors.ValidationError(
            f"Cannot edit subscription in terminal status={existing['status']}.",
            code="TERMINAL_STATE",
        )

    if patch.get("service_zone_id") is not None:
        if not await _repo.service_zone_exists(
            conn,
            tenant_id=tenant_id,
            service_zone_id=patch["service_zone_id"],
        ):
            raise _errors.ValidationError(
                f"Service zone {patch['service_zone_id']} not found for this tenant.",
                code="INVALID_SERVICE_ZONE",
            )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    row, event_type = await _repo.patch_subscription(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        existing=existing,
        patch=patch,
    )

    event_key_map = {
        "paused":    "somaerp.subscriptions.subscriptions.paused",
        "resumed":   "somaerp.subscriptions.subscriptions.resumed",
        "cancelled": "somaerp.subscriptions.subscriptions.cancelled",
        "ended":     "somaerp.subscriptions.subscriptions.ended",
    }
    audit_key = (
        event_key_map[event_type]
        if event_type is not None
        else "somaerp.subscriptions.subscriptions.updated"
    )
    metadata: dict[str, Any] = {
        "category": "setup" if is_setup else "operational",
        "entity_id": str(subscription_id),
        "entity_kind": "subscriptions.subscription",
        "changed_fields": sorted(
            [k for k, v in patch.items() if v is not None],
        ),
    }
    if event_type is not None:
        metadata["previous_status"] = existing["status"]
        metadata["new_status"] = patch.get("status")
        if patch.get("reason"):
            metadata["reason"] = patch["reason"]

    await tennetctl.audit_emit(
        event_key=audit_key,
        scope=_scope(
            actor_user_id=actor_user_id,
            session_id=session_id,
            org_id=org_id,
            tenant_id=tenant_id,
        ),
        payload={"outcome": "success", "metadata": metadata},
    )
    if event_type is not None:
        await tennetctl.audit_emit(
            event_key="somaerp.subscriptions.events.logged",
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
                    "entity_kind": "subscriptions.event",
                    "subscription_id": str(subscription_id),
                    "event_type": event_type,
                },
            },
        )
    return row


async def soft_delete_subscription(
    conn: Any,
    *,
    tennetctl: Any,
    tenant_id: str,
    actor_user_id: str | None,
    org_id: str | None,
    session_id: str | None,
    subscription_id: str,
) -> None:
    existing = await _repo.get_subscription(
        conn, tenant_id=tenant_id, subscription_id=subscription_id,
    )
    if existing is None:
        raise _errors.NotFoundError(
            f"Subscription {subscription_id} not found.",
        )
    if existing["status"] == "active":
        raise _errors.ValidationError(
            "Cannot delete an active subscription. Cancel it first.",
            code="INVALID_DELETE_STATE",
        )

    is_setup = actor_user_id is None
    effective_user = actor_user_id or "00000000-0000-0000-0000-000000000000"

    ok = await _repo.soft_delete_subscription(
        conn,
        tenant_id=tenant_id,
        actor_user_id=effective_user,
        subscription_id=subscription_id,
    )
    if not ok:
        raise _errors.NotFoundError(
            f"Subscription {subscription_id} not found.",
        )
    await tennetctl.audit_emit(
        event_key="somaerp.subscriptions.subscriptions.deleted",
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
                "entity_id": str(subscription_id),
                "entity_kind": "subscriptions.subscription",
            },
        },
    )


# ── Events ────────────────────────────────────────────────────────────

async def list_subscription_events(
    conn: Any, *, tenant_id: str, subscription_id: str,
) -> list[dict]:
    # Existence check (cross-tenant 404).
    exists = await _repo.get_subscription(
        conn, tenant_id=tenant_id, subscription_id=subscription_id,
    )
    if exists is None:
        raise _errors.NotFoundError(
            f"Subscription {subscription_id} not found.",
        )
    return await _repo.list_subscription_events(
        conn, tenant_id=tenant_id, subscription_id=subscription_id,
    )
