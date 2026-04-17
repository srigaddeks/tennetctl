"""
audit.saved_views — asyncpg repository.

Reads from v_audit_saved_views. Writes to 10_fct_audit_saved_views and
20_dtl_audit_saved_view_details. Views are org-scoped.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")

_FCT  = '"04_audit"."10_fct_audit_saved_views"'
_DTL  = '"04_audit"."20_dtl_audit_saved_view_details"'
_VIEW = '"04_audit"."v_audit_saved_views"'


async def list_saved_views(conn: Any, *, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT id, org_id, user_id, name, filter_json, bucket, created_at "
        f"FROM {_VIEW} WHERE org_id = $1 ORDER BY created_at DESC",
        org_id,
    )
    return [dict(r) for r in rows]


async def get_saved_view(conn: Any, *, view_id: str, org_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT id, org_id, user_id, name, filter_json, bucket, created_at "
        f"FROM {_VIEW} WHERE id = $1 AND org_id = $2",
        view_id, org_id,
    )
    return dict(row) if row else None


async def create_saved_view(
    conn: Any,
    *,
    org_id: str,
    user_id: str | None,
    name: str,
    filter_json: dict,
    bucket: str,
) -> dict:
    fct_id = _core_id.uuid7()
    dtl_id = _core_id.uuid7()

    await conn.execute(
        f"INSERT INTO {_FCT} (id, org_id, user_id) VALUES ($1, $2, $3)",
        fct_id, org_id, user_id,
    )
    await conn.execute(
        f"INSERT INTO {_DTL} (id, saved_view_id, name, filter_json, bucket) "
        f"VALUES ($1, $2, $3, $4, $5)",
        dtl_id, fct_id, name, filter_json, bucket,
    )
    # Read-back via view for consistent shape.
    row = await conn.fetchrow(
        f"SELECT id, org_id, user_id, name, filter_json, bucket, created_at "
        f"FROM {_VIEW} WHERE id = $1",
        fct_id,
    )
    return dict(row)


async def delete_saved_view(conn: Any, *, view_id: str, org_id: str) -> bool:
    """Delete by id + org_id guard. Returns True if a row was deleted."""
    result = await conn.execute(
        f"DELETE FROM {_FCT} WHERE id = $1 AND org_id = $2",
        view_id, org_id,
    )
    # result is e.g. "DELETE 1" or "DELETE 0"
    return result.endswith("1")
