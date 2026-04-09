"""kprotect policy_sets repository.

Reads from v_policy_sets.
Writes to 11_kprotect.11_fct_policy_sets, 20_dtl_attrs, 40_lnk_policy_set_selections.
EAV attr/entity lookups always use subselects — never hardcoded IDs.
"""

from __future__ import annotations

import uuid


async def list_policy_sets(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
) -> list[dict]:
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, org_id, code, name, description, evaluation_mode,
               is_default, is_active, created_at, updated_at
          FROM "11_kprotect".v_policy_sets
         WHERE org_id = $1
           AND deleted_at IS NULL
         ORDER BY is_default DESC, created_at DESC
         LIMIT $2 OFFSET $3
        """,
        org_id,
        limit,
        offset,
    )
    return [dict(r) for r in rows]


async def count_policy_sets(conn: object, org_id: str) -> int:
    total = await conn.fetchval(  # type: ignore[union-attr]
        """
        SELECT COUNT(*)
          FROM "11_kprotect".v_policy_sets
         WHERE org_id = $1
           AND deleted_at IS NULL
        """,
        org_id,
    )
    return int(total)


async def get_policy_set(conn: object, policy_set_id: str) -> dict | None:
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, org_id, code, name, description, evaluation_mode,
               is_default, is_active, created_at, updated_at
          FROM "11_kprotect".v_policy_sets
         WHERE id = $1
           AND deleted_at IS NULL
        """,
        policy_set_id,
    )
    return dict(row) if row else None


async def create_policy_set(
    conn: object,
    *,
    set_id: str,
    org_id: str,
    is_default: bool,
    actor_id: str,
) -> None:
    """Insert the fact row for a policy set."""
    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "11_kprotect"."11_fct_policy_sets"
            (id, org_id, is_default, is_active,
             created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, TRUE, $4, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        set_id,
        org_id,
        is_default,
        actor_id,
    )


async def upsert_policy_set_attr(
    conn: object,
    *,
    set_id: str,
    attr_code: str,
    value: object,
    actor_id: str,
) -> None:
    """EAV upsert into 20_dtl_attrs for a policy set entity."""
    attr_id = str(uuid.uuid4())
    if isinstance(value, (dict, list)):
        await conn.execute(  # type: ignore[union-attr]
            """
            INSERT INTO "11_kprotect"."20_dtl_attrs"
                (id, entity_type_id, entity_id, attr_def_id,
                 key_jsonb, created_by, updated_by, created_at, updated_at)
            VALUES (
                $1,
                (SELECT id FROM "11_kprotect"."04_dim_entity_types"
                  WHERE code = 'kp_policy_set'),
                $2,
                (SELECT id FROM "11_kprotect"."05_dim_attr_defs"
                  WHERE code = $3),
                $4,
                $5, $5,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (entity_id, attr_def_id)
            DO UPDATE SET key_jsonb  = EXCLUDED.key_jsonb,
                          updated_by = EXCLUDED.updated_by,
                          updated_at = CURRENT_TIMESTAMP
            """,
            attr_id,
            set_id,
            attr_code,
            value,
            actor_id,
        )
    else:
        await conn.execute(  # type: ignore[union-attr]
            """
            INSERT INTO "11_kprotect"."20_dtl_attrs"
                (id, entity_type_id, entity_id, attr_def_id,
                 key_text, created_by, updated_by, created_at, updated_at)
            VALUES (
                $1,
                (SELECT id FROM "11_kprotect"."04_dim_entity_types"
                  WHERE code = 'kp_policy_set'),
                $2,
                (SELECT id FROM "11_kprotect"."05_dim_attr_defs"
                  WHERE code = $3),
                $4,
                $5, $5,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
            ON CONFLICT (entity_id, attr_def_id)
            DO UPDATE SET key_text   = EXCLUDED.key_text,
                          updated_by = EXCLUDED.updated_by,
                          updated_at = CURRENT_TIMESTAMP
            """,
            attr_id,
            set_id,
            attr_code,
            str(value),
            actor_id,
        )


async def add_selection_to_set(
    conn: object,
    *,
    set_id: str,
    selection_id: str,
    sort_order: int,
    org_id: str,
    actor_id: str,
) -> None:
    """Insert a member link row into 40_lnk_policy_set_selections."""
    link_id = str(uuid.uuid4())
    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "11_kprotect"."40_lnk_policy_set_selections"
            (id, policy_set_id, policy_selection_id, sort_order,
             org_id, created_by, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
        """,
        link_id,
        set_id,
        selection_id,
        sort_order,
        org_id,
        actor_id,
    )


async def clear_set_selections(conn: object, set_id: str) -> None:
    """Delete all link rows for this set (so they can be recreated)."""
    await conn.execute(  # type: ignore[union-attr]
        """
        DELETE FROM "11_kprotect"."40_lnk_policy_set_selections"
         WHERE policy_set_id = $1
        """,
        set_id,
    )


async def get_set_selections(conn: object, set_id: str) -> list[dict]:
    """Return the member list for a set, ordered by sort_order."""
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT policy_selection_id AS selection_id, sort_order
          FROM "11_kprotect"."40_lnk_policy_set_selections"
         WHERE policy_set_id = $1
         ORDER BY sort_order ASC
        """,
        set_id,
    )
    return [dict(r) for r in rows]


async def soft_delete_policy_set(
    conn: object,
    set_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete by setting deleted_at."""
    await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "11_kprotect"."11_fct_policy_sets"
           SET deleted_at  = CURRENT_TIMESTAMP,
               is_active   = FALSE,
               updated_by  = $2,
               updated_at  = CURRENT_TIMESTAMP
         WHERE id = $1
        """,
        set_id,
        actor_id,
    )
