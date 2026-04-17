"""Service layer for notify.smtp_configs."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module("backend.02_features.06_notify.sub_features.01_smtp_configs.repository")
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")


async def list_smtp_configs(conn: Any, *, org_id: str) -> list[dict]:
    return await _repo.list_smtp_configs(conn, org_id=org_id)


async def get_smtp_config(conn: Any, *, config_id: str) -> dict | None:
    return await _repo.get_smtp_config(conn, config_id=config_id)


async def create_smtp_config(conn: Any, pool: Any, ctx: Any, *, data: dict) -> dict:
    config_id = _core_id.uuid7()
    row = await _repo.create_smtp_config(
        conn,
        config_id=config_id,
        org_id=data["org_id"],
        key=data["key"],
        label=data["label"],
        host=data["host"],
        port=data["port"],
        tls=data["tls"],
        username=data["username"],
        auth_vault_key=data["auth_vault_key"],
        created_by=ctx.user_id or "system",
    )
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": "notify.smtp_configs.created", "outcome": "success",
         "metadata": {"config_id": config_id, "key": data["key"]}},
    )
    return row


async def update_smtp_config(conn: Any, pool: Any, ctx: Any, *, config_id: str, data: dict) -> dict | None:
    row = await _repo.update_smtp_config(
        conn, config_id=config_id, updated_by=ctx.user_id or "system", **data,
    )
    if row:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "notify.smtp_configs.updated", "outcome": "success",
             "metadata": {"config_id": config_id}},
        )
    return row


async def delete_smtp_config(conn: Any, pool: Any, ctx: Any, *, config_id: str) -> bool:
    deleted = await _repo.delete_smtp_config(conn, config_id=config_id, updated_by=ctx.user_id or "system")
    if deleted:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "notify.smtp_configs.deleted", "outcome": "success",
             "metadata": {"config_id": config_id}},
        )
    return deleted
