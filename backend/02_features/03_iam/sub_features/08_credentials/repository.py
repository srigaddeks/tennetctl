"""
iam.credentials — asyncpg repository.

Reads + writes "03_iam"."22_dtl_credentials" — a fixed-schema dtl table holding
exactly one argon2id password hash per user. No view layer; the password_hash
column is sensitive and must never appear in v_users.

Also manages the failed-auth-attempts table (Plan 20-03) for account lockout,
and lockout state stored as dtl_attrs on the user entity.
"""

from __future__ import annotations

import datetime as dt
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")

_ATTEMPTS_TABLE = '"03_iam"."23_fct_failed_auth_attempts"'
_ATTRS_TABLE = '"03_iam"."21_dtl_attrs"'
_ATTR_DEFS_TABLE = '"03_iam"."20_dtl_attr_defs"'


async def get_hash(conn: Any, user_id: str) -> str | None:
    return await conn.fetchval(
        'SELECT password_hash FROM "03_iam"."22_dtl_credentials" WHERE user_id = $1',
        user_id,
    )


async def upsert_hash(conn: Any, *, user_id: str, password_hash: str) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."22_dtl_credentials" (user_id, password_hash) '
        'VALUES ($1, $2) '
        'ON CONFLICT (user_id) DO UPDATE '
        '   SET password_hash = EXCLUDED.password_hash, '
        '       updated_at = CURRENT_TIMESTAMP',
        user_id,
        password_hash,
    )


async def delete_hash(conn: Any, user_id: str) -> bool:
    result = await conn.execute(
        'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = $1',
        user_id,
    )
    return result.endswith(" 1")


# ── Lockout: failed-attempt tracking ──────────────────────────────────────────

async def record_failed_attempt(
    conn: Any, *, email: str, user_id: str | None, source_ip: str | None,
) -> None:
    attempt_id = _core_id.uuid7()
    await conn.execute(
        f'INSERT INTO {_ATTEMPTS_TABLE} (id, email, user_id, source_ip) '
        'VALUES ($1, $2, $3, $4::inet)',
        attempt_id, email, user_id, source_ip,
    )


async def count_failed_in_window(conn: Any, *, email: str, window_seconds: int) -> int:
    cutoff = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None) - dt.timedelta(seconds=window_seconds)
    return await conn.fetchval(
        f'SELECT COUNT(*) FROM {_ATTEMPTS_TABLE} '
        'WHERE email = $1 AND attempted_at >= $2',
        email, cutoff,
    )


# ── Lockout: dtl_attr lock state ───────────────────────────────────────────────
# lockout_until is stored in 21_dtl_attrs (key_text = ISO timestamp).
# attr_def_id is SMALLINT (auto-identity); we register on first use.

async def _ensure_lockout_attr_def(conn: Any) -> int:
    """Return the SMALLINT attr_def id for 'lockout_until' on user entities.
    Registers the def if it doesn't exist (idempotent INSERT).
    """
    row = await conn.fetchrow(
        f'SELECT id FROM {_ATTR_DEFS_TABLE} WHERE code = $1 AND entity_type_id = 3',
        "lockout_until",
    )
    if row is not None:
        return row["id"]
    await conn.execute(
        f'INSERT INTO {_ATTR_DEFS_TABLE} '
        '(entity_type_id, code, value_type, label, description) '
        'VALUES (3, $1, $2, $3, $4) '
        'ON CONFLICT (entity_type_id, code) DO NOTHING',
        "lockout_until", "text",
        "Lockout Until",
        "ISO timestamp until which signin is blocked for this user.",
    )
    row = await conn.fetchrow(
        f'SELECT id FROM {_ATTR_DEFS_TABLE} WHERE code = $1 AND entity_type_id = 3',
        "lockout_until",
    )
    return row["id"]


async def get_lockout_until(conn: Any, *, user_id: str) -> dt.datetime | None:
    """Return lockout.until timestamp (UTC naive) if the user is locked, else None."""
    attr_def_id = await _ensure_lockout_attr_def(conn)
    row = await conn.fetchrow(
        f'SELECT key_text FROM {_ATTRS_TABLE} '
        'WHERE entity_type_id = 3 AND entity_id = $1 AND attr_def_id = $2',
        user_id, attr_def_id,
    )
    if row is None or not row["key_text"]:
        return None
    try:
        return dt.datetime.fromisoformat(row["key_text"])
    except (ValueError, TypeError):
        return None


async def set_lockout_until(conn: Any, *, user_id: str, until_ts: dt.datetime) -> None:
    """Upsert the lockout_until attr on the user."""
    attr_def_id = await _ensure_lockout_attr_def(conn)
    row_id = _core_id.uuid7()
    await conn.execute(
        f'INSERT INTO {_ATTRS_TABLE} '
        '(id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, 3, $2, $3, $4) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        'DO UPDATE SET key_text = EXCLUDED.key_text',
        row_id, user_id, attr_def_id, until_ts.isoformat(),
    )


async def clear_lockout(conn: Any, *, user_id: str) -> None:
    """Remove the lockout_until attr from the user."""
    attr_def_id = await _ensure_lockout_attr_def(conn)
    await conn.execute(
        f'DELETE FROM {_ATTRS_TABLE} '
        'WHERE entity_type_id = 3 AND entity_id = $1 AND attr_def_id = $2',
        user_id, attr_def_id,
    )
