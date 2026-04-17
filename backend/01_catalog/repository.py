"""
Catalog repository — raw asyncpg upserts into `01_catalog` fct tables.

One function per write path. Reads are via helper fetches only.
No business logic here. Follow `.claude/rules/python.md`:
- conn (never pool)
- raw SQL
- asyncpg handles dict → JSONB automatically
"""

from __future__ import annotations

import asyncpg

_SCHEMA = '"01_catalog"'


# ── dim lookups (cached in-proc; dim rows never change) ─────────────

_dim_cache: dict[str, dict[str, int]] = {}


async def _load_dim(conn: asyncpg.Connection, table: str) -> dict[str, int]:
    if table in _dim_cache:
        return _dim_cache[table]
    rows = await conn.fetch(f'SELECT id, code FROM {_SCHEMA}."{table}"')
    mapping = {row["code"]: row["id"] for row in rows}
    _dim_cache[table] = mapping
    return mapping


async def get_module_id(conn: asyncpg.Connection, code: str) -> int:
    mapping = await _load_dim(conn, "01_dim_modules")
    if code not in mapping:
        raise LookupError(f"Unknown module code: {code!r}")
    return mapping[code]


async def get_node_kind_id(conn: asyncpg.Connection, code: str) -> int:
    mapping = await _load_dim(conn, "02_dim_node_kinds")
    if code not in mapping:
        raise LookupError(f"Unknown node kind: {code!r}")
    return mapping[code]


async def get_tx_mode_id(conn: asyncpg.Connection, code: str) -> int:
    mapping = await _load_dim(conn, "03_dim_tx_modes")
    if code not in mapping:
        raise LookupError(f"Unknown tx mode: {code!r}")
    return mapping[code]


def reset_dim_cache() -> None:
    """Clear cache — useful in tests."""
    _dim_cache.clear()


# ── fct upserts ─────────────────────────────────────────────────────

async def upsert_feature(
    conn: asyncpg.Connection,
    *,
    key: str,
    number: int,
    module_id: int,
) -> int:
    """Upsert by key without burning the SMALLINT sequence on conflicts.

    Uses SELECT-then-INSERT-or-UPDATE so the sequence only advances for
    genuinely new rows (INSERT ... ON CONFLICT DO UPDATE always advances
    the sequence, exhausting SMALLINT quickly across test runs).
    """
    existing = await conn.fetchrow(
        f'SELECT id FROM {_SCHEMA}."10_fct_features" WHERE key = $1', key
    )
    if existing:
        await conn.execute(
            f"""
            UPDATE {_SCHEMA}."10_fct_features"
            SET number = $2, module_id = $3,
                updated_at = CURRENT_TIMESTAMP,
                deprecated_at = NULL, tombstoned_at = NULL
            WHERE key = $1
            """,
            key, number, module_id,
        )
        return existing["id"]
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_SCHEMA}."10_fct_features" (key, number, module_id)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        key, number, module_id,
    )
    assert row is not None
    return row["id"]


async def upsert_sub_feature(
    conn: asyncpg.Connection,
    *,
    key: str,
    feature_id: int,
    number: int,
) -> int:
    """Upsert by key without burning the SMALLINT sequence on conflicts."""
    existing = await conn.fetchrow(
        f'SELECT id FROM {_SCHEMA}."11_fct_sub_features" WHERE key = $1', key
    )
    if existing:
        await conn.execute(
            f"""
            UPDATE {_SCHEMA}."11_fct_sub_features"
            SET feature_id = $2, number = $3,
                updated_at = CURRENT_TIMESTAMP,
                deprecated_at = NULL, tombstoned_at = NULL
            WHERE key = $1
            """,
            key, feature_id, number,
        )
        return existing["id"]
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_SCHEMA}."11_fct_sub_features" (key, feature_id, number)
        VALUES ($1, $2, $3)
        RETURNING id
        """,
        key, feature_id, number,
    )
    assert row is not None
    return row["id"]


async def upsert_node(
    conn: asyncpg.Connection,
    *,
    key: str,
    sub_feature_id: int,
    kind_id: int,
    handler_path: str,
    version: int,
    emits_audit: bool,
    timeout_ms: int,
    retries: int,
    tx_mode_id: int,
) -> int:
    """Upsert by key without burning the SMALLINT sequence on conflicts."""
    existing = await conn.fetchrow(
        f'SELECT id FROM {_SCHEMA}."12_fct_nodes" WHERE key = $1', key
    )
    if existing:
        await conn.execute(
            f"""
            UPDATE {_SCHEMA}."12_fct_nodes"
            SET sub_feature_id = $2, kind_id = $3, handler_path = $4,
                version = $5, emits_audit = $6, timeout_ms = $7, retries = $8,
                tx_mode_id = $9, updated_at = CURRENT_TIMESTAMP,
                deprecated_at = NULL, tombstoned_at = NULL
            WHERE key = $1
            """,
            key, sub_feature_id, kind_id, handler_path,
            version, emits_audit, timeout_ms, retries, tx_mode_id,
        )
        return existing["id"]
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_SCHEMA}."12_fct_nodes" (
            key, sub_feature_id, kind_id, handler_path,
            version, emits_audit, timeout_ms, retries, tx_mode_id
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id
        """,
        key, sub_feature_id, kind_id, handler_path,
        version, emits_audit, timeout_ms, retries, tx_mode_id,
    )
    assert row is not None
    return row["id"]


# ── deprecation sweep ───────────────────────────────────────────────

async def mark_absent_deprecated(
    conn: asyncpg.Connection,
    *,
    table: str,
    keys_present: set[str],
) -> int:
    """
    For any row in `table` whose key is NOT in keys_present AND deprecated_at IS NULL,
    set deprecated_at = CURRENT_TIMESTAMP.

    `table` must be one of: '10_fct_features', '11_fct_sub_features', '12_fct_nodes'.
    Returns number of rows marked deprecated.
    """
    if table not in ("10_fct_features", "11_fct_sub_features", "12_fct_nodes"):
        raise ValueError(f"Cannot sweep table {table!r}")
    if not keys_present:
        # Nothing present — still safely no-op (don't deprecate everything on an empty boot;
        # that would nuke the whole catalog if loader misfires).
        return 0
    result = await conn.execute(
        f"""
        UPDATE {_SCHEMA}."{table}"
        SET deprecated_at = CURRENT_TIMESTAMP
        WHERE deprecated_at IS NULL
          AND key != ALL($1::text[])
        """,
        list(keys_present),
    )
    # asyncpg execute returns 'UPDATE N'
    try:
        return int(result.split()[-1])
    except (ValueError, IndexError):
        return 0
