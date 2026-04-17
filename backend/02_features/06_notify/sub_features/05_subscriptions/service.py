"""Service layer for notify.subscriptions."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.05_subscriptions.repository"
)
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")
_errors: Any = import_module("backend.01_core.errors")


def matches_pattern(event_key: str, pattern: str) -> bool:
    """
    Match event_key against a subscription pattern.

    Rules:
      - "*"         → matches everything
      - exact       → "iam.users.created" matches only "iam.users.created"
      - suffix ".*" → "iam.users.*" matches "iam.users.created", "iam.users.updated", etc.
                      and also "iam.users.X.Y" (deep match on prefix)
    """
    if pattern == "*":
        return True
    if pattern == event_key:
        return True
    if pattern.endswith(".*"):
        prefix = pattern[:-2]  # strip trailing ".*"
        return event_key.startswith(prefix + ".")
    return False


async def list_subscriptions(
    conn: Any, *, org_id: str, include_inactive: bool = False
) -> list[dict]:
    return await _repo.list_subscriptions(
        conn, org_id=org_id, include_inactive=include_inactive
    )


async def get_subscription(conn: Any, *, sub_id: str) -> dict | None:
    return await _repo.get_subscription(conn, sub_id)


async def create_subscription(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    data: dict,
) -> dict:
    sub_id = _core_id.uuid7()
    row = await _repo.create_subscription(
        conn,
        sub_id=sub_id,
        org_id=data["org_id"],
        name=data["name"],
        event_key_pattern=data["event_key_pattern"],
        template_id=data["template_id"],
        channel_id=data["channel_id"],
        created_by=ctx.user_id or "system",
    )
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {
            "event_key": "notify.subscriptions.created",
            "outcome": "success",
            "metadata": {
                "sub_id": sub_id,
                "org_id": data["org_id"],
                "event_key_pattern": data["event_key_pattern"],
            },
        },
    )
    return row


async def update_subscription(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    sub_id: str,
    data: dict,
) -> dict | None:
    row = await _repo.update_subscription(
        conn, sub_id=sub_id, updated_by=ctx.user_id or "system", **data
    )
    if row:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "notify.subscriptions.updated",
                "outcome": "success",
                "metadata": {"sub_id": sub_id},
            },
        )
    return row


async def delete_subscription(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    sub_id: str,
) -> bool:
    deleted = await _repo.delete_subscription(
        conn, sub_id=sub_id, updated_by=ctx.user_id or "system"
    )
    if deleted:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {
                "event_key": "notify.subscriptions.deleted",
                "outcome": "success",
                "metadata": {"sub_id": sub_id},
            },
        )
    return deleted


async def list_active_for_worker(conn: Any) -> list[dict]:
    """All active subscriptions for the worker's matching loop."""
    return await _repo.list_active_subscriptions_all(conn)
