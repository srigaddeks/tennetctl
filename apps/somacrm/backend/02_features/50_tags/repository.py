"""Tags repository — raw asyncpg against schema "12_somacrm"."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_id = import_module("apps.somacrm.backend.01_core.id")

SCHEMA = '"12_somacrm"'
TAG_TABLE = f'{SCHEMA}."fct_tags"'
TAG_VIEW = f'{SCHEMA}.v_tags'
LNK_TABLE = f'{SCHEMA}."lnk_entity_tags"'


async def list_tags(conn: Any, *, tenant_id: str, limit: int = 200, offset: int = 0) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {TAG_VIEW} WHERE tenant_id = $1 AND deleted_at IS NULL "
        f"ORDER BY name ASC LIMIT $2 OFFSET $3",
        tenant_id, limit, offset,
    )
    return [dict(r) for r in rows]


async def create_tag(conn: Any, *, tenant_id: str, actor_user_id: str, data: dict) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {TAG_TABLE} (id, tenant_id, name, color, created_by, updated_by) "
        "VALUES ($1,$2,$3,$4,$5,$5)",
        new_id, tenant_id, data["name"], data.get("color", "#6366f1"), actor_user_id,
    )
    row = await conn.fetchrow(f"SELECT * FROM {TAG_VIEW} WHERE id = $1", new_id)
    return dict(row) if row else {}


async def soft_delete_tag(conn: Any, *, tenant_id: str, actor_user_id: str, tag_id: str) -> bool:
    result = await conn.execute(
        f"UPDATE {TAG_TABLE} "
        "SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP, updated_by = $1 "
        "WHERE id = $2 AND tenant_id = $3 AND deleted_at IS NULL",
        actor_user_id, tag_id, tenant_id,
    )
    return result.endswith(" 1")


async def list_entity_tags(conn: Any, *, tenant_id: str, entity_type: str, entity_id: str) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {LNK_TABLE} WHERE tenant_id = $1 AND entity_type = $2 AND entity_id = $3",
        tenant_id, entity_type, entity_id,
    )
    return [dict(r) for r in rows]


async def create_entity_tag(conn: Any, *, tenant_id: str, actor_user_id: str, data: dict) -> dict:
    new_id = _id.uuid7()
    await conn.execute(
        f"INSERT INTO {LNK_TABLE} (id, tenant_id, entity_type, entity_id, tag_id, created_by) "
        "VALUES ($1,$2,$3,$4,$5,$6) ON CONFLICT DO NOTHING",
        new_id, tenant_id, data["entity_type"], data["entity_id"], data["tag_id"], actor_user_id,
    )
    row = await conn.fetchrow(
        f"SELECT * FROM {LNK_TABLE} WHERE tenant_id=$1 AND entity_type=$2 AND entity_id=$3 AND tag_id=$4",
        tenant_id, data["entity_type"], data["entity_id"], data["tag_id"],
    )
    return dict(row) if row else {}


async def delete_entity_tag(conn: Any, *, tenant_id: str, entity_tag_id: str) -> bool:
    result = await conn.execute(
        f"DELETE FROM {LNK_TABLE} WHERE id = $1 AND tenant_id = $2",
        entity_tag_id, tenant_id,
    )
    return result.endswith(" 1")
