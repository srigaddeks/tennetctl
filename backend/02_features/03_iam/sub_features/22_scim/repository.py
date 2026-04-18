"""iam.scim — asyncpg repository: SCIM tokens + user externalId attrs."""

from __future__ import annotations

from typing import Any

_SCIM_EXTERNAL_ID_ATTR = 50  # 20_dtl_attr_defs.id


# ── Token management ──────────────────────────────────────────────────────────

async def insert_token(conn: Any, *, id: str, org_id: str, label: str, token_hash: str, created_by: str) -> dict:
    row = await conn.fetchrow(
        'INSERT INTO "03_iam"."32_fct_scim_tokens" (id, org_id, label, token_hash, created_by) '
        'VALUES ($1, $2, $3, $4, $5) RETURNING *',
        id, org_id, label, token_hash, created_by,
    )
    return dict(row)


async def list_tokens(conn: Any, org_id: str) -> list[dict]:
    rows = await conn.fetch(
        'SELECT * FROM "03_iam"."32_fct_scim_tokens" WHERE org_id = $1 AND revoked_at IS NULL ORDER BY created_at',
        org_id,
    )
    return [dict(r) for r in rows]


async def get_token_by_hash(conn: Any, token_hash: str) -> dict | None:
    row = await conn.fetchrow(
        'SELECT * FROM "03_iam"."32_fct_scim_tokens" WHERE token_hash = $1 AND revoked_at IS NULL',
        token_hash,
    )
    return dict(row) if row else None


async def touch_token(conn: Any, token_id: str) -> None:
    await conn.execute(
        'UPDATE "03_iam"."32_fct_scim_tokens" SET last_used_at = CURRENT_TIMESTAMP WHERE id = $1',
        token_id,
    )


async def revoke_token(conn: Any, token_id: str, org_id: str) -> bool:
    result = await conn.execute(
        'UPDATE "03_iam"."32_fct_scim_tokens" SET revoked_at = CURRENT_TIMESTAMP '
        'WHERE id = $1 AND org_id = $2 AND revoked_at IS NULL',
        token_id, org_id,
    )
    return result != "UPDATE 0"


# ── externalId attr ───────────────────────────────────────────────────────────

async def get_external_id(conn: Any, user_id: str) -> str | None:
    row = await conn.fetchrow(
        'SELECT key_text FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = $1 AND attr_def_id = $2',
        user_id, _SCIM_EXTERNAL_ID_ATTR,
    )
    return row["key_text"] if row else None


async def set_external_id(conn: Any, *, attr_row_id: str, user_id: str, external_id: str) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text) '
        'VALUES ($1, 3, $2, $3, $4) '
        'ON CONFLICT (entity_type_id, entity_id, attr_def_id) DO UPDATE SET key_text = EXCLUDED.key_text',
        attr_row_id, user_id, _SCIM_EXTERNAL_ID_ATTR, external_id,
    )


async def get_user_by_external_id(conn: Any, external_id: str) -> dict | None:
    row = await conn.fetchrow(
        '''
        SELECT u.* FROM "03_iam"."v_users" u
        JOIN "03_iam"."21_dtl_attrs" a ON a.entity_id = u.id
        WHERE a.entity_type_id = 3 AND a.attr_def_id = $1 AND a.key_text = $2
          AND u.deleted_at IS NULL
        LIMIT 1
        ''',
        _SCIM_EXTERNAL_ID_ATTR, external_id,
    )
    return dict(row) if row else None


async def enrich_user_with_external_id(conn: Any, user: dict) -> dict:
    ext_id = await get_external_id(conn, user["id"])
    return {**user, "scim_external_id": ext_id}


async def get_group_members(conn: Any, group_id: str) -> list[dict]:
    rows = await conn.fetch(
        '''
        SELECT u.id, u.display_name, u.email
        FROM "03_iam"."v_users" u
        JOIN "03_iam"."43_lnk_user_groups" lug ON lug.user_id = u.id
        WHERE lug.group_id = $1 AND u.deleted_at IS NULL
        ''',
        group_id,
    )
    return [dict(r) for r in rows]


async def add_user_to_group(conn: Any, *, lnk_id: str, user_id: str, group_id: str, org_id: str, created_by: str) -> None:
    await conn.execute(
        'INSERT INTO "03_iam"."43_lnk_user_groups" (id, user_id, group_id, org_id, created_by) '
        'VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING',
        lnk_id, user_id, group_id, org_id, created_by,
    )


async def remove_user_from_group(conn: Any, *, user_id: str, group_id: str) -> None:
    await conn.execute(
        'DELETE FROM "03_iam"."43_lnk_user_groups" WHERE user_id = $1 AND group_id = $2',
        user_id, group_id,
    )
