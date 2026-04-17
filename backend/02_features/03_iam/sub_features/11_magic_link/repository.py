"""Repository for iam.magic_link_tokens."""

from __future__ import annotations

from typing import Any

_TABLE = '"03_iam"."19_fct_iam_magic_link_tokens"'


async def create_token(
    conn: Any,
    *,
    token_id: str,
    user_id: str,
    email: str,
    token_hash: str,
    expires_at: Any,
    ip_address: str | None = None,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_TABLE}
            (id, user_id, email, token_hash, expires_at, ip_address)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        token_id, user_id, email, token_hash, expires_at, ip_address,
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


async def count_recent_by_email(conn: Any, email: str, window_minutes: int = 15) -> int:
    """Count tokens created for this email in the last N minutes (rate-limit check)."""
    row = await conn.fetchrow(
        f"""
        SELECT COUNT(*) AS cnt
        FROM {_TABLE}
        WHERE email = $1
          AND created_at >= CURRENT_TIMESTAMP - ($2 * INTERVAL '1 minute')
        """,
        email, window_minutes,
    )
    return row["cnt"] if row else 0
