"""kprotect signal_selections repository.

Reads from v_signal_selections.
Writes to 11_kprotect.13_fct_signal_selections and 20_dtl_attrs.
EAV attr/entity lookups always use subselects -- never hardcoded IDs.
"""

from __future__ import annotations

import uuid


async def list_signal_selections(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
) -> list[dict]:
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, org_id, signal_code, config_overrides, notes,
               is_active, created_at, updated_at
          FROM "11_kprotect".v_signal_selections
         WHERE org_id = $1
           AND deleted_at IS NULL
         ORDER BY created_at DESC
         LIMIT $2 OFFSET $3
        """,
        org_id,
        limit,
        offset,
    )
    return [dict(r) for r in rows]


async def count_signal_selections(conn: object, org_id: str) -> int:
    total = await conn.fetchval(  # type: ignore[union-attr]
        """
        SELECT COUNT(*)
          FROM "11_kprotect".v_signal_selections
         WHERE org_id = $1
           AND deleted_at IS NULL
        """,
        org_id,
    )
    return int(total)


async def get_signal_selection(conn: object, selection_id: str) -> dict | None:
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, org_id, signal_code, config_overrides, notes,
               is_active, created_at, updated_at
          FROM "11_kprotect".v_signal_selections
         WHERE id = $1
           AND deleted_at IS NULL
        """,
        selection_id,
    )
    return dict(row) if row else None


async def create_signal_selection(
    conn: object,
    *,
    selection_id: str,
    org_id: str,
    actor_id: str,
) -> None:
    """Insert the fact row for a signal selection."""
    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "11_kprotect"."13_fct_signal_selections"
            (id, org_id, is_active, created_by, updated_by,
             created_at, updated_at)
        VALUES ($1, $2, TRUE, $3, $3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        selection_id,
        org_id,
        actor_id,
    )


async def upsert_signal_selection_attr(
    conn: object,
    *,
    selection_id: str,
    attr_code: str,
    value: object,
    actor_id: str,
) -> None:
    """EAV upsert into 20_dtl_attrs.

    entity_type_id and attr_def_id are resolved by subselect -- never hardcoded.
    Uses key_text for string values, key_jsonb for dicts/lists.
    """
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
                  WHERE code = 'kp_signal_selection'),
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
            selection_id,
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
                  WHERE code = 'kp_signal_selection'),
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
            selection_id,
            attr_code,
            str(value),
            actor_id,
        )


async def patch_signal_selection(
    conn: object,
    selection_id: str,
    *,
    is_active: bool | None,
    actor_id: str,
) -> None:
    """Update mutable columns on the fact row."""
    sets: list[str] = ["updated_by = $2", "updated_at = CURRENT_TIMESTAMP"]
    params: list = [selection_id, actor_id]

    if is_active is not None:
        params.append(is_active)
        sets.append(f"is_active = ${len(params)}")

    await conn.execute(  # type: ignore[union-attr]
        f"""
        UPDATE "11_kprotect"."13_fct_signal_selections"
           SET {", ".join(sets)}
         WHERE id = $1
        """,
        *params,
    )


async def soft_delete_signal_selection(
    conn: object,
    selection_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete by setting deleted_at."""
    await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "11_kprotect"."13_fct_signal_selections"
           SET deleted_at  = CURRENT_TIMESTAMP,
               is_active   = FALSE,
               updated_by  = $2,
               updated_at  = CURRENT_TIMESTAMP
         WHERE id = $1
        """,
        selection_id,
        actor_id,
    )
