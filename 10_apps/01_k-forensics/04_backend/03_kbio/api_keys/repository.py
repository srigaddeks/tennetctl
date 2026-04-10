"""kbio API key repository.

Raw SQL operations for API key management. Reads from v_api_keys view,
writes to 16_fct_api_keys + 20_dtl_attrs tables.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

import asyncpg


_ENTITY_TYPE_QUERY = """
    SELECT id FROM "10_kbio"."06_dim_entity_types"
    WHERE code = 'kbio_api_key'
"""

_ATTR_DEF_QUERY = """
    SELECT id, code FROM "10_kbio"."07_dim_attr_defs"
    WHERE entity_type_id = $1
"""


async def list_api_keys(
    conn: asyncpg.Connection,
    *,
    org_id: str,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """List API keys for an org."""
    total = await conn.fetchval(
        'SELECT COUNT(*) FROM "10_kbio".v_api_keys WHERE org_id = $1 AND NOT is_deleted',
        org_id,
    )
    rows = await conn.fetch(
        """
        SELECT * FROM "10_kbio".v_api_keys
        WHERE org_id = $1 AND NOT is_deleted
        ORDER BY created_at DESC
        LIMIT $2 OFFSET $3
        """,
        org_id, limit, offset,
    )
    return [dict(r) for r in rows], total or 0


async def get_api_key(
    conn: asyncpg.Connection,
    key_id: str,
) -> dict[str, Any] | None:
    """Get a single API key by ID."""
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_api_keys WHERE id = $1 AND NOT is_deleted',
        key_id,
    )
    return dict(row) if row else None


async def create_api_key(
    conn: asyncpg.Connection,
    *,
    key_id: str,
    org_id: str,
    workspace_id: str,
    key_prefix: str,
    key_hash: str,
    status_id: int,
    actor_id: str,
    attrs: dict[str, Any],
) -> str:
    """Insert a new API key and its EAV attributes."""
    await conn.execute(
        """
        INSERT INTO "10_kbio"."16_fct_api_keys"
            (id, org_id, workspace_id, key_prefix, key_hash, status_id,
             is_active, created_by, updated_by)
        VALUES ($1, $2, $3, $4, $5, $6, TRUE, $7, $7)
        """,
        key_id, org_id, workspace_id, key_prefix, key_hash,
        status_id, actor_id,
    )

    entity_type_id = await conn.fetchval(_ENTITY_TYPE_QUERY)
    attr_defs = await conn.fetch(_ATTR_DEF_QUERY, entity_type_id)
    code_to_id = {r["code"]: r["id"] for r in attr_defs}

    for code, value in attrs.items():
        if value is None or value == "" or code not in code_to_id:
            continue
        attr_id = str(uuid.uuid4())
        if code == "permissions":
            await conn.execute(
                """
                INSERT INTO "10_kbio"."20_dtl_attrs"
                    (id, entity_type_id, entity_id, attr_def_id, key_jsonb, created_by)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                """,
                attr_id, entity_type_id, key_id, code_to_id[code],
                json.dumps(value), actor_id,
            )
        else:
            await conn.execute(
                """
                INSERT INTO "10_kbio"."20_dtl_attrs"
                    (id, entity_type_id, entity_id, attr_def_id, key_text, created_by)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                attr_id, entity_type_id, key_id, code_to_id[code],
                str(value), actor_id,
            )

    return key_id


async def update_api_key_attrs(
    conn: asyncpg.Connection,
    *,
    key_id: str,
    attrs: dict[str, Any],
    actor_id: str,
) -> None:
    """Update EAV attributes for an API key (upsert pattern)."""
    entity_type_id = await conn.fetchval(_ENTITY_TYPE_QUERY)
    attr_defs = await conn.fetch(_ATTR_DEF_QUERY, entity_type_id)
    code_to_id = {r["code"]: r["id"] for r in attr_defs}

    for code, value in attrs.items():
        if code not in code_to_id:
            continue
        existing = await conn.fetchval(
            """
            SELECT id FROM "10_kbio"."20_dtl_attrs"
            WHERE entity_type_id = $1 AND entity_id = $2 AND attr_def_id = $3
            """,
            entity_type_id, key_id, code_to_id[code],
        )
        if existing:
            if code == "permissions":
                await conn.execute(
                    """
                    UPDATE "10_kbio"."20_dtl_attrs"
                    SET key_jsonb = $1::jsonb, updated_by = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                    """,
                    json.dumps(value), actor_id, existing,
                )
            else:
                await conn.execute(
                    """
                    UPDATE "10_kbio"."20_dtl_attrs"
                    SET key_text = $1, updated_by = $2, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $3
                    """,
                    str(value), actor_id, existing,
                )
        else:
            attr_id = str(uuid.uuid4())
            if code == "permissions":
                await conn.execute(
                    """
                    INSERT INTO "10_kbio"."20_dtl_attrs"
                        (id, entity_type_id, entity_id, attr_def_id, key_jsonb, created_by)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                    """,
                    attr_id, entity_type_id, key_id, code_to_id[code],
                    json.dumps(value), actor_id,
                )
            else:
                await conn.execute(
                    """
                    INSERT INTO "10_kbio"."20_dtl_attrs"
                        (id, entity_type_id, entity_id, attr_def_id, key_text, created_by)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    attr_id, entity_type_id, key_id, code_to_id[code],
                    str(value), actor_id,
                )


async def revoke_api_key(
    conn: asyncpg.Connection,
    key_id: str,
    *,
    revoked_status_id: int,
    actor_id: str,
) -> None:
    """Revoke an API key (set status to revoked, deactivate)."""
    await conn.execute(
        """
        UPDATE "10_kbio"."16_fct_api_keys"
        SET status_id = $1, is_active = FALSE, updated_by = $2
        WHERE id = $3
        """,
        revoked_status_id, actor_id, key_id,
    )


async def soft_delete_api_key(
    conn: asyncpg.Connection,
    key_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete an API key."""
    await conn.execute(
        """
        UPDATE "10_kbio"."16_fct_api_keys"
        SET deleted_at = CURRENT_TIMESTAMP, is_active = FALSE, updated_by = $1
        WHERE id = $2
        """,
        actor_id, key_id,
    )


async def update_last_used(
    conn: asyncpg.Connection,
    key_id: str,
) -> None:
    """Update the last_used_at timestamp for an API key."""
    entity_type_id = await conn.fetchval(_ENTITY_TYPE_QUERY)
    attr_defs = await conn.fetch(_ATTR_DEF_QUERY, entity_type_id)
    code_to_id = {r["code"]: r["id"] for r in attr_defs}

    last_used_def = code_to_id.get("last_used_at")
    if not last_used_def:
        return

    from datetime import datetime, timezone
    now_str = datetime.now(timezone.utc).isoformat()

    existing = await conn.fetchval(
        """
        SELECT id FROM "10_kbio"."20_dtl_attrs"
        WHERE entity_type_id = $1 AND entity_id = $2 AND attr_def_id = $3
        """,
        entity_type_id, key_id, last_used_def,
    )
    if existing:
        await conn.execute(
            """
            UPDATE "10_kbio"."20_dtl_attrs"
            SET key_text = $1, updated_at = CURRENT_TIMESTAMP
            WHERE id = $2
            """,
            now_str, existing,
        )
    else:
        attr_id = str(uuid.uuid4())
        await conn.execute(
            """
            INSERT INTO "10_kbio"."20_dtl_attrs"
                (id, entity_type_id, entity_id, attr_def_id, key_text, created_by)
            VALUES ($1, $2, $3, $4, $5, 'system')
            """,
            attr_id, entity_type_id, key_id, last_used_def, now_str,
        )
