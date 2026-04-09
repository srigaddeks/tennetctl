"""kbio profile repository.

Reads from v_user_profiles view. Writes to 12_fct_user_profiles and
20_dtl_attrs (EAV pattern). No business logic.
"""
from __future__ import annotations

from typing import Any

import asyncpg


async def get_profile(
    conn: asyncpg.Connection, user_hash: str
) -> dict[str, Any] | None:
    """Fetch a user behavioral profile from the resolved view.

    Returns the row as a plain dict, or None if the profile does not exist.
    """
    row = await conn.fetchrow(
        'SELECT * FROM "10_kbio".v_user_profiles WHERE user_hash = $1',
        user_hash,
    )
    return dict(row) if row else None


async def upsert_profile(
    conn: asyncpg.Connection,
    *,
    user_hash: str,
    baseline_quality_id: int,
    actor_id: str,
) -> dict[str, Any]:
    """Create or update the fct row for a user profile.

    Uses INSERT ... ON CONFLICT (user_hash) DO UPDATE to ensure idempotency.
    Returns the updated row (id + user_hash minimum).
    """
    row = await conn.fetchrow(
        """INSERT INTO "10_kbio".12_fct_user_profiles
               (id, user_hash, baseline_quality_id, is_active, is_test,
                created_by, updated_by, created_at, updated_at)
           VALUES (
               gen_random_uuid(), $1, $2, TRUE, FALSE,
               $3, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
           )
           ON CONFLICT (user_hash) DO UPDATE
               SET baseline_quality_id = EXCLUDED.baseline_quality_id,
                   updated_by          = EXCLUDED.updated_by,
                   updated_at          = CURRENT_TIMESTAMP
           RETURNING id, user_hash, baseline_quality_id, created_at, updated_at""",
        user_hash,
        baseline_quality_id,
        actor_id,
    )
    return dict(row)


async def upsert_profile_attr(
    conn: asyncpg.Connection,
    *,
    profile_id: str,
    attr_code: str,
    value: Any,
    actor_id: str,
) -> None:
    """Upsert a single EAV attribute for a user profile.

    Resolves the attr_def_id from attr_code. Value is stored as key_jsonb
    for complex types and key_text for plain strings/numbers.
    Raises asyncpg.PostgresError if attr_code is not registered in dim_attr_defs.
    """
    attr_def_row = await conn.fetchrow(
        """SELECT id FROM "10_kbio".dim_attr_defs
           WHERE code = $1 AND entity_type_code = 'user_profile' LIMIT 1""",
        attr_code,
    )
    if attr_def_row is None:
        raise ValueError(f"Unknown attr_code '{attr_code}' for entity_type user_profile")

    attr_def_id = attr_def_row["id"]

    # Store numeric scalars as key_jsonb (handles float/int uniformly).
    await conn.execute(
        """INSERT INTO "10_kbio".20_dtl_attrs
               (id, entity_type_code, entity_id, attr_def_id, key_jsonb, created_by, created_at)
           VALUES (gen_random_uuid(), 'user_profile', $1, $2, $3::jsonb, $4, CURRENT_TIMESTAMP)
           ON CONFLICT (entity_type_code, entity_id, attr_def_id) DO UPDATE
               SET key_jsonb   = EXCLUDED.key_jsonb,
                   created_by  = EXCLUDED.created_by,
                   created_at  = CURRENT_TIMESTAMP""",
        profile_id,
        attr_def_id,
        value,
        actor_id,
    )
