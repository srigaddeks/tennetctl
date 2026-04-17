"""Repository for monitoring.saved_queries — raw SQL against fct/view."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_SELECT = """
    SELECT id, org_id, owner_user_id, name, description, target, dsl,
           shared, is_active, deleted_at, created_at, updated_at
    FROM "05_monitoring"."v_monitoring_saved_queries"
"""


async def insert(
    conn: Any,
    *,
    id: str,
    org_id: str,
    owner_user_id: str,
    name: str,
    description: str | None,
    target: str,
    dsl: dict[str, Any],
    shared: bool,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_saved_queries"
            (id, org_id, owner_user_id, name, description, target, dsl,
             shared, is_active, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,TRUE,$9,$9)
        """,
        id, org_id, owner_user_id, name, description, target, dsl, shared, now,
    )
    row = await get_by_id(conn, id=id)
    assert row is not None
    return row


async def get_by_id(conn: Any, *, id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        _SELECT + " WHERE id = $1 AND deleted_at IS NULL",
        id,
    )
    return dict(row) if row else None


async def list_for_user(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    target: str | None = None,
) -> list[dict[str, Any]]:
    sql = _SELECT + """
        WHERE org_id = $1
          AND deleted_at IS NULL
          AND (owner_user_id = $2 OR shared = TRUE)
    """
    params: list[Any] = [org_id, user_id]
    if target is not None:
        sql += " AND target = $3"
        params.append(target)
    sql += " ORDER BY updated_at DESC"
    rows = await conn.fetch(sql, *params)
    return [dict(r) for r in rows]


async def update(
    conn: Any,
    *,
    id: str,
    name: str | None,
    description: str | None,
    dsl: dict[str, Any] | None,
    shared: bool | None,
    is_active: bool | None,
) -> dict[str, Any] | None:
    sets: list[str] = []
    params: list[Any] = []

    def _add(col: str, val: Any) -> None:
        params.append(val)
        sets.append(f"{col} = ${len(params)}")

    if name is not None:
        _add("name", name)
    if description is not None:
        _add("description", description)
    if dsl is not None:
        _add("dsl", dsl)
    if shared is not None:
        _add("shared", shared)
    if is_active is not None:
        _add("is_active", is_active)

    if not sets:
        return await get_by_id(conn, id=id)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    params.append(now)
    sets.append(f"updated_at = ${len(params)}")
    params.append(id)
    sql = f"""
        UPDATE "05_monitoring"."10_fct_monitoring_saved_queries"
           SET {", ".join(sets)}
         WHERE id = ${len(params)} AND deleted_at IS NULL
    """
    await conn.execute(sql, *params)
    return await get_by_id(conn, id=id)


async def soft_delete(conn: Any, *, id: str) -> bool:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await conn.execute(
        """
        UPDATE "05_monitoring"."10_fct_monitoring_saved_queries"
           SET deleted_at = $1, updated_at = $1
         WHERE id = $2 AND deleted_at IS NULL
        """,
        now, id,
    )
    # result like "UPDATE 1"
    try:
        count = int(result.split()[-1])
    except Exception:  # noqa: BLE001
        count = 0
    return count > 0
