"""asyncpg raw SQL for product_ops.cohorts."""

from __future__ import annotations

from typing import Any


async def insert_cohort(
    conn: Any, *,
    cohort_id: str, slug: str, name: str, description: str | None,
    org_id: str, workspace_id: str, kind: str, definition: dict, created_by: str,
) -> dict:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."10_fct_cohorts"
            (id, slug, name, description, org_id, workspace_id, kind, definition, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
        cohort_id, slug, name, description, org_id, workspace_id, kind, definition, created_by,
    )
    return await get_cohort_by_id(conn, cohort_id)


async def get_cohort_by_id(conn: Any, cohort_id: str) -> dict:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_cohorts WHERE id = $1', cohort_id,
    )
    return dict(row) if row else {}


async def get_cohort_by_slug(conn: Any, *, workspace_id: str, slug: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_cohorts '
        'WHERE workspace_id = $1 AND slug = $2 AND is_deleted = FALSE',
        workspace_id, slug,
    )
    return dict(row) if row else None


async def list_cohorts(
    conn: Any, *, workspace_id: str,
    kind: str | None = None, limit: int = 100, offset: int = 0,
) -> tuple[list[dict], int]:
    where = ['workspace_id = $1', 'is_deleted = FALSE']
    args: list[Any] = [workspace_id]
    if kind:
        args.append(kind); where.append(f"kind = ${len(args)}")
    where_sql = " AND ".join(where)
    rows = await conn.fetch(
        f'SELECT * FROM "10_product_ops".v_cohorts WHERE {where_sql} '
        f'ORDER BY created_at DESC LIMIT ${len(args)+1} OFFSET ${len(args)+2}',
        *args, limit, offset,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_cohorts WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)


async def update_cohort(conn: Any, *, cohort_id: str, fields: dict) -> dict | None:
    if not fields:
        return await get_cohort_by_id(conn, cohort_id)
    set_parts: list[str] = []; values: list[Any] = []
    for i, (k, v) in enumerate(fields.items(), start=2):
        set_parts.append(f"{k} = ${i}"); values.append(v)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    sql = (f'UPDATE "10_product_ops"."10_fct_cohorts" '
           f'SET {", ".join(set_parts)} WHERE id = $1 RETURNING id')
    out = await conn.fetchrow(sql, cohort_id, *values)
    return await get_cohort_by_id(conn, cohort_id) if out else None


async def soft_delete_cohort(conn: Any, cohort_id: str) -> bool:
    res = await conn.execute(
        'UPDATE "10_product_ops"."10_fct_cohorts" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND deleted_at IS NULL',
        cohort_id,
    )
    return res.endswith(" 1")


# ── Membership operations ──────────────────────────────────────────

async def list_members(conn: Any, cohort_id: str, *, limit: int = 100, offset: int = 0) -> tuple[list[dict], int]:
    rows = await conn.fetch(
        """
        SELECT v.id, v.anonymous_id, v.user_id, v.first_seen, v.last_seen,
               vp.email, vp.name, vp.plan, vp.country, lcm.joined_at
          FROM "10_product_ops"."40_lnk_cohort_members" lcm
          JOIN "10_product_ops"."10_fct_visitors" v ON v.id = lcm.visitor_id
          LEFT JOIN "10_product_ops".v_visitor_profiles vp ON vp.id = v.id
         WHERE lcm.cohort_id = $1
         ORDER BY lcm.joined_at DESC
         LIMIT $2 OFFSET $3
        """,
        cohort_id, limit, offset,
    )
    total = await conn.fetchval(
        'SELECT COUNT(*) FROM "10_product_ops"."40_lnk_cohort_members" WHERE cohort_id = $1',
        cohort_id,
    )
    return [dict(r) for r in rows], int(total or 0)


async def get_all_visitors_in_workspace(conn: Any, workspace_id: str) -> list[dict]:
    """Pull every visitor profile in workspace for dynamic cohort evaluation.
    Returns the v_visitor_profiles rows. For very large workspaces this should
    be paged + processed in chunks; v1 keeps it simple."""
    rows = await conn.fetch(
        'SELECT * FROM "10_product_ops".v_visitor_profiles '
        'WHERE workspace_id = $1 AND is_deleted = FALSE',
        workspace_id,
    )
    return [dict(r) for r in rows]


async def get_current_member_ids(conn: Any, cohort_id: str) -> set[str]:
    rows = await conn.fetch(
        'SELECT visitor_id FROM "10_product_ops"."40_lnk_cohort_members" WHERE cohort_id = $1',
        cohort_id,
    )
    return {r["visitor_id"] for r in rows}


async def replace_membership(
    conn: Any, *, cohort_id: str, org_id: str,
    new_member_ids: set[str], to_add: set[str], to_remove: set[str],
) -> None:
    """Apply add + remove diffs to lnk_cohort_members."""
    if to_remove:
        await conn.execute(
            'DELETE FROM "10_product_ops"."40_lnk_cohort_members" '
            'WHERE cohort_id = $1 AND visitor_id = ANY($2::text[])',
            cohort_id, list(to_remove),
        )
    if to_add:
        await conn.executemany(
            """
            INSERT INTO "10_product_ops"."40_lnk_cohort_members"
                (cohort_id, visitor_id, org_id)
            VALUES ($1, $2, $3)
            ON CONFLICT (cohort_id, visitor_id) DO NOTHING
            """,
            [(cohort_id, vid, org_id) for vid in to_add],
        )
    # Update the materialized count + timestamp on fct_cohorts
    await conn.execute(
        """
        UPDATE "10_product_ops"."10_fct_cohorts"
           SET member_count = $2, last_computed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
         WHERE id = $1
        """,
        cohort_id, len(new_member_ids),
    )


async def insert_computation(
    conn: Any, *,
    comp_id: str, cohort_id: str, org_id: str, workspace_id: str,
    triggered_by: str | None, duration_ms: int,
    members_added: int, members_removed: int, final_count: int,
    metadata: dict,
) -> str:
    await conn.execute(
        """
        INSERT INTO "10_product_ops"."60_evt_cohort_computations"
            (id, cohort_id, org_id, workspace_id, triggered_by,
             duration_ms, members_added, members_removed, final_count, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
        """,
        comp_id, cohort_id, org_id, workspace_id, triggered_by,
        duration_ms, members_added, members_removed, final_count, metadata,
    )
    return comp_id


async def is_member(conn: Any, *, cohort_slug: str, workspace_id: str, visitor_id: str) -> bool:
    """Fast membership check used by the eligibility evaluator's cohort_member op."""
    row = await conn.fetchrow(
        """
        SELECT 1 FROM "10_product_ops"."40_lnk_cohort_members" lcm
          JOIN "10_product_ops"."10_fct_cohorts" c ON c.id = lcm.cohort_id
         WHERE c.workspace_id = $1
           AND c.slug = $2
           AND lcm.visitor_id = $3
           AND c.is_active = TRUE
           AND c.deleted_at IS NULL
         LIMIT 1
        """,
        workspace_id, cohort_slug, visitor_id,
    )
    return row is not None
