"""
featureflags.flags — asyncpg repository.

Reads via v_flags / v_flag_states (flat shapes).
Writes to 10_fct_flags + 11_fct_flag_states.
"""

from __future__ import annotations

from typing import Any

_SENTINEL = object()  # marker for "field not provided" in partial updates


# ─── Dim resolvers ──────────────────────────────────────────────────

async def get_scope_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "09_featureflags"."03_dim_flag_scopes" WHERE code = $1',
        code,
    )


async def get_value_type_id(conn: Any, code: str) -> int | None:
    return await conn.fetchval(
        'SELECT id FROM "09_featureflags"."02_dim_value_types" WHERE code = $1',
        code,
    )


async def list_env_ids(conn: Any) -> list[int]:
    rows = await conn.fetch(
        'SELECT id FROM "09_featureflags"."01_dim_environments" '
        'WHERE deprecated_at IS NULL ORDER BY id',
    )
    return [int(r["id"]) for r in rows]


# ─── Flags ──────────────────────────────────────────────────────────

_FLAG_COLS = (
    "id, scope, org_id, application_id, flag_key, value_type, "
    "default_value, description, is_active, is_test, "
    "created_by, updated_by, created_at, updated_at"
)


async def get_flag_by_id(conn: Any, flag_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT {_FLAG_COLS} FROM "09_featureflags"."v_flags" '
        'WHERE id = $1 AND deleted_at IS NULL',
        flag_id,
    )
    return dict(row) if row else None


async def get_flag_by_scope_key(
    conn: Any,
    *,
    scope: str,
    org_id: str | None,
    application_id: str | None,
    flag_key: str,
) -> dict | None:
    if scope == "global":
        row = await conn.fetchrow(
            f'SELECT {_FLAG_COLS} FROM "09_featureflags"."v_flags" '
            "WHERE scope = 'global' AND flag_key = $1 AND deleted_at IS NULL",
            flag_key,
        )
    elif scope == "org":
        row = await conn.fetchrow(
            f'SELECT {_FLAG_COLS} FROM "09_featureflags"."v_flags" '
            "WHERE scope = 'org' AND org_id = $1 AND flag_key = $2 AND deleted_at IS NULL",
            org_id, flag_key,
        )
    else:  # application
        row = await conn.fetchrow(
            f'SELECT {_FLAG_COLS} FROM "09_featureflags"."v_flags" '
            "WHERE scope = 'application' AND application_id = $1 "
            "AND flag_key = $2 AND deleted_at IS NULL",
            application_id, flag_key,
        )
    return dict(row) if row else None


async def list_flags(
    conn: Any,
    *,
    limit: int,
    offset: int,
    scope: str | None = None,
    org_id: str | None = None,
    application_id: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if scope is not None:
        params.append(scope)
        where.append(f"scope = ${len(params)}")
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    if application_id is not None:
        params.append(application_id)
        where.append(f"application_id = ${len(params)}")
    if is_active is not None:
        params.append(is_active)
        where.append(f"is_active = ${len(params)}")
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "09_featureflags"."v_flags" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    l_idx, o_idx = len(params_page) - 1, len(params_page)
    rows = await conn.fetch(
        f'SELECT {_FLAG_COLS} FROM "09_featureflags"."v_flags" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, id DESC '
        f'LIMIT ${l_idx} OFFSET ${o_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_flag(
    conn: Any,
    *,
    id: str,
    scope_id: int,
    org_id: str | None,
    application_id: str | None,
    flag_key: str,
    value_type_id: int,
    default_value: Any,
    description: str | None,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "09_featureflags"."10_fct_flags" '
        '  (id, scope_id, org_id, application_id, flag_key, value_type_id, '
        '   default_value_jsonb, description, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $9)',
        id, scope_id, org_id, application_id,
        flag_key, value_type_id, default_value, description, created_by,
    )


async def update_flag_fields(
    conn: Any,
    *,
    id: str,
    default_value: Any = _SENTINEL,
    description: Any = _SENTINEL,
    is_active: Any = _SENTINEL,
    updated_by: str,
) -> bool:
    sets: list[str] = []
    params: list[Any] = []
    if default_value is not _SENTINEL:
        params.append(default_value)
        sets.append(f"default_value_jsonb = ${len(params)}")
    if description is not _SENTINEL:
        params.append(description)
        sets.append(f"description = ${len(params)}")
    if is_active is not _SENTINEL:
        params.append(is_active)
        sets.append(f"is_active = ${len(params)}")
    if not sets:
        return False
    params.append(updated_by)
    params.append(id)
    sets.append(f"updated_by = ${len(params) - 1}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    result = await conn.execute(
        f'UPDATE "09_featureflags"."10_fct_flags" SET {", ".join(sets)} '
        f'WHERE id = ${len(params)} AND deleted_at IS NULL',
        *params,
    )
    return result.endswith(" 1")


async def soft_delete_flag(
    conn: Any, *, id: str, updated_by: str,
) -> bool:
    result = await conn.execute(
        'UPDATE "09_featureflags"."10_fct_flags" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")


# ─── Flag states ────────────────────────────────────────────────────

_STATE_COLS = (
    "id, flag_id, environment, is_enabled, env_default_value, is_test, "
    "created_by, updated_by, created_at, updated_at"
)


async def get_flag_state_by_id(conn: Any, state_id: str) -> dict | None:
    row = await conn.fetchrow(
        f'SELECT {_STATE_COLS} FROM "09_featureflags"."v_flag_states" '
        'WHERE id = $1 AND deleted_at IS NULL',
        state_id,
    )
    return dict(row) if row else None


async def list_flag_states(
    conn: Any,
    *,
    limit: int,
    offset: int,
    flag_id: str | None = None,
) -> tuple[list[dict], int]:
    where = ["deleted_at IS NULL"]
    params: list[Any] = []
    if flag_id is not None:
        params.append(flag_id)
        where.append(f"flag_id = ${len(params)}")
    where_sql = " AND ".join(where)
    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "09_featureflags"."v_flag_states" WHERE {where_sql}',
        *params,
    )
    params_page = [*params, limit, offset]
    l_idx, o_idx = len(params_page) - 1, len(params_page)
    rows = await conn.fetch(
        f'SELECT {_STATE_COLS} FROM "09_featureflags"."v_flag_states" '
        f'WHERE {where_sql} '
        f'ORDER BY flag_id, environment '
        f'LIMIT ${l_idx} OFFSET ${o_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_flag_state(
    conn: Any,
    *,
    id: str,
    flag_id: str,
    environment_id: int,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "09_featureflags"."11_fct_flag_states" '
        '  (id, flag_id, environment_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $4)',
        id, flag_id, environment_id, created_by,
    )


async def update_flag_state_fields(
    conn: Any,
    *,
    id: str,
    is_enabled: Any = _SENTINEL,
    env_default_value: Any = _SENTINEL,
    updated_by: str,
) -> bool:
    sets: list[str] = []
    params: list[Any] = []
    if is_enabled is not _SENTINEL:
        params.append(is_enabled)
        sets.append(f"is_enabled = ${len(params)}")
    if env_default_value is not _SENTINEL:
        params.append(env_default_value)
        sets.append(f"env_default_value_jsonb = ${len(params)}")
    if not sets:
        return False
    params.append(updated_by)
    params.append(id)
    sets.append(f"updated_by = ${len(params) - 1}")
    sets.append("updated_at = CURRENT_TIMESTAMP")
    result = await conn.execute(
        f'UPDATE "09_featureflags"."11_fct_flag_states" SET {", ".join(sets)} '
        f'WHERE id = ${len(params)} AND deleted_at IS NULL',
        *params,
    )
    return result.endswith(" 1")


async def soft_delete_flag_states_cascade(
    conn: Any, *, flag_id: str, updated_by: str,
) -> int:
    result = await conn.execute(
        'UPDATE "09_featureflags"."11_fct_flag_states" '
        'SET deleted_at = CURRENT_TIMESTAMP, updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE flag_id = $2 AND deleted_at IS NULL',
        updated_by, flag_id,
    )
    # result format: "UPDATE <n>"; extract n for count
    parts = result.split()
    return int(parts[-1]) if parts and parts[-1].isdigit() else 0
