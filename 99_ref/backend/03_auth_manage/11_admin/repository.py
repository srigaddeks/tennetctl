from __future__ import annotations

from datetime import datetime
from importlib import import_module

import asyncpg

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="admin.repository", logger_name="backend.admin.repository.instrumentation"
)
class AdminRepository:
    async def list_users(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        limit: int = 50,
        offset: int = 0,
        search: str | None = None,
        is_active: bool | None = None,
        is_disabled: bool | None = None,
        account_status: str | None = None,
        org_id: str | None = None,
        group_id: str | None = None,
        user_category: str | None = None,
    ) -> tuple[list[dict], int]:
        """Returns (users, total_count) using a window function."""
        conditions = ["u.tenant_key = $1", "u.is_deleted = FALSE"]
        params: list = [tenant_key]
        idx = 2

        if search:
            conditions.append(
                f"(v.email ILIKE ${idx} OR v.username ILIKE ${idx} OR dn.property_value ILIKE ${idx})"
            )
            params.append(f"%{search}%")
            idx += 1
        if is_active is not None:
            conditions.append(f"u.is_active = ${idx}")
            params.append(is_active)
            idx += 1
        if is_disabled is not None:
            conditions.append(f"u.is_disabled = ${idx}")
            params.append(is_disabled)
            idx += 1
        if account_status is not None:
            conditions.append(f"v.account_status = ${idx}")
            params.append(account_status)
            idx += 1
        if user_category is not None:
            conditions.append(f"COALESCE(u.user_category, 'full') = ${idx}")
            params.append(user_category)
            idx += 1

        where_clause = " AND ".join(conditions)
        join_clause = f'LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = u.id'
        join_clause += f" LEFT JOIN {SCHEMA}.\"05_dtl_user_properties\" dn ON dn.user_id = u.id AND dn.property_key = 'display_name'"

        if org_id is not None:
            join_clause += f' JOIN {SCHEMA}."31_lnk_org_memberships" om ON om.user_id = u.id AND om.org_id = ${idx} AND om.is_deleted = FALSE'
            params.append(org_id)
            idx += 1
        if group_id is not None:
            join_clause += f' JOIN {SCHEMA}."18_lnk_group_memberships" gm ON gm.user_id = u.id AND gm.group_id = ${idx} AND gm.is_deleted = FALSE'
            params.append(group_id)
            idx += 1

        params.extend([limit, offset])
        rows = await connection.fetch(
            f"""
            SELECT
                u.id AS user_id,
                u.tenant_key,
                v.email,
                v.username,
                v.account_status,
                COALESCE(u.user_category, 'full') AS user_category,
                u.is_active,
                u.is_disabled,
                u.is_locked,
                u.is_system,
                u.is_test,
                u.created_at,
                dn.property_value AS display_name,
                COUNT(*) OVER() AS _total
            FROM {SCHEMA}."03_fct_users" u
            {join_clause}
            WHERE {where_clause}
            ORDER BY u.created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params,
        )
        total = rows[0]["_total"] if rows else 0
        return [dict(r) for r in rows], total

    async def get_user_detail(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                u.id AS user_id,
                u.tenant_key,
                v.email,
                v.username,
                v.account_status,
                u.is_active,
                u.is_disabled,
                u.created_at
            FROM {SCHEMA}."03_fct_users" u
            LEFT JOIN {SCHEMA}."42_vw_auth_users" v ON v.user_id = u.id
            WHERE u.id = $1 AND u.is_deleted = FALSE
            """,
            user_id,
        )
        return dict(row) if row else None

    async def get_user_properties(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT property_key AS key, property_value AS value
            FROM {SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1
            ORDER BY property_key
            """,
            user_id,
        )
        return [dict(r) for r in rows]

    async def get_user_org_memberships(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                o.id AS org_id,
                o.name AS org_name,
                o.org_type_code AS org_type,
                om.membership_type AS role,
                om.is_active,
                om.created_at AS joined_at
            FROM {SCHEMA}."31_lnk_org_memberships" om
            JOIN {SCHEMA}."29_fct_orgs" o ON o.id = om.org_id
            WHERE om.user_id = $1 AND om.is_deleted = FALSE
            ORDER BY o.name
            """,
            user_id,
        )
        return [dict(r) for r in rows]

    async def get_user_workspace_memberships(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                w.id AS workspace_id,
                w.name AS workspace_name,
                w.workspace_type_code AS workspace_type,
                o.id AS org_id,
                o.name AS org_name,
                wm.membership_type AS role,
                wm.is_active,
                wm.created_at AS joined_at
            FROM {SCHEMA}."36_lnk_workspace_memberships" wm
            JOIN {SCHEMA}."34_fct_workspaces" w ON w.id = wm.workspace_id
            JOIN {SCHEMA}."29_fct_orgs" o ON o.id = w.org_id
            WHERE wm.user_id = $1 AND wm.is_deleted = FALSE
            ORDER BY o.name, w.name
            """,
            user_id,
        )
        return [dict(r) for r in rows]

    async def get_user_group_memberships(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                g.id AS group_id,
                g.name AS group_name,
                g.code AS group_code,
                g.role_level_code,
                g.scope_org_id,
                g.scope_workspace_id,
                g.is_system,
                gm.is_active,
                gm.created_at AS joined_at
            FROM {SCHEMA}."18_lnk_group_memberships" gm
            JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gm.group_id
            WHERE gm.user_id = $1 AND gm.is_deleted = FALSE AND gm.is_active = TRUE
              AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
            ORDER BY g.scope_org_id NULLS FIRST, g.name
            """,
            user_id,
        )
        return [dict(r) for r in rows]

    async def set_user_disabled(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        is_disabled: bool,
        now: datetime,
    ) -> bool:
        result = await connection.fetchval(
            f"""
            UPDATE {SCHEMA}."03_fct_users"
            SET is_disabled = $1, updated_at = $2
            WHERE id = $3 AND is_deleted = FALSE
            RETURNING id
            """,
            is_disabled,
            now,
            user_id,
        )
        return result is not None

    async def get_user_audit_events(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                e.id, e.tenant_key, e.entity_type, e.entity_id,
                e.event_type, e.event_category, e.actor_id, e.actor_type,
                e.ip_address, e.session_id, e.occurred_at,
                COALESCE(
                    json_object_agg(p.meta_key, p.meta_value)
                        FILTER (WHERE p.meta_key IS NOT NULL),
                    '{{}}'::json
                ) AS properties
            FROM {SCHEMA}."40_aud_events" e
            LEFT JOIN {SCHEMA}."41_dtl_audit_event_properties" p ON p.event_id = e.id
            WHERE (e.entity_id::text = $1 OR e.actor_id::text = $1)
            GROUP BY e.id
            ORDER BY e.occurred_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id,
            limit,
            offset,
        )
        return [dict(r) for r in rows]

    async def count_user_audit_events(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> int:
        return await connection.fetchval(
            f"""
            SELECT COUNT(*)
            FROM {SCHEMA}."40_aud_events"
            WHERE entity_id::text = $1 OR actor_id::text = $1
            """,
            user_id,
        )

    async def list_user_sessions(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        include_revoked: bool = False,
    ) -> list[dict]:
        if include_revoked:
            rows = await connection.fetch(
                f"""
                SELECT id AS session_id, user_id, client_ip, user_agent,
                       is_impersonation, created_at, revoked_at
                FROM {SCHEMA}."10_trx_auth_sessions"
                WHERE user_id = $1
                ORDER BY created_at DESC
                """,
                user_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT id AS session_id, user_id, client_ip, user_agent,
                       is_impersonation, created_at, revoked_at
                FROM {SCHEMA}."10_trx_auth_sessions"
                WHERE user_id = $1
                  AND revoked_at IS NULL
                ORDER BY created_at DESC
                """,
                user_id,
            )
        return [dict(r) for r in rows]

    async def revoke_user_session(
        self,
        connection: asyncpg.Connection,
        *,
        session_id: str,
        reason: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_trx_auth_sessions"
            SET revoked_at = $1, revocation_reason = $2
            WHERE id = $3 AND revoked_at IS NULL
            """,
            now,
            reason,
            session_id,
        )

    async def revoke_all_user_sessions(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        reason: str,
        now: datetime,
    ) -> int:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_trx_auth_sessions"
            SET revoked_at = $1,
                revocation_reason = $2,
                updated_at = $1
            WHERE user_id = $3
              AND revoked_at IS NULL
            """,
            now,
            reason,
            user_id,
        )
        return int(result.split()[-1])

    async def get_session_owner(
        self,
        connection: asyncpg.Connection,
        *,
        session_id: str,
    ) -> str | None:
        return await connection.fetchval(
            f"""
            SELECT user_id::text
            FROM {SCHEMA}."10_trx_auth_sessions"
            WHERE id = $1
            """,
            session_id,
        )

    async def list_audit_events(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        actor_id: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        conditions = ["e.tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2

        if entity_type is not None:
            conditions.append(f"e.entity_type = ${idx}")
            params.append(entity_type)
            idx += 1
        if entity_id is not None:
            conditions.append(f"e.entity_id::text = ${idx}")
            params.append(entity_id)
            idx += 1
        if actor_id is not None:
            conditions.append(f"e.actor_id = ${idx}")
            params.append(actor_id)
            idx += 1
        if event_type is not None:
            conditions.append(f"e.event_type = ${idx}")
            params.append(event_type)
            idx += 1

        where_clause = " AND ".join(conditions)
        params.extend([limit, offset])

        rows = await connection.fetch(
            f"""
            SELECT
                e.id, e.tenant_key, e.entity_type, e.entity_id,
                e.event_type, e.event_category, e.actor_id, e.actor_type,
                e.ip_address, e.session_id, e.occurred_at,
                COALESCE(
                    json_object_agg(p.meta_key, p.meta_value)
                        FILTER (WHERE p.meta_key IS NOT NULL),
                    '{{}}'::json
                ) AS properties
            FROM {SCHEMA}."40_aud_events" e
            LEFT JOIN {SCHEMA}."41_dtl_audit_event_properties" p ON p.event_id = e.id
            WHERE {where_clause}
            GROUP BY e.id
            ORDER BY e.occurred_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params,
        )
        return [dict(r) for r in rows]

    async def count_audit_events(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
        actor_id: str | None = None,
        event_type: str | None = None,
    ) -> int:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2

        if entity_type is not None:
            conditions.append(f"entity_type = ${idx}")
            params.append(entity_type)
            idx += 1
        if entity_id is not None:
            conditions.append(f"entity_id::text = ${idx}")
            params.append(entity_id)
            idx += 1
        if actor_id is not None:
            conditions.append(f"actor_id = ${idx}")
            params.append(actor_id)
            idx += 1
        if event_type is not None:
            conditions.append(f"event_type = ${idx}")
            params.append(event_type)
            idx += 1

        where_clause = " AND ".join(conditions)
        return await connection.fetchval(
            f"""
            SELECT COUNT(*)
            FROM {SCHEMA}."40_aud_events"
            WHERE {where_clause}
            """,
            *params,
        )

    async def list_impersonation_sessions(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                s.id AS session_id,
                s.user_id AS target_user_id,
                s.impersonator_user_id,
                s.impersonation_reason AS reason,
                s.created_at,
                s.revoked_at,
                vt.email AS target_email,
                vi.email AS impersonator_email
            FROM {SCHEMA}."10_trx_auth_sessions" s
            JOIN {SCHEMA}."03_fct_users" u ON u.id = s.user_id
            LEFT JOIN {SCHEMA}."42_vw_auth_users" vt ON vt.user_id = s.user_id
            LEFT JOIN {SCHEMA}."42_vw_auth_users" vi ON vi.user_id = s.impersonator_user_id
            WHERE s.is_impersonation = TRUE
              AND u.tenant_key = $1
            ORDER BY s.created_at DESC
            LIMIT $2 OFFSET $3
            """,
            tenant_key,
            limit,
            offset,
        )
        return [dict(r) for r in rows]

    async def evaluate_user_features(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                ff.code,
                ff.name,
                (ff.lifecycle_state = 'active') AS enabled,
                ARRAY_AGG(DISTINCT pa.code ORDER BY pa.code) AS permissions
            FROM {SCHEMA}."18_lnk_group_memberships" gm
            JOIN {SCHEMA}."17_fct_user_groups" g ON g.id = gm.group_id
            JOIN {SCHEMA}."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
            JOIN {SCHEMA}."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
            JOIN {SCHEMA}."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
            JOIN {SCHEMA}."14_dim_feature_flags" ff ON ff.code = fp.feature_flag_code
            JOIN {SCHEMA}."12_dim_feature_permission_actions" pa ON pa.code = fp.permission_action_code
            WHERE gm.user_id = $1
              AND gm.is_active = TRUE AND gm.is_deleted = FALSE
              AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
              AND g.is_active = TRUE AND g.is_deleted = FALSE
              AND gra.is_active = TRUE AND gra.is_deleted = FALSE
              AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
              AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
            GROUP BY ff.code, ff.name, ff.lifecycle_state
            ORDER BY ff.code
            """,
            user_id,
        )
        return [dict(r) for r in rows]

    async def soft_delete_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        now,
    ) -> bool:
        """Soft-delete a user by setting is_deleted=TRUE and revoking all active sessions."""
        # Revoke all active sessions (sessions without revoked_at are still active)
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_trx_auth_sessions"
            SET revoked_at = $2, revocation_reason = 'admin_deleted'
            WHERE user_id = $1 AND revoked_at IS NULL
            """,
            user_id,
            now,
        )
        # Soft-delete the user
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."03_fct_users"
            SET is_deleted = TRUE, is_active = FALSE, is_disabled = TRUE, updated_at = $2
            WHERE id = $1 AND is_deleted = FALSE
            """,
            user_id,
            now,
        )
        return result == "UPDATE 1"
