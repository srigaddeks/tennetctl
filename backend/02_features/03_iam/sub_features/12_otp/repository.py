"""Repository for iam.otp (email OTP codes + TOTP credentials + backup codes)."""

from __future__ import annotations

from typing import Any

_OTP_TABLE     = '"03_iam"."23_fct_iam_otp_codes"'
_TOTP_TABLE    = '"03_iam"."24_fct_iam_totp_credentials"'
_BACKUP_TABLE  = '"03_iam"."28_fct_totp_backup_codes"'


# ─── Email OTP ────────────────────────────────────────────────────────────────

async def create_otp_code(
    conn: Any,
    *,
    code_id: str,
    user_id: str,
    email: str,
    code_hash: str,
    expires_at: Any,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_OTP_TABLE} (id, user_id, email, code_hash, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        code_id, user_id, email, code_hash, expires_at,
    )
    return dict(row)


async def get_active_otp(conn: Any, email: str) -> dict | None:
    """Return most-recent unconsumed, unexpired OTP for email."""
    row = await conn.fetchrow(
        f"""
        SELECT * FROM {_OTP_TABLE}
        WHERE email = $1
          AND consumed_at IS NULL
          AND expires_at > CURRENT_TIMESTAMP
        ORDER BY created_at DESC
        LIMIT 1
        """,
        email,
    )
    return dict(row) if row else None


async def increment_otp_attempts(conn: Any, otp_id: str) -> int:
    row = await conn.fetchrow(
        f"""
        UPDATE {_OTP_TABLE}
        SET attempts = attempts + 1
        WHERE id = $1
        RETURNING attempts
        """,
        otp_id,
    )
    return row["attempts"] if row else 0


async def mark_otp_consumed(conn: Any, otp_id: str) -> None:
    await conn.execute(
        f"UPDATE {_OTP_TABLE} SET consumed_at = CURRENT_TIMESTAMP WHERE id = $1",
        otp_id,
    )


async def count_recent_otp_by_email(conn: Any, email: str, window_minutes: int = 15) -> int:
    row = await conn.fetchrow(
        f"""
        SELECT COUNT(*) AS cnt FROM {_OTP_TABLE}
        WHERE email = $1
          AND created_at >= CURRENT_TIMESTAMP - ($2 * INTERVAL '1 minute')
        """,
        email, window_minutes,
    )
    return row["cnt"] if row else 0


# ─── TOTP credentials ─────────────────────────────────────────────────────────

async def create_totp_credential(
    conn: Any,
    *,
    cred_id: str,
    user_id: str,
    device_name: str,
    ciphertext: str,
    dek: str,
    nonce: str,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_TOTP_TABLE} (id, user_id, device_name, secret_ciphertext, secret_dek, secret_nonce)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING *
        """,
        cred_id, user_id, device_name, ciphertext, dek, nonce,
    )
    return dict(row)


async def get_totp_credential(conn: Any, cred_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {_TOTP_TABLE} WHERE id = $1 AND deleted_at IS NULL",
        cred_id,
    )
    return dict(row) if row else None


async def list_totp_credentials(conn: Any, user_id: str) -> list[dict]:
    rows = await conn.fetch(
        f"""
        SELECT * FROM {_TOTP_TABLE}
        WHERE user_id = $1 AND deleted_at IS NULL
        ORDER BY created_at DESC
        """,
        user_id,
    )
    return [dict(r) for r in rows]


async def mark_totp_used(conn: Any, cred_id: str) -> None:
    await conn.execute(
        f"UPDATE {_TOTP_TABLE} SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1",
        cred_id,
    )


async def delete_totp_credential(conn: Any, cred_id: str, user_id: str) -> None:
    await conn.execute(
        f"UPDATE {_TOTP_TABLE} SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND user_id = $2",
        cred_id, user_id,
    )


# ─── TOTP backup codes ────────────────────────────────────────────────────────

async def insert_backup_code(conn: Any, *, code_id: str, user_id: str, code_hash: str) -> None:
    await conn.execute(
        f"INSERT INTO {_BACKUP_TABLE} (id, user_id, code_hash) VALUES ($1, $2, $3)",
        code_id, user_id, code_hash,
    )


async def list_active_backup_codes(conn: Any, user_id: str) -> list[dict]:
    rows = await conn.fetch(
        f"SELECT * FROM {_BACKUP_TABLE} WHERE user_id = $1 AND consumed_at IS NULL",
        user_id,
    )
    return [dict(r) for r in rows]


async def get_backup_code_by_hash(conn: Any, user_id: str, code_hash: str) -> dict | None:
    row = await conn.fetchrow(
        f"""
        SELECT * FROM {_BACKUP_TABLE}
        WHERE user_id = $1 AND code_hash = $2 AND consumed_at IS NULL
        FOR UPDATE
        """,
        user_id, code_hash,
    )
    return dict(row) if row else None


async def mark_backup_code_consumed(conn: Any, code_id: str) -> None:
    await conn.execute(
        f"UPDATE {_BACKUP_TABLE} SET consumed_at = CURRENT_TIMESTAMP WHERE id = $1",
        code_id,
    )


async def delete_all_backup_codes(conn: Any, user_id: str) -> None:
    await conn.execute(
        f"DELETE FROM {_BACKUP_TABLE} WHERE user_id = $1",
        user_id,
    )
