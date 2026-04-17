"""Service layer for notify.template_groups."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module("backend.02_features.06_notify.sub_features.02_template_groups.repository")
_core_id: Any = import_module("backend.01_core.id")
_catalog: Any = import_module("backend.01_catalog")


async def list_template_groups(conn: Any, *, org_id: str) -> list[dict]:
    return await _repo.list_template_groups(conn, org_id=org_id)


async def get_template_group(conn: Any, *, group_id: str) -> dict | None:
    return await _repo.get_template_group(conn, group_id=group_id)


async def create_template_group(conn: Any, pool: Any, ctx: Any, *, data: dict) -> dict:
    group_id = _core_id.uuid7()
    row = await _repo.create_template_group(
        conn,
        group_id=group_id,
        org_id=data["org_id"],
        key=data["key"],
        label=data["label"],
        category_id=data["category_id"],
        smtp_config_id=data.get("smtp_config_id"),
        created_by=ctx.user_id or "system",
    )
    await _catalog.run_node(
        pool, "audit.events.emit", ctx,
        {"event_key": "notify.template_groups.created", "outcome": "success",
         "metadata": {"group_id": group_id, "key": data["key"]}},
    )
    return row


async def update_template_group(conn: Any, pool: Any, ctx: Any, *, group_id: str, data: dict) -> dict | None:
    row = await _repo.update_template_group(
        conn, group_id=group_id, updated_by=ctx.user_id or "system", **data,
    )
    if row:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "notify.template_groups.updated", "outcome": "success",
             "metadata": {"group_id": group_id}},
        )
    return row


async def delete_template_group(conn: Any, pool: Any, ctx: Any, *, group_id: str) -> bool:
    deleted = await _repo.delete_template_group(conn, group_id=group_id, updated_by=ctx.user_id or "system")
    if deleted:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "notify.template_groups.deleted", "outcome": "success",
             "metadata": {"group_id": group_id}},
        )
    return deleted
