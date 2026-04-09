"""kbio trust repository.

Writes to 13_fct_trusted_entities and 20_dtl_attrs (EAV).
Reads from v_trusted_entities.  No business logic.
"""
from __future__ import annotations

from typing import Any

import asyncpg


async def get_trust_profile(
    conn: asyncpg.Connection, user_hash: str
) -> list[dict[str, Any]]:
    """Return all active trusted entity rows for a user from the resolved view.

    Includes all entity types (device, ip_address, location, network).
    Ordered by created_at descending.
    """
    rows = await conn.fetch(
        """
        SELECT * FROM "10_kbio".v_trusted_entities
        WHERE user_hash = $1
        ORDER BY created_at DESC
        """,
        user_hash,
    )
    return [dict(r) for r in rows]


async def create_trusted_entity(
    conn: asyncpg.Connection,
    *,
    entity_id: str,
    user_hash: str,
    entity_type_id: str,
    actor_id: str,
) -> None:
    """Insert a new row into 13_fct_trusted_entities.

    entity_type_id is the UUID of the matching dim_entity_type row.
    actor_id is written to both created_by and updated_by.
    """
    await conn.execute(
        """
        INSERT INTO "10_kbio"."13_fct_trusted_entities"
            (id, user_hash, entity_type_id, is_active, is_test,
             created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, TRUE, FALSE, $4, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
        """,
        entity_id,
        user_hash,
        entity_type_id,
        actor_id,
    )


async def upsert_trust_attr(
    conn: asyncpg.Connection,
    *,
    entity_id: str,
    attr_code: str,
    value: str,
    actor_id: str,
) -> None:
    """Upsert a single EAV attribute for a trusted entity.

    entity_type_id and attr_def_id are resolved via subselects.
    Value is stored in key_text.

    Raises:
        asyncpg.PostgresError — if attr_code is not registered.
    """
    attr_id = str(__import__("uuid").uuid4())
    await conn.execute(
        """
        INSERT INTO "10_kbio"."20_dtl_attrs"
            (id, entity_type_id, entity_id, attr_def_id, key_text,
             created_by, created_at)
        VALUES (
            $1,
            (SELECT id FROM "10_kbio"."06_dim_entity_types"
             WHERE code = 'kbio_trusted_entity'),
            $2,
            (SELECT id FROM "10_kbio"."07_dim_attr_defs"
             WHERE entity_type_id = (
                 SELECT id FROM "10_kbio"."06_dim_entity_types"
                 WHERE code = 'kbio_trusted_entity'
             )
             AND code = $3),
            $4,
            $5,
            CURRENT_TIMESTAMP
        )
        ON CONFLICT (entity_id, attr_def_id)
            DO UPDATE SET key_text = EXCLUDED.key_text,
                          updated_at = CURRENT_TIMESTAMP
        """,
        attr_id,
        entity_id,
        attr_code,
        value,
        actor_id,
    )


async def deactivate_trusted_entity(
    conn: asyncpg.Connection,
    entity_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete a trusted entity by setting deleted_at to CURRENT_TIMESTAMP.

    Also clears is_active and records the actor.
    """
    await conn.execute(
        """
        UPDATE "10_kbio"."13_fct_trusted_entities"
        SET deleted_at  = CURRENT_TIMESTAMP,
            is_active   = FALSE,
            updated_by  = $2,
            updated_at  = CURRENT_TIMESTAMP
        WHERE id = $1
          AND deleted_at IS NULL
        """,
        entity_id,
        actor_id,
    )


async def get_trusted_entity(
    conn: asyncpg.Connection, entity_id: str
) -> dict[str, Any] | None:
    """Fetch a single trusted entity by ID from the resolved view.

    Returns the row as a plain dict, or None if not found.
    """
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_trusted_entities WHERE id = $1',
        entity_id,
    )
    return dict(row) if row else None


async def is_entity_trusted(
    conn: asyncpg.Connection,
    user_hash: str,
    entity_type_code: str,
    entity_value: str,
) -> bool:
    """Check whether a specific entity value is currently trusted for a user.

    Uses the view so only active, non-expired records are considered.
    Returns True if at least one matching active record exists.
    """
    row = await conn.fetchrow(
        """
        SELECT 1
        FROM "10_kbio".v_trusted_entities
        WHERE user_hash = $1
          AND entity_type = $2
          AND entity_value = $3
          AND is_active = TRUE
          AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        LIMIT 1
        """,
        user_hash,
        entity_type_code,
        entity_value,
    )
    return row is not None
