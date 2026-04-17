"""Repository for iam.invites — asyncpg raw SQL."""

from __future__ import annotations

from typing import Any

_TABLE = '"03_iam"."30_fct_user_invites"'
_VIEW  = '"03_iam"."v_invites"'


async def create_invite(
    conn: Any,
    *,
    invite_id: str,
    org_id: str,
    email: str,
    invited_by: str,
    role_id: str | None,
    token_hash: str,
    expires_at: Any,
    created_by: str,
) -> dict:
    row = await conn.fetchrow(
        f"""
        INSERT INTO {_TABLE}
            (id, org_id, email, invited_by, role_id, token_hash, expires_at, created_by)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """,
        invite_id, org_id, email, invited_by, role_id,
        token_hash, expires_at, created_by,
    )
    return dict(row)


async def get_by_id(conn: Any, invite_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"SELECT * FROM {_VIEW} WHERE id = $1",
        invite_id,
    )
    return dict(row) if row else None


async def get_by_token_hash(conn: Any, token_hash: str) -> dict | None:
    row = await conn.fetchrow(
        f"""
        SELECT * FROM {_TABLE}
        WHERE token_hash = $1
          AND status = 1
          AND expires_at > CURRENT_TIMESTAMP
          AND deleted_at IS NULL
        LIMIT 1
        """,
        token_hash,
    )
    return dict(row) if row else None


async def list_pending(conn: Any, *, org_id: str, limit: int, offset: int) -> tuple[list[dict], int]:
    rows = await conn.fetch(
        f"""
        SELECT * FROM {_VIEW}
        WHERE org_id = $1
          AND deleted_at IS NULL
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        org_id, limit, offset,
    )
    total_row = await conn.fetchrow(
        f"""
        SELECT COUNT(*) AS cnt FROM {_TABLE}
        WHERE org_id = $1 AND deleted_at IS NULL
        """,
        org_id,
    )
    total = total_row["cnt"] if total_row else 0
    return [dict(r) for r in rows], total


async def mark_accepted(conn: Any, invite_id: str, updated_by: str) -> None:
    await conn.execute(
        f"""
        UPDATE {_TABLE}
        SET status = 2, accepted_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP, updated_by = $2
        WHERE id = $1
        """,
        invite_id, updated_by,
    )


async def cancel_invite(conn: Any, invite_id: str, updated_by: str) -> None:
    await conn.execute(
        f"""
        UPDATE {_TABLE}
        SET status = 3, deleted_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP, updated_by = $2
        WHERE id = $1
        """,
        invite_id, updated_by,
    )


async def get_pending_by_email_org(conn: Any, email: str, org_id: str) -> dict | None:
    row = await conn.fetchrow(
        f"""
        SELECT * FROM {_TABLE}
        WHERE email = $1 AND org_id = $2 AND status = 1 AND deleted_at IS NULL
        LIMIT 1
        """,
        email, org_id,
    )
    return dict(row) if row else None
