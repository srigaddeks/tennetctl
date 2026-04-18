"""iam.portal_views — asyncpg repository.

Reads:  08_dim_portal_views (dim), 46_lnk_role_views (lnk), 42_lnk_user_roles (lnk)
Writes: 46_lnk_role_views
"""

from __future__ import annotations

from typing import Any


# ── Dim reads ──────────────────────────────────────────────────────────────────

async def list_all_views(conn: Any) -> list[dict]:
    """Return all non-deprecated portal views ordered by sort_order."""
    rows = await conn.fetch(
        """
        SELECT id, code, label, icon, color, default_route, sort_order, deprecated_at
        FROM "03_iam"."08_dim_portal_views"
        WHERE deprecated_at IS NULL
        ORDER BY sort_order
        """
    )
    return [dict(r) for r in rows]


async def list_all_views_including_deprecated(conn: Any) -> list[dict]:
    """Return every portal view (admin use — includes deprecated)."""
    rows = await conn.fetch(
        """
        SELECT id, code, label, icon, color, default_route, sort_order, deprecated_at
        FROM "03_iam"."08_dim_portal_views"
        ORDER BY sort_order
        """
    )
    return [dict(r) for r in rows]


async def get_view_by_id(conn: Any, view_id: int) -> dict | None:
    row = await conn.fetchrow(
        """
        SELECT id, code, label, icon, color, default_route, sort_order, deprecated_at
        FROM "03_iam"."08_dim_portal_views"
        WHERE id = $1
        """,
        view_id,
    )
    return dict(row) if row else None


# ── lnk_role_views reads ───────────────────────────────────────────────────────

async def list_role_views(conn: Any, role_id: str) -> list[dict]:
    """Return all view assignments for a role with joined dim data."""
    rows = await conn.fetch(
        """
        SELECT
            rv.id, rv.role_id, rv.view_id, rv.org_id, rv.created_by, rv.created_at,
            v.code, v.label, v.icon, v.color, v.default_route, v.sort_order
        FROM "03_iam"."46_lnk_role_views" rv
        JOIN "03_iam"."08_dim_portal_views" v ON v.id = rv.view_id
        WHERE rv.role_id = $1
        ORDER BY v.sort_order
        """,
        role_id,
    )
    return [dict(r) for r in rows]


async def count_grants_per_view(conn: Any) -> dict[int, int]:
    """Return {view_id: grant_count} for all views."""
    rows = await conn.fetch(
        """
        SELECT view_id, COUNT(*) AS cnt
        FROM "03_iam"."46_lnk_role_views"
        GROUP BY view_id
        """
    )
    return {r["view_id"]: r["cnt"] for r in rows}


# ── lnk_role_views writes ──────────────────────────────────────────────────────

async def attach_view(
    conn: Any,
    *,
    id: str,
    role_id: str,
    view_id: int,
    org_id: str,
    created_by: str,
) -> dict:
    """Insert a role→view grant (idempotent via ON CONFLICT DO NOTHING).

    Returns the existing or newly-inserted row.
    """
    # Try insert first
    row = await conn.fetchrow(
        """
        INSERT INTO "03_iam"."46_lnk_role_views"
            (id, role_id, view_id, org_id, created_by)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (role_id, view_id) DO NOTHING
        RETURNING id, role_id, view_id, org_id, created_by, created_at
        """,
        id, role_id, view_id, org_id, created_by,
    )
    if row:
        return dict(row)
    # Already exists — fetch the existing row
    existing = await conn.fetchrow(
        """
        SELECT id, role_id, view_id, org_id, created_by, created_at
        FROM "03_iam"."46_lnk_role_views"
        WHERE role_id = $1 AND view_id = $2
        """,
        role_id, view_id,
    )
    return dict(existing)  # type: ignore[arg-type]


async def detach_view(conn: Any, *, role_id: str, view_id: int) -> bool:
    """Delete a role→view grant. Returns True if a row was deleted."""
    result = await conn.execute(
        """
        DELETE FROM "03_iam"."46_lnk_role_views"
        WHERE role_id = $1 AND view_id = $2
        """,
        role_id, view_id,
    )
    return result != "DELETE 0"


# ── /my-views resolver ─────────────────────────────────────────────────────────

async def resolve_my_views(conn: Any, user_id: str, org_id: str) -> list[dict]:
    """Return distinct views granted to the user via their role assignments.

    Joins: lnk_user_roles → lnk_role_views → dim_portal_views.
    Falls back to empty list when no grants exist (caller handles fallback logic).
    """
    rows = await conn.fetch(
        """
        SELECT DISTINCT
            v.code, v.label, v.icon, v.color, v.default_route, v.sort_order
        FROM "03_iam"."42_lnk_user_roles" ur
        JOIN "03_iam"."46_lnk_role_views" rv ON rv.role_id = ur.role_id
        JOIN "03_iam"."08_dim_portal_views" v ON v.id = rv.view_id
        WHERE ur.user_id = $1
          AND (ur.org_id = $2 OR ur.org_id IS NULL)
          AND ur.revoked_at IS NULL
          AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
          AND v.deprecated_at IS NULL
        ORDER BY v.sort_order
        """,
        user_id, org_id,
    )
    return [dict(r) for r in rows]
