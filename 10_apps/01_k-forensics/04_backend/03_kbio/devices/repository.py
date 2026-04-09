"""kbio devices repository.

Writes to 11_fct_devices, 20_dtl_attrs, and 40_lnk_user_devices.
Reads from v_devices.  No business logic.
"""
from __future__ import annotations

from typing import Any

import asyncpg


async def list_devices_by_user(
    conn: asyncpg.Connection,
    user_hash: str,
    *,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    """Return paginated device rows linked to a user.

    Joins v_devices with 40_lnk_user_devices to scope results to the user.
    Ordered by first_seen_at descending (newest first).
    """
    rows = await conn.fetch(
        """
        SELECT d.*
        FROM "10_kbio".v_devices d
        JOIN "10_kbio"."40_lnk_user_devices" lnk ON lnk.device_id = d.id
        WHERE lnk.user_hash = $1
        ORDER BY d.first_seen_at DESC
        LIMIT $2 OFFSET $3
        """,
        user_hash,
        limit,
        offset,
    )
    return [dict(r) for r in rows]


async def count_devices_by_user(
    conn: asyncpg.Connection, user_hash: str
) -> int:
    """Return the total count of devices linked to a user."""
    row = await conn.fetchrow(
        """
        SELECT COUNT(*) AS cnt
        FROM "10_kbio"."40_lnk_user_devices"
        WHERE user_hash = $1
        """,
        user_hash,
    )
    return int(row["cnt"]) if row else 0


async def get_device_by_id(
    conn: asyncpg.Connection, device_id: str
) -> dict[str, Any] | None:
    """Fetch a single device by its UUID primary key from the resolved view.

    Returns the row as a plain dict, or None if not found.
    """
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_devices WHERE id = $1',
        device_id,
    )
    return dict(row) if row else None


async def get_device_by_uuid(
    conn: asyncpg.Connection, device_uuid: str
) -> dict[str, Any] | None:
    """Fetch a single device by its external device_uuid from the resolved view.

    Returns the row as a plain dict, or None if not found.
    """
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_devices WHERE device_uuid = $1',
        device_uuid,
    )
    return dict(row) if row else None


async def upsert_device(
    conn: asyncpg.Connection,
    *,
    device_id: str,
    device_uuid: str,
    user_hash: str,
    actor_id: str,
) -> dict[str, Any]:
    """Insert or update a device row in 11_fct_devices.

    Uses INSERT … ON CONFLICT (device_uuid) DO UPDATE for idempotency.
    Returns the id and device_uuid of the upserted row.
    """
    row = await conn.fetchrow(
        """
        INSERT INTO "10_kbio"."11_fct_devices"
            (id, device_uuid, is_active, is_test,
             created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, TRUE, FALSE, $3, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (device_uuid) DO UPDATE
            SET updated_by = EXCLUDED.updated_by,
                updated_at = CURRENT_TIMESTAMP
        RETURNING id, device_uuid
        """,
        device_id,
        device_uuid,
        actor_id,
    )
    return dict(row)


async def upsert_device_attr(
    conn: asyncpg.Connection,
    *,
    device_id: str,
    attr_code: str,
    value: str,
    actor_id: str,
) -> None:
    """Upsert a single EAV attribute for a device.

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
            (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_device'),
            $2,
            (SELECT id FROM "10_kbio"."07_dim_attr_defs"
             WHERE entity_type_id = (
                 SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_device'
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
        device_id,
        attr_code,
        value,
        actor_id,
    )


async def link_user_device(
    conn: asyncpg.Connection,
    *,
    user_hash: str,
    device_id: str,
    actor_id: str,
) -> None:
    """Create a user↔device association in 40_lnk_user_devices.

    Silently ignores duplicate links (ON CONFLICT DO NOTHING).
    """
    link_id = str(__import__("uuid").uuid4())
    await conn.execute(
        """
        INSERT INTO "10_kbio"."40_lnk_user_devices"
            (id, user_hash, device_id, created_by, created_at)
        VALUES ($1, $2, $3, $4, CURRENT_TIMESTAMP)
        ON CONFLICT (user_hash, device_id) DO NOTHING
        """,
        link_id,
        user_hash,
        device_id,
        actor_id,
    )
