"""
vault.secrets — asyncpg repository.

Reads go through "02_vault"."v_vault_entries" (latest-non-deleted version per key,
description pivoted from dtl_attrs). Writes hit raw fct_vault_entries + dtl_attrs.
No business logic; callers (service) own conflict resolution + audit emission.
"""

from __future__ import annotations

from typing import Any

_SECRET_ENTITY_TYPE_ID = 1  # dim_entity_types row for "secret"


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
            "Re-run vault seed (02vault_20_dtl_attr_defs.yaml)."
        )
    return int(row["id"])


async def get_metadata_by_key(conn: Any, key: str) -> dict | None:
    """Return v_vault_entries row (excludes soft-deleted) or None."""
    row = await conn.fetchrow(
        'SELECT id, key, version, description, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "02_vault"."v_vault_entries" '
        'WHERE key = $1 AND deleted_at IS NULL',
        key,
    )
    return dict(row) if row else None


async def list_metadata(
    conn: Any,
    *,
    limit: int,
    offset: int,
) -> tuple[list[dict], int]:
    """Paginated list of vault entries (latest version per key, soft-deleted excluded)."""
    total = await conn.fetchval(
        'SELECT COUNT(*) FROM "02_vault"."v_vault_entries" '
        'WHERE deleted_at IS NULL',
    )
    rows = await conn.fetch(
        'SELECT id, key, version, description, is_active, is_test, '
        '       created_by, updated_by, created_at, updated_at '
        'FROM "02_vault"."v_vault_entries" '
        'WHERE deleted_at IS NULL '
        'ORDER BY created_at DESC, key ASC '
        'LIMIT $1 OFFSET $2',
        limit,
        offset,
    )
    return [dict(r) for r in rows], int(total or 0)


async def get_latest_envelope(conn: Any, key: str) -> dict | None:
    """Load the latest non-deleted encrypted envelope for `key`. Returns dict with
    id / version / ciphertext / wrapped_dek / nonce, or None."""
    row = await conn.fetchrow(
        'SELECT id, version, ciphertext, wrapped_dek, nonce '
        'FROM "02_vault"."10_fct_vault_entries" '
        'WHERE key = $1 AND deleted_at IS NULL '
        'ORDER BY version DESC LIMIT 1',
        key,
    )
    return dict(row) if row else None


async def any_row_exists(conn: Any, key: str) -> bool:
    """True iff any row for `key` exists (including soft-deleted) — used to refuse key reuse."""
    row = await conn.fetchrow(
        'SELECT 1 FROM "02_vault"."10_fct_vault_entries" WHERE key = $1 LIMIT 1',
        key,
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
    created_by: str,
    rotated_from_id: str | None = None,
) -> None:
    """Insert a new row into fct_vault_entries. Caller owns the transaction + conflict handling."""
    await conn.execute(
        'INSERT INTO "02_vault"."10_fct_vault_entries" '
        '(id, key, version, ciphertext, wrapped_dek, nonce, '
        ' rotated_from_id, created_by, updated_by) '
        'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)',
        id,
        key,
        version,
        ciphertext,
        wrapped_dek,
        nonce,
        rotated_from_id,
        created_by,
    )


async def soft_delete_all_versions(conn: Any, key: str, updated_by: str) -> int:
    """Soft-delete every live version of a key. Returns number of rows affected."""
    result = await conn.execute(
        'UPDATE "02_vault"."10_fct_vault_entries" '
        'SET deleted_at = CURRENT_TIMESTAMP, '
        '    updated_by = $1, '
        '    updated_at = CURRENT_TIMESTAMP '
        'WHERE key = $2 AND deleted_at IS NULL',
        updated_by,
        key,
    )
    # asyncpg execute returns "UPDATE N"
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
    """Upsert the description EAV row for a secret."""
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
