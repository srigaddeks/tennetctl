"""kbio challenge repository.

Writes to 14_fct_challenges and 20_dtl_attrs (EAV).
Reads from v_challenges.  No business logic.
"""
from __future__ import annotations

from typing import Any

import asyncpg


async def create_challenge(
    conn: asyncpg.Connection,
    *,
    challenge_id: str,
    sdk_session_id: str,
    user_hash: str,
    actor_id: str,
) -> None:
    """Insert a new challenge row into 14_fct_challenges.

    The challenge starts as active (is_active=TRUE) and not used.
    actor_id is written to both created_by and updated_by.
    """
    await conn.execute(
        """
        INSERT INTO "10_kbio"."14_fct_challenges"
            (id, sdk_session_id, user_hash, is_active, is_test,
             created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, TRUE, FALSE, $4, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (id) DO NOTHING
        """,
        challenge_id,
        sdk_session_id,
        user_hash,
        actor_id,
    )


async def upsert_challenge_attr(
    conn: asyncpg.Connection,
    *,
    challenge_id: str,
    attr_code: str,
    value: str,
    actor_id: str,
) -> None:
    """Upsert a single EAV attribute for a challenge.

    The attr_def_id and entity_type_id are resolved via subselects so no
    hardcoded integer IDs are needed.  value is stored in key_text.

    Raises:
        asyncpg.PostgresError — if attr_code is not in dim_attr_defs.
    """
    attr_id = str(__import__("uuid").uuid4())
    await conn.execute(
        """
        INSERT INTO "10_kbio"."20_dtl_attrs"
            (id, entity_type_id, entity_id, attr_def_id, key_text,
             created_by, created_at)
        VALUES (
            $1,
            (SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_challenge'),
            $2,
            (SELECT id FROM "10_kbio"."07_dim_attr_defs"
             WHERE entity_type_id = (
                 SELECT id FROM "10_kbio"."06_dim_entity_types" WHERE code = 'kbio_challenge'
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
        challenge_id,
        attr_code,
        value,
        actor_id,
    )


async def get_challenge(
    conn: asyncpg.Connection, challenge_id: str
) -> dict[str, Any] | None:
    """Fetch a challenge row from the resolved view.

    Returns the row as a plain dict, or None if it does not exist.
    """
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_challenges WHERE id = $1',
        challenge_id,
    )
    return dict(row) if row else None
