"""Repository for the capabilities catalog + role grants."""

from __future__ import annotations

from typing import Any

import asyncpg


async def list_actions(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        'SELECT id, code, label, description, sort_order '
        'FROM "09_featureflags"."01_dim_permission_actions" '
        'WHERE deprecated_at IS NULL '
        'ORDER BY sort_order, id'
    )
    return [dict(r) for r in rows]


async def list_categories(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        'SELECT id, code, label, description, sort_order '
        'FROM "09_featureflags"."02_dim_feature_flag_categories" '
        'WHERE deprecated_at IS NULL '
        'ORDER BY sort_order, id'
    )
    return [dict(r) for r in rows]


async def list_capabilities(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        '''
        SELECT f.id, f.code, f.name, f.description,
               f.category_id, c.code AS category_code,
               f.feature_scope, f.access_mode, f.lifecycle_state,
               f.env_dev, f.env_staging, f.env_prod,
               f.rollout_mode, f.required_license
        FROM "09_featureflags"."03_dim_feature_flags" f
        JOIN "09_featureflags"."02_dim_feature_flag_categories" c
          ON c.id = f.category_id
        WHERE f.deprecated_at IS NULL
        ORDER BY c.sort_order, c.id, f.name
        '''
    )
    return [dict(r) for r in rows]


async def list_feature_permissions(conn: asyncpg.Connection) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        '''
        SELECT fp.id, fp.code,
               fp.flag_id, f.code AS flag_code,
               fp.action_id, a.code AS action_code,
               fp.name, fp.description
        FROM "09_featureflags"."04_dim_feature_permissions" fp
        JOIN "09_featureflags"."03_dim_feature_flags" f ON f.id = fp.flag_id
        JOIN "09_featureflags"."01_dim_permission_actions" a ON a.id = fp.action_id
        WHERE fp.deprecated_at IS NULL
        ORDER BY f.code, a.sort_order
        '''
    )
    return [dict(r) for r in rows]


async def list_role_grants(
    conn: asyncpg.Connection, role_id: str
) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        '''
        SELECT rfp.id, rfp.role_id, rfp.feature_permission_id,
               fp.code AS permission_code,
               f.code AS flag_code, a.code AS action_code,
               rfp.created_at
        FROM "09_featureflags"."40_lnk_role_feature_permissions" rfp
        JOIN "09_featureflags"."04_dim_feature_permissions" fp
            ON fp.id = rfp.feature_permission_id
        JOIN "09_featureflags"."03_dim_feature_flags" f ON f.id = fp.flag_id
        JOIN "09_featureflags"."01_dim_permission_actions" a ON a.id = fp.action_id
        WHERE rfp.role_id = $1
        ORDER BY f.code, a.sort_order
        ''',
        role_id,
    )
    return [dict(r) for r in rows]


async def get_role_code(
    conn: asyncpg.Connection, role_id: str
) -> str | None:
    row = await conn.fetchrow(
        'SELECT code FROM "03_iam".v_roles WHERE id = $1',
        role_id,
    )
    return row["code"] if row else None


async def get_feature_permission_id_by_code(
    conn: asyncpg.Connection, code: str
) -> int | None:
    row = await conn.fetchrow(
        'SELECT id FROM "09_featureflags"."04_dim_feature_permissions" '
        'WHERE code = $1 AND deprecated_at IS NULL',
        code,
    )
    return row["id"] if row else None


async def insert_grant(
    conn: asyncpg.Connection,
    *,
    grant_id: str,
    role_id: str,
    feature_permission_id: int,
    created_by: str,
) -> None:
    await conn.execute(
        'INSERT INTO "09_featureflags"."40_lnk_role_feature_permissions" '
        '(id, role_id, feature_permission_id, created_by) '
        'VALUES ($1, $2, $3, $4) '
        'ON CONFLICT (role_id, feature_permission_id) DO NOTHING',
        grant_id, role_id, feature_permission_id, created_by,
    )


async def delete_grant_by_code(
    conn: asyncpg.Connection,
    *,
    role_id: str,
    permission_code: str,
) -> int:
    row = await conn.fetchrow(
        '''
        DELETE FROM "09_featureflags"."40_lnk_role_feature_permissions" rfp
        USING "09_featureflags"."04_dim_feature_permissions" fp
        WHERE rfp.role_id = $1
          AND rfp.feature_permission_id = fp.id
          AND fp.code = $2
        RETURNING rfp.id
        ''',
        role_id, permission_code,
    )
    return 1 if row else 0
