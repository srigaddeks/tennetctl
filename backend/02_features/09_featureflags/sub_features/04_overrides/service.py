"""featureflags.overrides — service layer."""
from __future__ import annotations

from importlib import import_module
from typing import Any

import asyncpg

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.04_overrides.repository"
)

_AUDIT = "audit.events.emit"
_SENTINEL = object()


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    await _catalog.run_node(
        pool, _AUDIT, ctx,
        {"event_key": event_key, "outcome": "success", "metadata": metadata},
    )


async def _assert_flag(pool: Any, ctx: Any, flag_id: str) -> None:
    result = await _catalog.run_node(
        pool, "featureflags.flags.get", ctx, {"id": flag_id},
    )
    if result.get("flag") is None:
        raise _errors.NotFoundError(f"Flag {flag_id!r} not found.")


async def create_override(
    pool: Any, conn: Any, ctx: Any, *,
    flag_id: str,
    environment: str,
    entity_type: str,
    entity_id: str,
    value: Any,
    reason: str | None = None,
) -> dict:
    await _assert_flag(pool, ctx, flag_id)

    env_id = await _repo.get_env_id(conn, environment)
    if env_id is None:
        raise _errors.ValidationError(f"unknown environment {environment!r}")
    et_id = await _repo.get_entity_type_id(conn, entity_type)
    if et_id is None:
        raise _errors.ValidationError(f"unknown entity_type {entity_type!r}")

    existing = await _repo.get_by_key(
        conn, flag_id=flag_id, environment_id=env_id,
        entity_type_id=et_id, entity_id=entity_id,
    )
    if existing is not None:
        raise _errors.ConflictError(
            f"override already exists for (flag, env, {entity_type}, {entity_id})"
        )

    override_id = _core_id.uuid7()
    try:
        await _repo.insert_override(
            conn,
            id=override_id, flag_id=flag_id, environment_id=env_id,
            entity_type_id=et_id, entity_id=entity_id,
            value=value, reason=reason,
            created_by=(ctx.user_id or "sys"),
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError("override already exists for this key") from e

    await _emit(
        pool, ctx,
        event_key="featureflags.overrides.created",
        metadata={
            "override_id": override_id, "flag_id": flag_id,
            "environment": environment, "entity_type": entity_type,
            "entity_id": entity_id,
        },
    )
    created = await _repo.get_by_id(conn, override_id)
    if created is None:
        raise RuntimeError(f"override {override_id} not visible after insert")
    return created


async def get_override(conn: Any, _ctx: Any, *, override_id: str) -> dict | None:
    return await _repo.get_by_id(conn, override_id)


async def list_overrides(
    conn: Any, _ctx: Any, *,
    limit: int = 100, offset: int = 0,
    flag_id: str | None = None,
    environment: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_overrides(
        conn, limit=limit, offset=offset,
        flag_id=flag_id, environment=environment,
        entity_type=entity_type, entity_id=entity_id,
        is_active=is_active,
    )


async def update_override(
    pool: Any, conn: Any, ctx: Any, *,
    override_id: str,
    value: Any = _SENTINEL,
    reason: Any = _SENTINEL,
    is_active: Any = _SENTINEL,
) -> dict:
    current = await _repo.get_by_id(conn, override_id)
    if current is None:
        raise _errors.NotFoundError(f"Override {override_id!r} not found.")

    kw: dict[str, Any] = {"id": override_id, "updated_by": ctx.user_id or "sys"}
    changed: dict[str, Any] = {}
    for k, v in (("value", value), ("reason", reason), ("is_active", is_active)):
        if v is not _SENTINEL and v != current.get(k):
            kw[k] = v
            changed[k] = v

    if not changed:
        return current

    await _repo.update_override_fields(conn, **kw)
    await _emit(
        pool, ctx,
        event_key="featureflags.overrides.updated",
        metadata={"override_id": override_id, "changed": sorted(changed.keys())},
    )
    updated = await _repo.get_by_id(conn, override_id)
    if updated is None:
        raise RuntimeError(f"override {override_id} vanished after update")
    return updated


async def delete_override(pool: Any, conn: Any, ctx: Any, *, override_id: str) -> None:
    ok = await _repo.soft_delete_override(
        conn, id=override_id, updated_by=(ctx.user_id or "sys"),
    )
    if not ok:
        raise _errors.NotFoundError(f"Override {override_id!r} not found.")
    await _emit(
        pool, ctx,
        event_key="featureflags.overrides.deleted",
        metadata={"override_id": override_id},
    )
