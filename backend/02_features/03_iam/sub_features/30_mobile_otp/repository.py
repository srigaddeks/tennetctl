"""IAM mobile-OTP — repository (asyncpg raw SQL)."""

from __future__ import annotations

from datetime import datetime
from importlib import import_module
from typing import Any

_core_id = import_module("backend.01_core.id")

_TABLE = '"03_iam"."24_fct_iam_mobile_otp_codes"'
_USERS_TABLE = '"03_iam"."12_fct_users"'
_DTL_ATTRS = '"03_iam"."21_dtl_attrs"'
_ATTR_DEFS = '"03_iam"."20_dtl_attr_defs"'
_DIM_ENTITY = '"03_iam"."01_dim_entity_types"'


async def insert_code(
    conn: Any,
    *,
    code_id: str,
    user_id: str | None,
    phone_e164: str,
    code_hash: str,
    expires_at: datetime,
) -> None:
    await conn.execute(
        f"""
        INSERT INTO {_TABLE}
            (id, user_id, phone_e164, code_hash, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        """,
        code_id, user_id, phone_e164, code_hash, expires_at,
    )


async def latest_unconsumed(conn: Any, *, phone_e164: str) -> dict[str, Any] | None:
    sql = f"""
        SELECT id, user_id, phone_e164, code_hash, attempts, expires_at,
               consumed_at, created_at
        FROM {_TABLE}
        WHERE phone_e164 = $1 AND consumed_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    """
    row = await conn.fetchrow(sql, phone_e164)
    return dict(row) if row else None


async def increment_attempts(conn: Any, *, code_id: str) -> int:
    sql = f"""
        UPDATE {_TABLE}
        SET attempts = attempts + 1
        WHERE id = $1
        RETURNING attempts
    """
    return int(await conn.fetchval(sql, code_id) or 0)


async def consume(conn: Any, *, code_id: str, user_id: str) -> None:
    await conn.execute(
        f"""
        UPDATE {_TABLE}
        SET consumed_at = CURRENT_TIMESTAMP, user_id = $2
        WHERE id = $1 AND consumed_at IS NULL
        """,
        code_id, user_id,
    )


async def find_user_by_phone(
    conn: Any, *, phone_e164: str,
) -> dict[str, Any] | None:
    """Find an active (non-deleted) user with the given phone attr."""
    sql = f"""
        SELECT u.id, u.account_type_id, u.is_active
        FROM {_USERS_TABLE} u
        JOIN {_DTL_ATTRS} a ON a.entity_id = u.id
        JOIN {_ATTR_DEFS} d ON d.id = a.attr_def_id
        JOIN {_DIM_ENTITY} e ON e.id = d.entity_type_id
        WHERE e.code = 'user'
          AND d.code = 'phone'
          AND a.key_text = $1
          AND u.deleted_at IS NULL
        ORDER BY u.created_at ASC
        LIMIT 1
    """
    row = await conn.fetchrow(sql, phone_e164)
    return dict(row) if row else None


async def attr_def_id(conn: Any, *, code: str) -> int | None:
    sql = f"""
        SELECT d.id
        FROM {_ATTR_DEFS} d
        JOIN {_DIM_ENTITY} e ON e.id = d.entity_type_id
        WHERE e.code = 'user' AND d.code = $1
    """
    return await conn.fetchval(sql, code)


async def account_type_id(conn: Any, *, code: str) -> int | None:
    sql = '''SELECT id FROM "03_iam"."02_dim_account_types" WHERE code = $1'''
    return await conn.fetchval(sql, code)


async def insert_user_with_attrs(
    conn: Any,
    *,
    user_id: str,
    account_type_id: int,
    phone_e164: str,
    display_name: str | None,
    actor_id: str,
) -> None:
    """Create a fct_user + dtl_attrs entries for phone (+ optional display_name)
    in a single transaction. Caller wraps in BEGIN/COMMIT or runs inside
    one (asyncpg pool conn is auto-tx by default)."""
    await conn.execute(
        f"""
        INSERT INTO {_USERS_TABLE}
            (id, account_type_id, is_active, is_test, created_by, updated_by)
        VALUES ($1, $2, TRUE, FALSE, $3, $3)
        """,
        user_id, account_type_id, actor_id,
    )
    phone_def = await attr_def_id(conn, code="phone")
    if phone_def is None:
        raise RuntimeError("phone attr_def missing — migration 096 not applied")
    await conn.execute(
        f"""
        INSERT INTO {_DTL_ATTRS} (id, entity_type_id, entity_id, attr_def_id, key_text)
        VALUES ($1, 3, $2, $3, $4)
        """,
        _core_id.uuid7(), user_id, phone_def, phone_e164,
    )
    if display_name:
        dn_def = await attr_def_id(conn, code="display_name")
        if dn_def is not None:
            await conn.execute(
                f"""
                INSERT INTO {_DTL_ATTRS} (id, entity_type_id, entity_id, attr_def_id, key_text)
                VALUES ($1, 3, $2, $3, $4)
                """,
                _core_id.uuid7(), user_id, dn_def, display_name,
            )
