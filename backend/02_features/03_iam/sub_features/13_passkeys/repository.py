"""Repository for iam.passkeys (WebAuthn challenges + credentials)."""

from __future__ import annotations

from typing import Any

_CHALLENGE_TABLE = '"03_iam"."25_fct_iam_passkey_challenges"'
_CRED_TABLE      = '"03_iam"."26_fct_iam_passkey_credentials"'


# ─── Challenges ───────────────────────────────────────────────────────────────

async def create_challenge(
    conn: Any,
    *,
    challenge_id: str,
    user_id: str | None,
    challenge_b64: str,
    purpose: str,
    expires_at: Any,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_CHALLENGE_TABLE} (id, user_id, challenge, purpose, expires_at)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
        """,
        challenge_id, user_id, challenge_b64, purpose, expires_at,
    )
    return dict(row)


async def get_challenge(conn: Any, challenge_id: str, purpose: str) -> dict | None:
    row = await conn.fetchrow(
        f"""
        SELECT * FROM {_CHALLENGE_TABLE}
        WHERE id = $1 AND purpose = $2
          AND consumed_at IS NULL
          AND expires_at > CURRENT_TIMESTAMP
        """,
        challenge_id, purpose,
    )
    return dict(row) if row else None


async def mark_challenge_consumed(conn: Any, challenge_id: str) -> None:
    await conn.execute(
        f"UPDATE {_CHALLENGE_TABLE} SET consumed_at = CURRENT_TIMESTAMP WHERE id = $1",
        challenge_id,
    )


# ─── Credentials ──────────────────────────────────────────────────────────────

async def create_credential(
    conn: Any,
    *,
    cred_id: str,
    user_id: str,
    credential_id_b64: str,
    public_key_b64: str,
    aaguid: str,
    sign_count: int,
    device_name: str,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_CRED_TABLE} (id, user_id, credential_id, public_key, aaguid, sign_count, device_name)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        RETURNING *
        """,
        cred_id, user_id, credential_id_b64, public_key_b64, aaguid, sign_count, device_name,
    )
    return dict(row)


async def get_credential_by_raw_id(conn: Any, credential_id_b64: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {_CRED_TABLE} WHERE credential_id = $1 AND deleted_at IS NULL",
        credential_id_b64,
    )
    return dict(row) if row else None


async def get_credentials_for_user(conn: Any, user_id: str) -> list[dict]:
    rows = await conn.fetch(
        f"""
        SELECT * FROM {_CRED_TABLE}
        WHERE user_id = $1 AND deleted_at IS NULL
        ORDER BY created_at DESC
        """,
        user_id,
    )
    return [dict(r) for r in rows]


async def update_sign_count(conn: Any, cred_id: str, new_sign_count: int) -> None:
    await conn.execute(
        f"UPDATE {_CRED_TABLE} SET sign_count = $1, last_used_at = CURRENT_TIMESTAMP WHERE id = $2",
        new_sign_count, cred_id,
    )


async def delete_credential(conn: Any, cred_id: str, user_id: str) -> None:
    await conn.execute(
        f"UPDATE {_CRED_TABLE} SET deleted_at = CURRENT_TIMESTAMP WHERE id = $1 AND user_id = $2",
        cred_id, user_id,
    )


async def list_credentials(conn: Any, user_id: str) -> list[dict]:
    return await get_credentials_for_user(conn, user_id)
