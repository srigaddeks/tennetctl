"""
vault.secrets — asyncpg repository.

Reads go through "02_vault"."v_vault_entries" (latest-non-deleted per (scope, key),
description pivoted, scope code joined). Writes hit fct_vault_entries + dtl_attrs.
Scope is carried through every read / write / uniqueness check.
"""

from __future__ import annotations

from typing import Any

_SECRET_ENTITY_TYPE_ID = 1  # dim_entity_types row for "secret"

_SCOPE_CODE_TO_ID = {"global": 1, "org": 2, "workspace": 3}


def _scope_id(scope: str) -> int:
    try:
        return _SCOPE_CODE_TO_ID[scope]
    except KeyError as e:
        raise ValueError(f"unknown scope {scope!r}") from e


async def _get_description_attr_def_id(conn: Any) -> int:
    """Look up the attr_def_id for (entity_type=secret, code=description)."""
    row = await conn.fetchrow(
        'SELECT id FROM "02_vault"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _SECRET_ENTITY_TYPE_ID,
        "description",
    )
    if row is None:
        raise RuntimeError(
            "attr_def missing: (entity_type_id=1, code='description'). "
            "Re-run vault seed."
        )
    return int(row["id"])


async def get_metadata_by_scope_key(
    conn: Any,
    *,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    key: str,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, key, version, description, scope, org_id, workspace_id, '
        '       is_active, is_test, created_by, updated_by, created_at, updated_at '
        'FROM "02_vault"."v_vault_entries" '
        'WHERE scope = $1 '
        '  AND org_id IS NOT DISTINCT FROM $2 '
        '  AND workspace_id IS NOT DISTINCT FROM $3 '
        '  AND key = $4 AND deleted_at IS NULL',
        scope, org_id, workspace_id, key,
    )
    return dict(row) if row else None


async def list_metadata(
    conn: Any,
    *,
    limit: int,
    offset: int,
    scope: str | None = None,
    org_id: str | None = None,
    workspace_id: str | None = None,
) -> tuple[list[dict], int]:
    """List with optional scope filtering. When scope is None, returns all scopes."""
    where = ["deleted_at IS NULL"]
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
    where_sql = " AND ".join(where)

    total = await conn.fetchval(
        f'SELECT COUNT(*) FROM "02_vault"."v_vault_entries" WHERE {where_sql}',
        *params,
    )

    params_page = [*params, limit, offset]
    limit_idx = len(params_page) - 1
    offset_idx = len(params_page)
    rows = await conn.fetch(
        f'SELECT id, key, version, description, scope, org_id, workspace_id, '
        f'       is_active, is_test, created_by, updated_by, created_at, updated_at '
        f'FROM "02_vault"."v_vault_entries" '
        f'WHERE {where_sql} '
        f'ORDER BY created_at DESC, scope, key '
        f'LIMIT ${limit_idx} OFFSET ${offset_idx}',
        *params_page,
    )
    return [dict(r) for r in rows], int(total or 0)


async def get_latest_envelope(
    conn: Any,
    *,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    key: str,
) -> dict | None:
    row = await conn.fetchrow(
        'SELECT id, version, ciphertext, wrapped_dek, nonce, scope_id '
        'FROM "02_vault"."10_fct_vault_entries" '
        'WHERE scope_id = $1 '
        '  AND org_id IS NOT DISTINCT FROM $2 '
        '  AND workspace_id IS NOT DISTINCT FROM $3 '
        '  AND key = $4 AND deleted_at IS NULL '
        'ORDER BY version DESC LIMIT 1',
        _scope_id(scope), org_id, workspace_id, key,
    )
    return dict(row) if row else None


async def any_row_exists_at_scope(
    conn: Any,
    *,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    key: str,
) -> bool:
    """True iff any row (live or soft-deleted) exists at the exact (scope, key)."""
    row = await conn.fetchrow(
        'SELECT 1 FROM "02_vault"."10_fct_vault_entries" '
        'WHERE scope_id = $1 '
        '  AND org_id IS NOT DISTINCT FROM $2 '
        '  AND workspace_id IS NOT DISTINCT FROM $3 '
        '  AND key = $4 LIMIT 1',
        _scope_id(scope), org_id, workspace_id, key,
    )
    return row is not None


async def insert_secret(
    conn: Any,
    *,
    id: str,
    key: str,
    version: int,
    ciphertext: bytes,
    wrapped_dek: bytes,
    nonce: bytes,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    created_by: str,
    rotated_from_id: str | None = None,
) -> None:
    await conn.execute(
        'INSERT INTO "02_vault"."10_fct_vault_entries" '
        '(id, key, version, ciphertext, wrapped_dek, nonce, '
        ' scope_id, org_id, workspace_id, '
        ' rotated_from_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $11)',
        id, key, version, ciphertext, wrapped_dek, nonce,
        _scope_id(scope), org_id, workspace_id,
        rotated_from_id, created_by,
    )


async def soft_delete_all_versions(
    conn: Any,
    *,
    scope: str,
    org_id: str | None,
    workspace_id: str | None,
    key: str,
    updated_by: str,
) -> int:
    result = await conn.execute(
        'UPDATE "02_vault"."10_fct_vault_entries" '
        'SET deleted_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE scope_id = $2 '
        '  AND org_id IS NOT DISTINCT FROM $3 '
        '  AND workspace_id IS NOT DISTINCT FROM $4 '
        '  AND key = $5 AND deleted_at IS NULL',
        updated_by, _scope_id(scope), org_id, workspace_id, key,
    )
    try:
        return int(result.split()[-1])
    except (IndexError, ValueError):
        return 0


async def set_description(
    conn: Any,
    *,
    secret_id: str,
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
        _SECRET_ENTITY_TYPE_ID,
        secret_id,
        attr_def_id,
        description,
    )
