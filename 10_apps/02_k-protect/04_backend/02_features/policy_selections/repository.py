"""kprotect policy_selections repository.

Reads from v_policy_selections.
Writes to 11_kprotect.10_fct_policy_selections and 20_dtl_attrs.
EAV attr/entity lookups always use subselects — never hardcoded IDs.
"""

from __future__ import annotations

import uuid


async def list_selections(
    conn: object,
    org_id: str,
    *,
    limit: int,
    offset: int,
) -> list[dict]:
    rows = await conn.fetch(  # type: ignore[union-attr]
        """
        SELECT id, org_id, predefined_policy_code, policy_category, policy_name,
               priority, config_overrides, notes,
               threat_type_code, signal_overrides, action_override,
               is_active, created_at, updated_at
          FROM "11_kprotect".v_policy_selections
         WHERE org_id = $1
           AND deleted_at IS NULL
         ORDER BY priority ASC, created_at DESC
         LIMIT $2 OFFSET $3
        """,
        org_id,
        limit,
        offset,
    )
    return [dict(r) for r in rows]


async def count_selections(conn: object, org_id: str) -> int:
    total = await conn.fetchval(  # type: ignore[union-attr]
        """
        SELECT COUNT(*)
          FROM "11_kprotect".v_policy_selections
         WHERE org_id = $1
           AND deleted_at IS NULL
        """,
        org_id,
    )
    return int(total)


async def get_selection(conn: object, selection_id: str) -> dict | None:
    row = await conn.fetchrow(  # type: ignore[union-attr]
        """
        SELECT id, org_id, predefined_policy_code, policy_category, policy_name,
               priority, config_overrides, notes,
               threat_type_code, signal_overrides, action_override,
               is_active, created_at, updated_at
          FROM "11_kprotect".v_policy_selections
         WHERE id = $1
           AND deleted_at IS NULL
        """,
        selection_id,
    )
    return dict(row) if row else None


async def create_selection(
    conn: object,
    *,
    selection_id: str,
    org_id: str,
    predefined_policy_code: str,
    priority: int,
    actor_id: str,
) -> None:
    """Insert the fact row for a policy selection."""
    await conn.execute(  # type: ignore[union-attr]
        """
        INSERT INTO "11_kprotect"."10_fct_policy_selections"
            (id, org_id, predefined_policy_code, priority,
             is_active, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, $4, TRUE, $5, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        selection_id,
        org_id,
        predefined_policy_code,
        priority,
        actor_id,
    )


async def upsert_selection_attr(
    conn: object,
    *,
    selection_id: str,
    attr_code: str,
    value: object,
    actor_id: str,
) -> None:
    """EAV upsert into 20_dtl_attrs.

    entity_type_id and attr_def_id are resolved by subselect — never hardcoded.
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
                  WHERE code = 'kp_policy_selection'),
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
                  WHERE code = 'kp_policy_selection'),
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


async def patch_selection(
    conn: object,
    selection_id: str,
    *,
    priority: int | None,
    is_active: bool | None,
    actor_id: str,
) -> None:
    """Update mutable columns on the fact row."""
    sets: list[str] = ["updated_by = $2", "updated_at = CURRENT_TIMESTAMP"]
    params: list = [selection_id, actor_id]

    if priority is not None:
        params.append(priority)
        sets.append(f"priority = ${len(params)}")

    if is_active is not None:
        params.append(is_active)
        sets.append(f"is_active = ${len(params)}")

    await conn.execute(  # type: ignore[union-attr]
        f"""
        UPDATE "11_kprotect"."10_fct_policy_selections"
           SET {", ".join(sets)}
         WHERE id = $1
        """,
        *params,
    )


async def soft_delete_selection(
    conn: object,
    selection_id: str,
    *,
    actor_id: str,
) -> None:
    """Soft-delete by setting deleted_at."""
    await conn.execute(  # type: ignore[union-attr]
        """
        UPDATE "11_kprotect"."10_fct_policy_selections"
           SET deleted_at  = CURRENT_TIMESTAMP,
               is_active   = FALSE,
               updated_by  = $2,
               updated_at  = CURRENT_TIMESTAMP
         WHERE id = $1
        """,
        selection_id,
        actor_id,
    )
