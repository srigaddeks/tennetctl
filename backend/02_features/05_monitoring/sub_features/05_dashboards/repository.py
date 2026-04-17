"""Repository for monitoring.dashboards — raw SQL against fct/view."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


_DASH_SELECT = """
    SELECT id, org_id, owner_user_id, name, description, layout,
           shared, is_active, panel_count, created_at, updated_at
    FROM "05_monitoring"."v_monitoring_dashboards"
"""

_PANEL_SELECT = """
    SELECT id, dashboard_id, title, panel_type, dsl, grid_pos, display_opts,
           created_at, updated_at
    FROM "05_monitoring"."v_monitoring_panels"
"""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---------- dashboards ----------

async def insert_dashboard(
    conn: Any,
    *,
    id: str,
    org_id: str,
    owner_user_id: str,
    name: str,
    description: str | None,
    layout: dict[str, Any],
    shared: bool,
) -> dict[str, Any]:
    now = _utcnow()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."10_fct_monitoring_dashboards"
            (id, org_id, owner_user_id, name, description, layout,
             shared, is_active, created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,TRUE,$8,$8)
        """,
        id, org_id, owner_user_id, name, description, layout, shared, now,
    )
    row = await get_dashboard_by_id(conn, id=id)
    assert row is not None
    return row


async def get_dashboard_by_id(conn: Any, *, id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(_DASH_SELECT + " WHERE id = $1", id)
    return dict(row) if row else None


async def list_dashboards(
    conn: Any,
    *,
    org_id: str,
    owner_user_id: str,
    include_shared: bool = True,
) -> list[dict[str, Any]]:
    if include_shared:
        sql = _DASH_SELECT + """
            WHERE org_id = $1
              AND (owner_user_id = $2 OR shared = TRUE)
            ORDER BY updated_at DESC
        """
        rows = await conn.fetch(sql, org_id, owner_user_id)
    else:
        sql = _DASH_SELECT + """
            WHERE org_id = $1 AND owner_user_id = $2
            ORDER BY updated_at DESC
        """
        rows = await conn.fetch(sql, org_id, owner_user_id)
    return [dict(r) for r in rows]


async def update_dashboard(
    conn: Any,
    *,
    id: str,
    name: str | None,
    description: str | None,
    layout: dict[str, Any] | None,
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
    if layout is not None:
        _add("layout", layout)
    if shared is not None:
        _add("shared", shared)
    if is_active is not None:
        _add("is_active", is_active)

    if not sets:
        return await get_dashboard_by_id(conn, id=id)

    now = _utcnow()
    params.append(now)
    sets.append(f"updated_at = ${len(params)}")
    params.append(id)
    sql = f"""
        UPDATE "05_monitoring"."10_fct_monitoring_dashboards"
           SET {", ".join(sets)}
         WHERE id = ${len(params)} AND deleted_at IS NULL
    """
    await conn.execute(sql, *params)
    return await get_dashboard_by_id(conn, id=id)


async def soft_delete_dashboard(conn: Any, *, id: str) -> bool:
    now = _utcnow()
    result = await conn.execute(
        """
        UPDATE "05_monitoring"."10_fct_monitoring_dashboards"
           SET deleted_at = $1, updated_at = $1
         WHERE id = $2 AND deleted_at IS NULL
        """,
        now, id,
    )
    try:
        count = int(result.split()[-1])
    except Exception:  # noqa: BLE001
        count = 0
    return count > 0


# ---------- panels ----------

async def insert_panel(
    conn: Any,
    *,
    id: str,
    dashboard_id: str,
    title: str,
    panel_type: str,
    dsl: dict[str, Any],
    grid_pos: dict[str, Any],
    display_opts: dict[str, Any],
) -> dict[str, Any]:
    now = _utcnow()
    await conn.execute(
        """
        INSERT INTO "05_monitoring"."11_fct_monitoring_panels"
            (id, dashboard_id, title, panel_type, dsl, grid_pos, display_opts,
             created_at, updated_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$8)
        """,
        id, dashboard_id, title, panel_type, dsl, grid_pos, display_opts, now,
    )
    row = await get_panel_by_id(conn, id=id)
    assert row is not None
    return row


async def get_panel_by_id(conn: Any, *, id: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(_PANEL_SELECT + " WHERE id = $1", id)
    return dict(row) if row else None


async def list_panels_for_dashboard(
    conn: Any, *, dashboard_id: str,
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        _PANEL_SELECT + " WHERE dashboard_id = $1 ORDER BY created_at ASC",
        dashboard_id,
    )
    return [dict(r) for r in rows]


async def update_panel(
    conn: Any,
    *,
    id: str,
    title: str | None,
    panel_type: str | None,
    dsl: dict[str, Any] | None,
    grid_pos: dict[str, Any] | None,
    display_opts: dict[str, Any] | None,
) -> dict[str, Any] | None:
    sets: list[str] = []
    params: list[Any] = []

    def _add(col: str, val: Any) -> None:
        params.append(val)
        sets.append(f"{col} = ${len(params)}")

    if title is not None:
        _add("title", title)
    if panel_type is not None:
        _add("panel_type", panel_type)
    if dsl is not None:
        _add("dsl", dsl)
    if grid_pos is not None:
        _add("grid_pos", grid_pos)
    if display_opts is not None:
        _add("display_opts", display_opts)

    if not sets:
        return await get_panel_by_id(conn, id=id)

    now = _utcnow()
    params.append(now)
    sets.append(f"updated_at = ${len(params)}")
    params.append(id)
    sql = f"""
        UPDATE "05_monitoring"."11_fct_monitoring_panels"
           SET {", ".join(sets)}
         WHERE id = ${len(params)}
    """
    await conn.execute(sql, *params)
    return await get_panel_by_id(conn, id=id)


async def delete_panel(conn: Any, *, id: str) -> bool:
    result = await conn.execute(
        'DELETE FROM "05_monitoring"."11_fct_monitoring_panels" WHERE id = $1',
        id,
    )
    try:
        count = int(result.split()[-1])
    except Exception:  # noqa: BLE001
        count = 0
    return count > 0
