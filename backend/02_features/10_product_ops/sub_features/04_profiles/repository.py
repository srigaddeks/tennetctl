"""asyncpg raw SQL for product_ops.profiles."""

from __future__ import annotations

from typing import Any


# ── Attribute definition lookup ─────────────────────────────────────

async def get_attr_defs(conn: Any) -> dict[str, dict]:
    """Cache-able lookup: code → {id, value_type, label}. Stable across the run."""
    rows = await conn.fetch(
        """
        SELECT id, code, label, value_type
          FROM "10_product_ops"."03_dim_attr_defs"
         WHERE entity_type = 'visitor' AND deprecated_at IS NULL
        """,
    )
    return {r["code"]: dict(r) for r in rows}


async def upsert_visitor_attr(
    conn: Any,
    *,
    attr_id: str,
    visitor_id: str,
    attr_def_id: int,
    value_type: str,
    value: Any,
    source: str,
) -> None:
    """Set or replace a single trait. UNIQUE (visitor_id, attr_def_id) enforces 1:1."""
    if value_type == "text":
        kt, kj, ks = (str(value) if value is not None else None), None, None
    elif value_type == "jsonb":
        kt, kj, ks = None, value, None
    elif value_type == "smallint":
        kt, kj, ks = None, None, int(value) if value is not None else None
    else:
        raise ValueError(f"unknown value_type {value_type!r}")

    await conn.execute(
        """
        INSERT INTO "10_product_ops"."20_dtl_visitor_attrs"
            (id, visitor_id, attr_def_id, key_text, key_jsonb, key_smallint, source)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (visitor_id, attr_def_id) DO UPDATE
            SET key_text     = EXCLUDED.key_text,
                key_jsonb    = EXCLUDED.key_jsonb,
                key_smallint = EXCLUDED.key_smallint,
                source       = EXCLUDED.source,
                set_at       = CURRENT_TIMESTAMP,
                updated_at   = CURRENT_TIMESTAMP
        """,
        attr_id, visitor_id, attr_def_id, kt, kj, ks, source,
    )


async def get_visitor_attrs(conn: Any, visitor_id: str) -> list[dict]:
    """Return all traits set on a visitor as flat rows joined to dim_attr_defs."""
    rows = await conn.fetch(
        """
        SELECT ad.code, ad.label, ad.value_type,
               COALESCE(t.key_text, t.key_jsonb::text, t.key_smallint::text) AS value_str,
               t.key_text, t.key_jsonb, t.key_smallint,
               t.source, t.set_at
          FROM "10_product_ops"."20_dtl_visitor_attrs" t
          JOIN "10_product_ops"."03_dim_attr_defs" ad ON ad.id = t.attr_def_id
         WHERE t.visitor_id = $1
         ORDER BY ad.code
        """,
        visitor_id,
    )
    out: list[dict] = []
    for r in rows:
        d = dict(r)
        # Pick the typed value back out
        if d["value_type"] == "text":
            d["value"] = d["key_text"]
        elif d["value_type"] == "jsonb":
            d["value"] = d["key_jsonb"]
        else:
            d["value"] = d["key_smallint"]
        for k in ("key_text", "key_jsonb", "key_smallint", "value_str"):
            d.pop(k, None)
        out.append(d)
    return out


# ── Profile read views ──────────────────────────────────────────────

async def get_profile(conn: Any, visitor_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "10_product_ops".v_visitor_profiles WHERE id = $1',
        visitor_id,
    )
    return dict(row) if row else None


async def list_profiles(
    conn: Any,
    *,
    workspace_id: str,
    q: str | None = None,         # substring match on email / name / company
    plan: str | None = None,
    country: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    where = ['workspace_id = $1', 'is_deleted = FALSE']
    args: list[Any] = [workspace_id]
    if q:
        args.append(f"%{q}%")
        i = len(args)
        where.append(f"(email ILIKE ${i} OR name ILIKE ${i} OR company ILIKE ${i})")
    if plan:
        args.append(plan)
        where.append(f"plan = ${len(args)}")
    if country:
        args.append(country)
        where.append(f"country = ${len(args)}")

    where_sql = " AND ".join(where)
    args_with_paging = [*args, limit, offset]
    rows = await conn.fetch(
        f"""
        SELECT * FROM "10_product_ops".v_visitor_profiles
         WHERE {where_sql}
         ORDER BY last_seen DESC
         LIMIT ${len(args)+1} OFFSET ${len(args)+2}
        """,
        *args_with_paging,
    )
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "10_product_ops".v_visitor_profiles WHERE {where_sql}',
        *args,
    )
    return [dict(r) for r in rows], int(total or 0)
