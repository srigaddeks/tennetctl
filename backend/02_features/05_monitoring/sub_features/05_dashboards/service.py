"""Service layer for monitoring.dashboards.

Creates/updates/deletes dashboards + panels. Emits audit events via
`audit.events.emit` node for every mutation. Panel deletes are implicit
(CASCADE) when the parent dashboard is soft-deleted — note that soft-delete
does NOT cascade panel rows; they remain in fct_monitoring_panels but are
unreachable through the dashboards view. A future hard-delete job is expected
to clean them up.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.05_dashboards.repository"
)


# ---------- dashboards ----------

async def create_dashboard(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    owner_user_id: str,
    name: str,
    description: str | None,
    layout: dict[str, Any] | None,
    shared: bool,
) -> dict[str, Any]:
    existing = await conn.fetchrow(
        """
        SELECT id FROM "05_monitoring"."10_fct_monitoring_dashboards"
         WHERE org_id = $1 AND owner_user_id = $2 AND name = $3
           AND deleted_at IS NULL
        """,
        org_id, owner_user_id, name,
    )
    if existing is not None:
        raise _errors.AppError(
            "DUPLICATE",
            f"dashboard {name!r} already exists for this owner in this org",
            400,
        )
    dash_id = _core_id.uuid7()
    row = await _repo.insert_dashboard(
        conn,
        id=dash_id, org_id=org_id, owner_user_id=owner_user_id,
        name=name, description=description,
        layout=layout or {}, shared=shared,
    )
    await _emit_audit(
        pool, ctx, "monitoring.dashboards.created",
        {"dashboard_id": dash_id, "name": name, "shared": shared},
    )
    return row


async def list_dashboards(
    conn: Any,
    *,
    org_id: str,
    owner_user_id: str,
) -> list[dict[str, Any]]:
    return await _repo.list_dashboards(
        conn, org_id=org_id, owner_user_id=owner_user_id, include_shared=True,
    )


async def get_dashboard(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    id: str,
) -> dict[str, Any] | None:
    row = await _repo.get_dashboard_by_id(conn, id=id)
    if row is None:
        return None
    if row["org_id"] != org_id:
        return None
    if row["owner_user_id"] != user_id and not row["shared"]:
        return None
    return row


async def update_dashboard(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    user_id: str,
    id: str,
    name: str | None,
    description: str | None,
    layout: dict[str, Any] | None,
    shared: bool | None,
    is_active: bool | None,
) -> dict[str, Any] | None:
    existing = await _repo.get_dashboard_by_id(conn, id=id)
    if existing is None or existing["org_id"] != org_id:
        return None
    if existing["owner_user_id"] != user_id:
        raise _errors.ForbiddenError("only the owner may update this dashboard")
    row = await _repo.update_dashboard(
        conn, id=id, name=name, description=description,
        layout=layout, shared=shared, is_active=is_active,
    )
    await _emit_audit(
        pool, ctx, "monitoring.dashboards.updated",
        {"dashboard_id": id},
    )
    return row


async def delete_dashboard(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    user_id: str,
    id: str,
) -> bool:
    existing = await _repo.get_dashboard_by_id(conn, id=id)
    if existing is None or existing["org_id"] != org_id:
        return False
    if existing["owner_user_id"] != user_id:
        raise _errors.ForbiddenError("only the owner may delete this dashboard")
    ok = await _repo.soft_delete_dashboard(conn, id=id)
    if ok:
        await _emit_audit(
            pool, ctx, "monitoring.dashboards.deleted",
            {"dashboard_id": id},
        )
    return ok


# ---------- panels ----------

async def list_panels(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    dashboard_id: str,
) -> list[dict[str, Any]] | None:
    dash = await get_dashboard(conn, org_id=org_id, user_id=user_id, id=dashboard_id)
    if dash is None:
        return None
    return await _repo.list_panels_for_dashboard(conn, dashboard_id=dashboard_id)


async def create_panel(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    user_id: str,
    dashboard_id: str,
    title: str,
    panel_type: str,
    dsl: dict[str, Any],
    grid_pos: dict[str, Any] | None,
    display_opts: dict[str, Any] | None,
) -> dict[str, Any] | None:
    existing = await _repo.get_dashboard_by_id(conn, id=dashboard_id)
    if existing is None or existing["org_id"] != org_id:
        return None
    if existing["owner_user_id"] != user_id:
        raise _errors.ForbiddenError(
            "only the dashboard owner may add panels"
        )
    panel_id = _core_id.uuid7()
    row = await _repo.insert_panel(
        conn,
        id=panel_id, dashboard_id=dashboard_id,
        title=title, panel_type=panel_type,
        dsl=dsl,
        grid_pos=grid_pos or {"x": 0, "y": 0, "w": 6, "h": 4},
        display_opts=display_opts or {},
    )
    await _emit_audit(
        pool, ctx, "monitoring.panels.created",
        {"panel_id": panel_id, "dashboard_id": dashboard_id, "panel_type": panel_type},
    )
    return row


async def get_panel(
    conn: Any,
    *,
    org_id: str,
    user_id: str,
    dashboard_id: str,
    panel_id: str,
) -> dict[str, Any] | None:
    dash = await get_dashboard(conn, org_id=org_id, user_id=user_id, id=dashboard_id)
    if dash is None:
        return None
    row = await _repo.get_panel_by_id(conn, id=panel_id)
    if row is None or row["dashboard_id"] != dashboard_id:
        return None
    return row


async def update_panel(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    user_id: str,
    dashboard_id: str,
    panel_id: str,
    title: str | None,
    panel_type: str | None,
    dsl: dict[str, Any] | None,
    grid_pos: dict[str, Any] | None,
    display_opts: dict[str, Any] | None,
) -> dict[str, Any] | None:
    dash = await _repo.get_dashboard_by_id(conn, id=dashboard_id)
    if dash is None or dash["org_id"] != org_id:
        return None
    if dash["owner_user_id"] != user_id:
        raise _errors.ForbiddenError(
            "only the dashboard owner may update panels"
        )
    existing = await _repo.get_panel_by_id(conn, id=panel_id)
    if existing is None or existing["dashboard_id"] != dashboard_id:
        return None
    row = await _repo.update_panel(
        conn, id=panel_id,
        title=title, panel_type=panel_type, dsl=dsl,
        grid_pos=grid_pos, display_opts=display_opts,
    )
    await _emit_audit(
        pool, ctx, "monitoring.panels.updated",
        {"panel_id": panel_id, "dashboard_id": dashboard_id},
    )
    return row


async def delete_panel(
    conn: Any,
    ctx: Any,
    pool: Any,
    *,
    org_id: str,
    user_id: str,
    dashboard_id: str,
    panel_id: str,
) -> bool:
    dash = await _repo.get_dashboard_by_id(conn, id=dashboard_id)
    if dash is None or dash["org_id"] != org_id:
        return False
    if dash["owner_user_id"] != user_id:
        raise _errors.ForbiddenError(
            "only the dashboard owner may delete panels"
        )
    existing = await _repo.get_panel_by_id(conn, id=panel_id)
    if existing is None or existing["dashboard_id"] != dashboard_id:
        return False
    ok = await _repo.delete_panel(conn, id=panel_id)
    if ok:
        await _emit_audit(
            pool, ctx, "monitoring.panels.deleted",
            {"panel_id": panel_id, "dashboard_id": dashboard_id},
        )
    return ok


# ---------- helpers ----------

async def _emit_audit(
    pool: Any, ctx: Any, event_key: str, metadata: dict[str, Any],
) -> None:
    try:
        await _catalog.run_node(
            pool,
            "audit.events.emit",
            ctx,
            {
                "event_key": event_key,
                "outcome": "success",
                "metadata": metadata,
            },
        )
    except Exception:  # noqa: BLE001
        # Fire-and-forget: never fail the request solely because audit failed.
        pass
