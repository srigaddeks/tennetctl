"""featureflags.rules — service layer."""
from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.03_rules.repository"
)

_AUDIT = "audit.events.emit"
_SENTINEL = object()


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def _assert_flag(pool: Any, ctx: Any, flag_id: str) -> dict:
    result = await _catalog.run_node(
        pool, "featureflags.flags.get", ctx, {"id": flag_id},
    )
    flag = result.get("flag")
    if flag is None:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")
    return flag


async def create_rule(
    pool: Any, conn: Any, ctx: Any, *,
    flag_id: str,
    environment: str,
    priority: int,
    conditions: dict,
    value: Any,
    rollout_percentage: int = 100,
) -> dict:
    await _assert_flag(pool, ctx, flag_id)
    env_id = await _repo.get_env_id(conn, environment)
    if env_id is None:
        raise _errors.ValidationError(f"unknown environment {environment!r}")

    rule_id = _core_id.uuid7()
    await _repo.insert_rule(
        conn,
        id=rule_id, flag_id=flag_id, environment_id=env_id,
        priority=priority, conditions=conditions, value=value,
        rollout_percentage=rollout_percentage,
        created_by=(ctx.user_id or "sys"),
    )
    await _emit(
        pool, ctx,
        event_key="featureflags.rules.created",
        metadata={
            "rule_id": rule_id, "flag_id": flag_id,
            "environment": environment, "priority": priority,
        },
    )
    created = await _repo.get_by_id(conn, rule_id)
    if created is None:
        raise RuntimeError(f"rule {rule_id} not visible after insert")
    return created


async def get_rule(conn: Any, _ctx: Any, *, rule_id: str) -> dict | None:
    return await _repo.get_by_id(conn, rule_id)


async def list_rules(
    conn: Any, _ctx: Any, *,
    limit: int = 100, offset: int = 0,
    flag_id: str | None = None,
    environment: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_rules(
        conn, limit=limit, offset=offset,
        flag_id=flag_id, environment=environment, is_active=is_active,
    )


async def update_rule(
    pool: Any, conn: Any, ctx: Any, *,
    rule_id: str,
    priority: Any = _SENTINEL,
    conditions: Any = _SENTINEL,
    value: Any = _SENTINEL,
    rollout_percentage: Any = _SENTINEL,
    is_active: Any = _SENTINEL,
) -> dict:
    current = await _repo.get_by_id(conn, rule_id)
    if current is None:
        raise _errors.NotFoundError(f"Rule {rule_id!r} not found.")

    kw: dict[str, Any] = {"id": rule_id, "updated_by": ctx.user_id or "sys"}
    changed: dict[str, Any] = {}
    for k, v in (
        ("priority", priority), ("conditions", conditions), ("value", value),
        ("rollout_percentage", rollout_percentage), ("is_active", is_active),
    ):
        if v is not _SENTINEL and v != current.get(k):
            kw[k] = v
            changed[k] = v

    if not changed:
        return current

    await _repo.update_rule_fields(conn, **kw)
    await _emit(
        pool, ctx,
        event_key="featureflags.rules.updated",
        metadata={"rule_id": rule_id, "changed": sorted(changed.keys())},
    )
    updated = await _repo.get_by_id(conn, rule_id)
    if updated is None:
        raise RuntimeError(f"rule {rule_id} vanished after update")
    return updated


async def delete_rule(pool: Any, conn: Any, ctx: Any, *, rule_id: str) -> None:
    ok = await _repo.soft_delete_rule(
        conn, id=rule_id, updated_by=(ctx.user_id or "sys"),
    )
    if not ok:
        raise _errors.NotFoundError(f"Rule {rule_id!r} not found.")
    await _emit(
        pool, ctx,
        event_key="featureflags.rules.deleted",
        metadata={"rule_id": rule_id},
    )
