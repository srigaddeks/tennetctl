"""Repository for iam.email_verification tokens."""

from __future__ import annotations

from typing import Any

_TABLE = '"03_iam"."29_fct_iam_email_verifications"'
_USER_ENTITY_TYPE_ID = 3


async def create_token(
    conn: Any,
    *,
    token_id: str,
    user_id: str,
    token_hash: str,
    ttl_at: Any,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_TABLE} (id, user_id, token_hash, ttl_at)
        VALUES ($1, $2, $3, $4)
        RETURNING *
        """,
        token_id, user_id, token_hash, ttl_at,
    )
    return dict(row)


async def get_by_hash(conn: Any, token_hash: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {_TABLE} WHERE token_hash = $1",
        token_hash,
    )
    return dict(row) if row else None


async def mark_consumed(conn: Any, token_id: str) -> None:
    await conn.execute(
        f"UPDATE {_TABLE} SET consumed_at = CURRENT_TIMESTAMP WHERE id = $1",
        token_id,
    )


async def count_recent_by_user(conn: Any, user_id: str, window_minutes: int = 60) -> int:
    """Count tokens created for this user in the last N minutes (rate-limit check)."""
    row = await conn.fetchrow(
        f"""
        SELECT COUNT(*) AS cnt
        FROM {_TABLE}
        WHERE user_id = $1
          AND created_at >= CURRENT_TIMESTAMP - ($2 * INTERVAL '1 minute')
        """,
        user_id, window_minutes,
    )
    return row["cnt"] if row else 0


async def set_email_verified_at(conn: Any, user_id: str, attr_row_id: str) -> None:
    """Upsert email_verified_at EAV attr for the user (stored as ISO-8601 text)."""
    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

    def_id = await conn.fetchval(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" '
        'WHERE entity_type_id = $1 AND code = $2',
        _USER_ENTITY_TYPE_ID, "email_verified_at",
    )
    if def_id is None:
        raise RuntimeError("attr_def missing: (entity_type_id=3, code='email_verified_at')")

    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" '
        '    (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, $2, $3, $4, $5) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) '
        '    DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id,
        _USER_ENTITY_TYPE_ID,
        user_id,
        def_id,
        now_str,
    )


async def get_email_verified_at(conn: Any, user_id: str) -> str | None:
    """Return ISO-8601 text value of email_verified_at for a user, or None."""
    row = await conn.fetchrow(
        """
        SELECT da.key_text
        FROM "03_iam"."21_dtl_attrs" da
        JOIN "03_iam"."20_dtl_attr_defs" ad ON ad.id = da.attr_def_id
        WHERE da.entity_type_id = $1
          AND da.entity_id = $2
          AND ad.code = 'email_verified_at'
        LIMIT 1
        """,
        _USER_ENTITY_TYPE_ID, user_id,
    )
    return row["key_text"] if row else None
