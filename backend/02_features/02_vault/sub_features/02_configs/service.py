"""
vault.configs — service layer.

Business rules:
  - (scope, org_id, workspace_id, key) must be unique at the live level.
  - value_type + scope + key are immutable after create.
  - Description is optional; provided string → upserted dtl_attrs row; omitted
    on update → unchanged; explicit empty string → deleted.

Audit fires on every create / update / delete.
"""

from __future__ import annotations

import asyncpg
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.repository"
)
_schemas: Any = import_module(
    "backend.02_features.02_vault.sub_features.02_configs.schemas"
)

_AUDIT_NODE_KEY = "audit.events.emit"


async def _emit_audit(
    pool: Any,
    ctx: Any,
    *,
    event_key: str,
    metadata: dict,
    outcome: str = "success",
) -> None:
    await _catalog.run_node(
        pool,
        _AUDIT_NODE_KEY,
        ctx,
        {"event_key": event_key, "outcome": outcome, "metadata": metadata},
    )


async def create_config(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    key: str,
    value_type: str,
    value: Any,
    description: str | None,
    scope: str = "global",
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> dict:
    existing = await _repo.get_by_scope_key(
        conn, scope=scope, org_id=org_id, workspace_id=workspace_id, key=key,
    )
    if existing is not None:
        raise _errors.ConflictError(
            f"vault config {key!r} already exists at scope={scope!r}"
        )

    config_id = _core_id.uuid7()
    created_by = ctx.user_id or "sys"

    try:
        await _repo.insert_config(
            conn,
            id=config_id,
            key=key,
            value_type=value_type,
            value=value,
            scope=scope,
            org_id=org_id,
            workspace_id=workspace_id,
            created_by=created_by,
        )
    except asyncpg.UniqueViolationError as e:
        raise _errors.ConflictError(
            f"vault config {key!r} already exists at scope={scope!r}"
        ) from e

    if description:
        attr_id = _core_id.uuid7()
        await _repo.set_description(
            conn, config_id=config_id, description=description, attr_row_id=attr_id,
        )

    await _emit_audit(
        pool, ctx,
        event_key="vault.configs.created",
        metadata={
            "key": key, "value_type": value_type,
            "scope": scope, "org_id": org_id, "workspace_id": workspace_id,
        },
    )

    created = await _repo.get_by_id(conn, config_id)
    if created is None:
        raise RuntimeError(
            f"vault config {key!r} not visible after insert — tx isolation issue?"
        )
    return created


async def list_configs(
    conn: Any,
    _ctx: Any,
    *,
    limit: int = 50,
    offset: int = 0,
    scope: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> tuple[list[dict], int]:
    return await _repo.list_configs(
        conn, limit=limit, offset=offset,
        scope=scope, org_id=org_id, workspace_id=workspace_id,
    )


async def get_config(
    conn: Any,
    _ctx: Any,
    *,
    config_id: str,
) -> dict | None:
    return await _repo.get_by_id(conn, config_id)


async def update_config(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    config_id: str,
    value: Any = None,
    description: str | None = None,
    is_active: bool | None = None,
    has_value: bool = False,
    has_description: bool = False,
    has_is_active: bool = False,
) -> dict:
    current = await _repo.get_by_id(conn, config_id)
    if current is None or current.get("deleted_at") is not None:
        raise _errors.NotFoundError(f"vault config {config_id!r} not found")

    # Type-check the value against the declared value_type.
    if has_value:
        try:
            _schemas._validate_value_matches_type(value, current["value_type"])
        except ValueError as e:
            raise _errors.ValidationError(str(e)) from e

    changed: dict[str, Any] = {}

    if has_value or has_is_active:
        ok = await _repo.update_config(
            conn,
            id=config_id,
            value=value,
            is_active=is_active,
            updated_by=(ctx.user_id or "sys"),
            has_value=has_value,
            has_is_active=has_is_active,
        )
        if not ok:
            raise _errors.NotFoundError(f"vault config {config_id!r} not found")
        if has_value:
            changed["value"] = True
        if has_is_active:
            changed["is_active"] = is_active

    if has_description:
        if description:
            attr_id = _core_id.uuid7()
            await _repo.set_description(
                conn, config_id=config_id, description=description, attr_row_id=attr_id,
            )
        else:
            await _repo.clear_description(conn, config_id=config_id)
        changed["description"] = True

    if not changed:
        return current

    await _emit_audit(
        pool, ctx,
        event_key="vault.configs.updated",
        metadata={
            "key": current["key"], "scope": current["scope"],
            "org_id": current["org_id"], "workspace_id": current["workspace_id"],
            "changed": sorted(changed.keys()),
        },
    )

    updated = await _repo.get_by_id(conn, config_id)
    if updated is None:
        raise RuntimeError(f"vault config {config_id!r} vanished after update")
    return updated


async def delete_config(
    pool: Any,
    conn: Any,
    ctx: Any,
    *,
    config_id: str,
) -> None:
    current = await _repo.get_by_id(conn, config_id)
    if current is None or current.get("deleted_at") is not None:
        raise _errors.NotFoundError(f"vault config {config_id!r} not found")

    ok = await _repo.soft_delete(
        conn, id=config_id, updated_by=(ctx.user_id or "sys"),
    )
    if not ok:
        raise _errors.NotFoundError(f"vault config {config_id!r} not found")

    await _emit_audit(
        pool, ctx,
        event_key="vault.configs.deleted",
        metadata={
            "key": current["key"], "scope": current["scope"],
            "org_id": current["org_id"], "workspace_id": current["workspace_id"],
        },
    )
