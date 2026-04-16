"""
vault.configs — asyncpg repository.

Reads from v_vault_configs (scope+value_type codes joined, description pivoted).
Writes to fct_vault_configs + dtl_attrs. Configs are NOT versioned — UPDATE is
in-place.
"""

from __future__ import annotations

from typing import Any

_CONFIG_ENTITY_TYPE_ID = 2  # dim_entity_types row for "config"

_SCOPE_CODE_TO_ID = {"global": 1, "org": 2, "workspace": 3}
_VALUE_TYPE_CODE_TO_ID = {"boolean": 1, "string": 2, "number": 3, "json": 4}


def _scope_id(scope: str) -> int:
    try:
        return _SCOPE_CODE_TO_ID[scope]
    except KeyError as e:
        raise ValueError(f"unknown scope {scope!r}") from e


def _value_type_id(value_type: str) -> int:
    try:
        return _VALUE_TYPE_CODE_TO_ID[value_type]
    except KeyError as e:
        raise ValueError(f"unknown value_type {value_type!r}") from e


async def _get_description_attr_def_id(conn: Any) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "02_vault"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _CONFIG_ENTITY_TYPE_ID,
        "description",
    )
    if row is None:
        raise RuntimeError(
            "attr_def missing: (entity_type_id=2, code='description'). "
            "Re-run vault configs migration."
        )
    return int(row["id"])


async def get_by_id(conn: Any, config_id: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, key, value_type, value_jsonb AS value, description, '
        '       scope, org_id, workspace_id, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "02_vault"."v_vault_configs" '
        'WHERE id = $1',
        config_id,
    )
    return dict(row) if row else None


async def get_by_scope_key(
    conn: Any,
    *,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    key: str,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, key, value_type, value_jsonb AS value, description, '
        '       scope, org_id, workspace_id, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "02_vault"."v_vault_configs" '
        'WHERE scope = $1 '
        '  AND org_id IS NOT DISTINCT FROM $2 '
        '  AND workspace_id IS NOT DISTINCT FROM $3 '
        '  AND key = $4',
        scope, org_id, workspace_id, key,
    )
    return dict(row) if row else None


async def list_configs(
    conn: Any,
    *,
    limit: int,
    offset: int,
    scope: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> tuple[list[dict], int]:
    where: list[str] = []
    params: list[Any] = []
    if scope is not None:
        params.append(scope)
        where.append(f"scope = ${len(params)}")
    if org_id is not None:
        params.append(org_id)
        where.append(f"org_id = ${len(params)}")
    if workspace_id is not None:
        params.append(workspace_id)
        where.append(f"workspace_id = ${len(params)}")
    where_sql = (" WHERE " + " AND ".join(where)) if where else ""

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "02_vault"."v_vault_configs"{where_sql}',
        *params,
    )

    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, key, value_type, value_jsonb AS value, description, '
        f'       scope, org_id, workspace_id, is_active, is_test, '
        f'       created_by, updated_by, created_at, updated_at '
        f'FROM "02_vault"."v_vault_configs"{where_sql} '
        f'ORDER BY created_at DESC, scope, key '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def insert_config(
    conn: Any,
    *,
    id: str,
    key: str,
    value_type: str,
    value: Any,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "02_vault"."11_fct_vault_configs" '
        '(id, key, value_type_id, value_jsonb, '
        ' scope_id, org_id, workspace_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)',
        id, key, _value_type_id(value_type), value,
        _scope_id(scope), org_id, workspace_id, created_by,
    )


async def update_config(
    conn: Any,
    *,
    id: str,
    value: Any = None,
    is_active: bool | None = None,
    updated_by: str,
    has_value: bool = False,
    has_is_active: bool = False,
) -> bool:
    """Update value and/or is_active. Returns True if a row was modified."""
    sets: list[str] = []
    params: list[Any] = []
    if has_value:
        params.append(value)
        sets.append(f"value_jsonb = ${len(params)}")
    if has_is_active:
        params.append(is_active)
        sets.append(f"is_active = ${len(params)}")
    if not sets:
        return False
    params.append(updated_by)
    sets.append(f"updated_by = ${len(params)}")
    sets.append("updated_at = CURRENT_TIMESTAMP")

    params.append(id)
    result = await conn.execute(
        f'UPDATE "02_vault"."11_fct_vault_configs" '
        f'SET {", ".join(sets)} '
        f'WHERE id = ${len(params)} AND deleted_at IS NULL',
        *params,
    )
    return result.endswith(" 1")


async def soft_delete(conn: Any, *, id: str, updated_by: str) -> bool:
    result = await conn.execute(
        'UPDATE "02_vault"."11_fct_vault_configs" '
        'SET deleted_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE id = $2 AND deleted_at IS NULL',
        updated_by, id,
    )
    return result.endswith(" 1")


async def set_description(
    conn: Any,
    *,
    config_id: str,
    description: str,
    attr_row_id: str,
) -> None:
    attr_def_id = await _get_description_attr_def_id(conn)
    await conn.execute(
        'INSERT INTO "02_vault"."21_dtl_attrs" '
        '(id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id,
        _CONFIG_ENTITY_TYPE_ID,
        config_id,
        attr_def_id,
        description,
    )


async def clear_description(conn: Any, *, config_id: str) -> None:
    attr_def_id = await _get_description_attr_def_id(conn)
    await conn.execute(
        'DELETE FROM "02_vault"."21_dtl_attrs" '
        'WHERE entity_type_id = $1 AND entity_id = $2 AND attr_def_id = $3',
        _CONFIG_ENTITY_TYPE_ID, config_id, attr_def_id,
    )
