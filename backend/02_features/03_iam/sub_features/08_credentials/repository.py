"""
iam.credentials — asyncpg repository.

Reads + writes "03_iam"."22_dtl_credentials" — a fixed-schema dtl table holding
exactly one argon2id password hash per user. No view layer; the password_hash
column is sensitive and must never appear in v_users.
"""

from __future__ import annotations

from typing import Any


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
