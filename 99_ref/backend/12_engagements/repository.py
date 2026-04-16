from __future__ import annotations
import asyncpg
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from importlib import import_module

from .models import EngagementDetailRecord, EngagementRecord, AuditAccessTokenRecord, AuditorRequestRecord

SCHEMA = '"12_engagements"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


def _accessible_engagements_cte(*, include_org_filter: bool = False) -> str:
    org_filter_sql = " AND e.org_id = $3::uuid" if include_org_filter else ""
    return f"""
        WITH accessible_engagements AS (
            SELECT DISTINCT e.id
            FROM {SCHEMA}."10_fct_audit_engagements" e
            JOIN "03_auth_manage"."03_fct_users" u
              ON u.id = $1::uuid
             AND u.is_active = TRUE
             AND u.is_disabled = FALSE
             AND u.is_deleted = FALSE
             AND u.is_locked = FALSE
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = e.framework_deployment_id
            LEFT JOIN {SCHEMA}."12_lnk_engagement_memberships" m
              ON m.engagement_id = e.id
             AND m.user_id = $1::uuid
             AND m.is_deleted = FALSE
             AND m.is_active = TRUE
             AND m.status_code = 'active'
             AND (m.expires_at IS NULL OR m.expires_at > NOW())
            LEFT JOIN {SCHEMA}."11_fct_audit_access_tokens" t
              ON t.engagement_id = e.id
             AND lower(t.auditor_email) = lower($2)
             AND t.is_revoked = FALSE
             AND t.expires_at > NOW()
            LEFT JOIN "03_auth_manage"."47_lnk_grc_role_assignments" gra
              ON gra.user_id = $1::uuid
             AND gra.org_id = e.org_id
             AND gra.revoked_at IS NULL
            LEFT JOIN "03_auth_manage"."48_lnk_grc_access_grants" g_eng
              ON g_eng.grc_role_assignment_id = gra.id
             AND g_eng.revoked_at IS NULL
             AND g_eng.scope_type = 'engagement'
             AND g_eng.scope_id = e.id
            LEFT JOIN "03_auth_manage"."48_lnk_grc_access_grants" g_fw
              ON g_fw.grc_role_assignment_id = gra.id
             AND g_fw.revoked_at IS NULL
             AND g_fw.scope_type = 'framework'
             AND g_fw.scope_id = e.framework_deployment_id
            WHERE e.is_deleted = FALSE
              AND (
                    m.id IS NOT NULL
                 OR t.id IS NOT NULL
                 OR (
                        gra.id IS NOT NULL
                    AND NOT EXISTS (
                        SELECT 1
                        FROM "03_auth_manage"."48_lnk_grc_access_grants" g_any
                        WHERE g_any.grc_role_assignment_id = gra.id
                          AND g_any.revoked_at IS NULL
                    )
                 )
                 OR g_eng.id IS NOT NULL
                 OR g_fw.id IS NOT NULL
              )
              {org_filter_sql}
        )
    """


@instrument_class_methods(namespace="engagements.repository", logger_name="backend.engagements.repository.instrumentation")
class EngagementRepository:
    async def deactivate_memberships_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        actor_id: str | None,
        now: datetime,
    ) -> int:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_lnk_engagement_memberships"
            SET status_code = 'revoked',
                is_active = FALSE,
                expires_at = COALESCE(expires_at, $2),
                updated_at = $2,
                updated_by = $3::uuid
            WHERE user_id = $1::uuid
              AND is_deleted = FALSE
              AND (
                    is_active = TRUE
                 OR status_code <> 'revoked'
                 OR (expires_at IS NULL OR expires_at > $2)
              )
            """,
            UUID(user_id),
            now,
            UUID(actor_id) if actor_id else None,
        )
        return int(result.split()[-1])

    async def revoke_evidence_grants_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        revoked_by: str | None,
        now: datetime,
    ) -> int:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."13_lnk_evidence_access_grants" AS g
            SET revoked_at = $2,
                revoked_by = $3::uuid,
                is_active = FALSE,
                updated_at = $2,
                updated_by = $3::uuid
            FROM {SCHEMA}."12_lnk_engagement_memberships" AS m
            WHERE m.id = g.membership_id
              AND m.user_id = $1::uuid
              AND m.is_deleted = FALSE
              AND g.revoked_at IS NULL
              AND g.is_deleted = FALSE
              AND g.is_active = TRUE
            """,
            UUID(user_id),
            now,
            UUID(revoked_by) if revoked_by else None,
        )
        return int(result.split()[-1])

    async def _lock_request_for_review(
        self,
        connection: asyncpg.Connection,
        *,
        request_id: str,
        tenant_key: str,
    ):
        return await connection.fetchrow(
            f"""
            SELECT
                r.id,
                r.engagement_id,
                r.control_id,
                r.task_id,
                r.request_status,
                lower(t.auditor_email) AS auditor_email,
                m.id::text AS membership_id
            FROM {SCHEMA}."20_trx_auditor_requests" r
            JOIN {SCHEMA}."10_fct_audit_engagements" e
              ON e.id = r.engagement_id
            LEFT JOIN {SCHEMA}."11_fct_audit_access_tokens" t
              ON t.id = r.requested_by_token_id
            LEFT JOIN {SCHEMA}."12_lnk_engagement_memberships" m
              ON m.engagement_id = r.engagement_id
             AND lower(m.external_email) = lower(t.auditor_email)
             AND m.is_deleted = FALSE
             AND m.is_active = TRUE
             AND COALESCE(m.is_disabled, FALSE) = FALSE
             AND m.status_code = 'active'
             AND (m.expires_at IS NULL OR m.expires_at > NOW())
            WHERE r.id = $1::uuid
              AND e.tenant_key = $2
              AND r.is_deleted = FALSE
            FOR UPDATE
            """,
            UUID(request_id),
            tenant_key,
        )

    async def is_user_globally_active(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
    ) -> bool:
        return bool(
            await connection.fetchval(
                """
                SELECT 1
                FROM "03_auth_manage"."03_fct_users"
                WHERE id = $1::uuid
                  AND is_active = TRUE
                  AND is_disabled = FALSE
                  AND is_deleted = FALSE
                  AND is_locked = FALSE
                LIMIT 1
                """,
                UUID(user_id),
            )
        )

    async def get_active_membership_access(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        user_id: str,
    ) -> Optional[dict[str, str | None]]:
        row = await connection.fetchrow(
            f"""
            SELECT
                e.tenant_key,
                e.org_id::text AS org_id,
                fd.workspace_id::text AS workspace_id,
                m.id::text AS membership_id,
                m.membership_type_code
            FROM {SCHEMA}."12_lnk_engagement_memberships" m
            JOIN {SCHEMA}."10_fct_audit_engagements" e
              ON e.id = m.engagement_id
             AND e.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = e.framework_deployment_id
            JOIN "03_auth_manage"."03_fct_users" u
              ON u.id = m.user_id
             AND u.is_active = TRUE
             AND u.is_disabled = FALSE
             AND u.is_deleted = FALSE
             AND u.is_locked = FALSE
            WHERE m.engagement_id = $1::uuid
              AND m.user_id = $2::uuid
              AND m.is_deleted = FALSE
              AND m.is_active = TRUE
              AND COALESCE(m.is_disabled, FALSE) = FALSE
              AND m.status_code = 'active'
              AND (m.expires_at IS NULL OR m.expires_at > NOW())
            LIMIT 1
            """,
            UUID(engagement_id),
            UUID(user_id),
        )
        return dict(row) if row else None

    async def list_accessible_engagement_ids_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        org_id: str | None = None,
    ) -> list[str] | None:
        """Return the list of engagement IDs accessible to the user.

        Returns None if the user has a GRC role with 'all access' (internal role or no grants),
        meaning they should see all data in the org (unfiltered).
        """
        # 1. Check for 'All Access' (INTERNAL roles or no explicit grants)
        # Internal roles (practitioner, engineer, ciso) bypass narrowing.
        role_info = await connection.fetchrow(
            """
            SELECT gra.id::text AS assignment_id, gra.grc_role_code
            FROM "03_auth_manage"."47_lnk_grc_role_assignments" gra
            WHERE gra.user_id = $1::uuid
              AND ($2::uuid IS NULL OR gra.org_id = $2::uuid)
              AND gra.revoked_at IS NULL
            LIMIT 1
            """,
            UUID(user_id),
            UUID(org_id) if org_id else None,
        )
        
        INTERNAL_ROLES = {"grc_practitioner", "grc_engineer", "grc_ciso"}
        if role_info:
            if role_info["grc_role_code"] in INTERNAL_ROLES:
                return None  # Internal roles see everything
            
            # Non-internal roles (auditor/vendor) are narrowed IF grants exist
            has_grants = await connection.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM "03_auth_manage"."48_lnk_grc_access_grants"
                    WHERE grc_role_assignment_id = $1::uuid
                      AND revoked_at IS NULL
                )
                """,
                UUID(role_info["assignment_id"]),
            )
            if not has_grants:
                return None  # No grants = All access
        else:
            # No GRC role at all = use standard permissions (unfiltered by GRC scope)
            return None

        # 2. Collect specific accessible engagement IDs (memberships, grants, tokens)
        params: list[object] = [UUID(user_id)]
        org_filter_sql = ""
        if org_id is not None:
            params.append(UUID(org_id))
            org_filter_sql = " AND e.org_id = $2::uuid"

        rows = await connection.fetch(
            f"""
            SELECT DISTINCT e.id::text
            FROM {SCHEMA}."10_fct_audit_engagements" e
            JOIN "03_auth_manage"."03_fct_users" u
              ON u.id = $1::uuid
             AND u.is_active = TRUE
             AND u.is_disabled = FALSE
             AND u.is_deleted = FALSE
             AND u.is_locked = FALSE
            LEFT JOIN {SCHEMA}."12_lnk_engagement_memberships" m
              ON m.engagement_id = e.id
             AND m.user_id = $1::uuid
             AND m.is_deleted = FALSE
             AND m.is_active = TRUE
             AND COALESCE(m.is_disabled, FALSE) = FALSE
             AND m.status_code = 'active'
             AND (m.expires_at IS NULL OR m.expires_at > NOW())
            LEFT JOIN "03_auth_manage"."47_lnk_grc_role_assignments" gra
              ON gra.user_id = $1::uuid
             AND gra.org_id = e.org_id
             AND gra.revoked_at IS NULL
            LEFT JOIN "03_auth_manage"."48_lnk_grc_access_grants" g_eng
              ON g_eng.grc_role_assignment_id = gra.id
             AND g_eng.revoked_at IS NULL
             AND g_eng.scope_type = 'engagement'
             AND g_eng.scope_id = e.id
            LEFT JOIN "03_auth_manage"."48_lnk_grc_access_grants" g_fw
              ON g_fw.grc_role_assignment_id = gra.id
             AND g_fw.revoked_at IS NULL
             AND g_fw.scope_type = 'framework'
             AND g_fw.scope_id = e.framework_deployment_id
            WHERE e.is_deleted = FALSE
              {org_filter_sql}
              AND (
                    m.id IS NOT NULL
                 OR g_eng.id IS NOT NULL
                 OR g_fw.id IS NOT NULL
              )
            """,
            *params,
        )
        return [row["id"] for row in rows]


    async def is_active_engagement_participant_user(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        user_id: str,
    ) -> bool:
        return bool(
            await connection.fetchval(
                f"""
                SELECT 1
                FROM {SCHEMA}."12_lnk_engagement_memberships" m
                WHERE m.engagement_id = $1::uuid
                  AND m.user_id = $2::uuid
                  AND m.is_deleted = FALSE
                  AND m.is_active = TRUE
                  AND COALESCE(m.is_disabled, FALSE) = FALSE
                  AND m.status_code = 'active'
                  AND (m.expires_at IS NULL OR m.expires_at > NOW())
                LIMIT 1
                """,
                UUID(engagement_id),
                UUID(user_id),
            )
        )

    async def list_active_engagement_participants(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
    ) -> list[dict[str, str | None]]:
        rows = await connection.fetch(
            f"""
            WITH engagement_context AS (
                SELECT
                    e.id,
                    e.created_by,
                    fd.workspace_id
                FROM {SCHEMA}."10_fct_audit_engagements" e
                LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
                  ON fd.id = e.framework_deployment_id
                WHERE e.id = $1::uuid
                  AND e.is_deleted = FALSE
            ),
            membership_participants AS (
                SELECT
                    u.id::text AS user_id,
                    COALESCE(
                        NULLIF(display_name_prop.property_value, ''),
                        NULLIF(name_prop.property_value, ''),
                        NULLIF(email_prop.property_value, ''),
                        u.id::text
                    ) AS display_name,
                    email_prop.property_value AS email,
                    m.membership_type_code
                FROM {SCHEMA}."12_lnk_engagement_memberships" m
                JOIN "03_auth_manage"."03_fct_users" u
                  ON u.id = m.user_id
                 AND u.is_active = TRUE
                 AND u.is_disabled = FALSE
                 AND u.is_deleted = FALSE
                 AND u.is_locked = FALSE
                LEFT JOIN "03_auth_manage"."05_dtl_user_properties" display_name_prop
                  ON display_name_prop.user_id = u.id
                 AND display_name_prop.property_key = 'display_name'
                LEFT JOIN "03_auth_manage"."05_dtl_user_properties" name_prop
                  ON name_prop.user_id = u.id
                 AND name_prop.property_key = 'name'
                LEFT JOIN "03_auth_manage"."05_dtl_user_properties" email_prop
                  ON email_prop.user_id = u.id
                 AND email_prop.property_key = 'email'
                WHERE m.engagement_id = $1::uuid
                  AND m.user_id IS NOT NULL
                  AND m.is_deleted = FALSE
                  AND m.is_active = TRUE
                  AND COALESCE(m.is_disabled, FALSE) = FALSE
                  AND m.status_code = 'active'
                  AND (m.expires_at IS NULL OR m.expires_at > NOW())
            ),
            creator_participant AS (
                SELECT
                    u.id::text AS user_id,
                    COALESCE(
                        NULLIF(display_name_prop.property_value, ''),
                        NULLIF(name_prop.property_value, ''),
                        NULLIF(email_prop.property_value, ''),
                        u.id::text
                    ) AS display_name,
                    email_prop.property_value AS email,
                    COALESCE(NULLIF(wm.grc_role_code, ''), 'owner') AS membership_type_code
                FROM engagement_context ec
                JOIN "03_auth_manage"."03_fct_users" u
                  ON u.id = ec.created_by
                 AND u.is_active = TRUE
                 AND u.is_disabled = FALSE
                 AND u.is_deleted = FALSE
                 AND u.is_locked = FALSE
                LEFT JOIN "03_auth_manage"."36_lnk_workspace_memberships" wm
                  ON wm.workspace_id = ec.workspace_id
                 AND wm.user_id = ec.created_by
                 AND wm.is_active = TRUE
                 AND wm.is_deleted = FALSE
                LEFT JOIN "03_auth_manage"."05_dtl_user_properties" display_name_prop
                  ON display_name_prop.user_id = u.id
                 AND display_name_prop.property_key = 'display_name'
                LEFT JOIN "03_auth_manage"."05_dtl_user_properties" name_prop
                  ON name_prop.user_id = u.id
                 AND name_prop.property_key = 'name'
                LEFT JOIN "03_auth_manage"."05_dtl_user_properties" email_prop
                  ON email_prop.user_id = u.id
                 AND email_prop.property_key = 'email'
                WHERE ec.created_by IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1
                      FROM membership_participants mp
                      WHERE mp.user_id = u.id::text
                  )
            )
            SELECT *
            FROM (
                SELECT * FROM membership_participants
                UNION ALL
                SELECT * FROM creator_participant
            ) participants
            ORDER BY display_name ASC
            """,
            UUID(engagement_id),
        )
        return [dict(row) for row in rows]

    async def is_task_entity_in_engagement_scope(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        entity_type: str | None,
        entity_id: str | None,
    ) -> bool:
        normalized_entity_type = (entity_type or "engagement").strip().lower()
        target_entity_id = entity_id or engagement_id

        if normalized_entity_type == "engagement":
            return str(target_entity_id) == str(engagement_id)

        if normalized_entity_type == "framework":
            sql = f"""
                SELECT 1
                FROM {SCHEMA}."10_fct_audit_engagements" e
                WHERE e.id = $1::uuid
                  AND e.framework_id = $2::uuid
                  AND e.is_deleted = FALSE
                LIMIT 1
            """
        elif normalized_entity_type == "control":
            sql = f"""
                SELECT 1
                FROM {SCHEMA}."10_fct_audit_engagements" e
                JOIN "05_grc_library"."13_fct_controls" c
                  ON c.framework_id = e.framework_id
                 AND c.is_deleted = FALSE
                WHERE e.id = $1::uuid
                  AND c.id = $2::uuid
                  AND e.is_deleted = FALSE
                LIMIT 1
            """
        elif normalized_entity_type == "requirement":
            sql = f"""
                SELECT 1
                FROM {SCHEMA}."10_fct_audit_engagements" e
                JOIN "05_grc_library"."12_fct_requirements" r
                  ON r.framework_id = e.framework_id
                 AND r.is_deleted = FALSE
                WHERE e.id = $1::uuid
                  AND r.id = $2::uuid
                  AND e.is_deleted = FALSE
                LIMIT 1
            """
        else:
            return False

        return bool(
            await connection.fetchval(
                sql,
                UUID(engagement_id),
                UUID(target_entity_id),
            )
        )

    async def get_assessment_in_engagement_scope(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        assessment_id: str,
    ) -> Optional[dict[str, str | None]]:
        row = await connection.fetchrow(
            f"""
            SELECT
                a.id::text AS assessment_id,
                a.tenant_key,
                a.org_id::text AS org_id,
                a.workspace_id::text AS workspace_id,
                a.framework_id::text AS framework_id
            FROM "09_assessments"."40_vw_assessment_detail" a
            JOIN {SCHEMA}."10_fct_audit_engagements" e
              ON e.id = $1::uuid
             AND e.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = e.framework_deployment_id
            WHERE a.id = $2::uuid
              AND a.is_active = TRUE
              AND a.org_id = e.org_id
              AND (
                    (fd.workspace_id IS NULL AND a.workspace_id IS NULL)
                 OR a.workspace_id = fd.workspace_id
              )
              AND (
                    (e.framework_id IS NULL AND a.framework_id IS NULL)
                 OR a.framework_id = e.framework_id
              )
            LIMIT 1
            """,
            UUID(engagement_id),
            UUID(assessment_id),
        )
        return dict(row) if row else None

    async def list_assessments_in_engagement_scope(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
    ) -> list[dict[str, object | None]]:
        rows = await connection.fetch(
            f"""
            SELECT
                a.id::text AS id,
                a.tenant_key,
                a.assessment_code,
                a.org_id::text AS org_id,
                a.workspace_id::text AS workspace_id,
                a.framework_id::text AS framework_id,
                a.assessment_type_code,
                a.assessment_status_code,
                a.lead_assessor_id::text AS lead_assessor_id,
                a.scheduled_start::text AS scheduled_start,
                a.scheduled_end::text AS scheduled_end,
                a.actual_start::text AS actual_start,
                a.actual_end::text AS actual_end,
                a.is_locked,
                a.assessment_type_name,
                a.assessment_status_name,
                a.name,
                a.description,
                a.scope_notes,
                a.finding_count,
                a.is_active,
                a.created_at::text AS created_at,
                a.updated_at::text AS updated_at,
                a.created_by::text AS created_by
            FROM "09_assessments"."40_vw_assessment_detail" a
            JOIN {SCHEMA}."10_fct_audit_engagements" e
              ON e.id = $1::uuid
             AND e.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = e.framework_deployment_id
            WHERE a.is_active = TRUE
              AND a.org_id = e.org_id
              AND (
                    (fd.workspace_id IS NULL AND a.workspace_id IS NULL)
                 OR a.workspace_id = fd.workspace_id
              )
              AND (
                    (e.framework_id IS NULL AND a.framework_id IS NULL)
                 OR a.framework_id = e.framework_id
              )
            ORDER BY a.created_at DESC
            """,
            UUID(engagement_id),
        )
        return [dict(row) for row in rows]

    async def list_engagements(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        status_code: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[EngagementDetailRecord]:
        conditions = ["v.tenant_key = $1", "v.org_id = $2"]
        args = [tenant_key, UUID(org_id)]
        idx = 3

        if status_code:
            conditions.append(f"v.status_code = ${idx}")
            args.append(status_code)
            idx += 1

        where = " AND ".join(conditions)

        rows = await connection.fetch(
            f"""
            SELECT 
                v.*, 
                org.name AS org_name,
                fd.workspace_id::text AS workspace_id,
                w.name AS workspace_name
            FROM {SCHEMA}."40_vw_engagement_detail" v
            LEFT JOIN "03_auth_manage"."29_fct_orgs" org ON org.id = v.org_id
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = v.framework_deployment_id::uuid
            LEFT JOIN "03_auth_manage"."34_fct_workspaces" w
              ON w.id = fd.workspace_id
            WHERE {where}
            ORDER BY v.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        return [_row_to_detail(r) for r in rows]

    async def list_my_engagements(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        email: str,
        org_id: str | None = None,
    ) -> List[EngagementDetailRecord]:
        """Fetch engagements accessible to the current user.

        Sources:
        - Active engagement memberships
        - Active auditor access tokens by email
        - Active GRC engagement grants
        - Active GRC framework grants matching the engagement deployment
        """
        cte = _accessible_engagements_cte(include_org_filter=org_id is not None)
        params: list[object] = [UUID(user_id), email]
        if org_id is not None:
            params.append(UUID(org_id))
        rows = await connection.fetch(
            f"""
            {cte}
            SELECT
                v.*,
                fd.workspace_id::text AS workspace_id,
                w.name AS workspace_name,
                org.name AS org_name
            FROM {SCHEMA}."40_vw_engagement_detail" v
            JOIN accessible_engagements ae ON ae.id = v.id
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = v.framework_deployment_id::uuid
            LEFT JOIN "03_auth_manage"."34_fct_workspaces" w
              ON w.id = fd.workspace_id
            LEFT JOIN "03_auth_manage"."29_fct_orgs" org
              ON org.id = v.org_id
            ORDER BY v.created_at DESC
            """,
            *params,
        )
        return [_row_to_detail(r) for r in rows]

    async def list_review_queue_for_user(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        email: str,
        org_id: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        cte = _accessible_engagements_cte(include_org_filter=org_id is not None)
        params: list[object] = [UUID(user_id), email]
        if org_id is not None:
            params.append(UUID(org_id))
        params.append(limit)
        rows = await connection.fetch(
            f"""
            {cte}
            SELECT
                t.id::text as task_id,
                t.title,
                c.control_code,
                COALESCE(fp.property_value, f.framework_code) as framework_name,
                t.due_date::text as due_date,
                t.status_code
            FROM "08_tasks"."40_vw_task_detail" t
            JOIN "05_grc_library"."13_fct_controls" c
              ON t.entity_id = c.id AND t.entity_type = 'control'
            JOIN "05_grc_library"."31_lnk_framework_version_controls" lvc
              ON lvc.control_id = c.id
            JOIN "05_grc_library"."10_fct_frameworks" f
              ON f.id = c.framework_id
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fp
              ON fp.framework_id = f.id AND fp.property_key = 'name'
            JOIN {SCHEMA}."10_fct_audit_engagements" e
              ON e.framework_deployment_id = lvc.framework_version_id
            JOIN accessible_engagements ae
              ON ae.id = e.id
            WHERE t.status_code IN ('ready_for_auditor', 'auditor_reviewing')
              AND t.is_deleted = FALSE
            ORDER BY t.due_date ASC NULLS LAST
            LIMIT ${len(params)}
            """,
            *params,
        )
        return [dict(r) for r in rows]

    async def get_engagement_by_id(
        self, connection: asyncpg.Connection, engagement_id: str, tenant_key: str
    ) -> Optional[EngagementDetailRecord]:
        row = await connection.fetchrow(
            f"""
            SELECT 
                v.*, 
                org.name AS org_name,
                fd.workspace_id::text AS workspace_id,
                w.name AS workspace_name
            FROM {SCHEMA}."40_vw_engagement_detail" v
            LEFT JOIN "03_auth_manage"."29_fct_orgs" org ON org.id = v.org_id 
            LEFT JOIN "05_grc_library"."16_fct_framework_deployments" fd
              ON fd.id = v.framework_deployment_id::uuid
            LEFT JOIN "03_auth_manage"."34_fct_workspaces" w
              ON w.id = fd.workspace_id
            WHERE v.id = $1 AND v.tenant_key = $2
            """,
            UUID(engagement_id),
            tenant_key
        )
        return _row_to_detail(row) if row else None

    async def create_engagement(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        engagement_code: str,
        framework_id: str,
        framework_deployment_id: str,
        status_code: str,
        target_completion_date: Optional[date],
        created_by: str,
        now: datetime,
    ) -> EngagementRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."10_fct_audit_engagements"
                (id, tenant_key, org_id, engagement_code, framework_id, framework_deployment_id,
                 status_code, target_completion_date, is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, TRUE, FALSE, $9, $9, $10, $10)
            RETURNING id, tenant_key, org_id::text, engagement_code, framework_id::text,
                      framework_deployment_id::text, status_code, target_completion_date::text,
                      is_active, created_at::text, updated_at::text, created_by::text
            """,
            UUID(id),
            tenant_key,
            UUID(org_id),
            engagement_code,
            UUID(framework_id),
            UUID(framework_deployment_id),
            status_code,
            target_completion_date,
            now,
            UUID(created_by),
        )
        return _row_to_engagement(row)

    async def update_engagement(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        *,
        status_code: Optional[str] = None,
        target_completion_date: Optional[date] = None,
        updated_by: str,
        now: datetime,
    ) -> bool:
        fields = ["updated_at = $1", "updated_by = $2"]
        values = [now, UUID(updated_by)]
        idx = 3

        if status_code:
            fields.append(f"status_code = ${idx}")
            values.append(status_code)
            idx += 1
        if target_completion_date is not None:
             fields.append(f"target_completion_date = ${idx}")
             values.append(target_completion_date)
             idx += 1

        values.append(UUID(engagement_id))
        values.append(tenant_key)
        set_clause = ", ".join(fields)

        result = await connection.execute(
            f'UPDATE {SCHEMA}."10_fct_audit_engagements" SET {set_clause} WHERE id = ${idx} AND tenant_key = ${idx+1}',
            *values,
        )
        return result != "UPDATE 0"

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        properties: dict[str, str],
        now: datetime,
    ) -> None:
        if not properties:
            return
        
        # Verify ownership before upsert (EAV tables don't have tenant_key directly)
        exists = await connection.fetchval(
            f'SELECT 1 FROM {SCHEMA}."10_fct_audit_engagements" WHERE id = $1 AND tenant_key = $2',
            UUID(engagement_id), tenant_key
        )
        if not exists:
            return

        rows = [
            (UUID(engagement_id), key, str(value), now)
            for key, value in properties.items()
        ]
        
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."22_dtl_engagement_properties"
                (engagement_id, property_key, property_value, updated_at)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (engagement_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at
            """,
            rows,
        )

    async def create_auditor_token(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        auditor_email: str,
        token_hash: str,
        expires_at: datetime,
    ) -> AuditAccessTokenRecord:
        # Verify ownership
        exists = await connection.fetchval(
            f'SELECT 1 FROM {SCHEMA}."10_fct_audit_engagements" WHERE id = $1 AND tenant_key = $2',
            UUID(engagement_id), tenant_key
        )
        if not exists:
            # Service layer will handle this branch
            return None

        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."11_fct_audit_access_tokens"
                (engagement_id, auditor_email, token_hash, expires_at, created_at)
            VALUES ($1, $2, $3, $4, now())
            RETURNING id::text, engagement_id::text, auditor_email, expires_at, is_revoked, created_at
            """,
            UUID(engagement_id),
            auditor_email,
            token_hash,
            expires_at,
        )
        return AuditAccessTokenRecord(
            id=row["id"],
            engagement_id=row["engagement_id"],
            auditor_email=row["auditor_email"],
            expires_at=row["expires_at"],
            is_revoked=row["is_revoked"],
            created_at=row["created_at"],
        )

    async def list_access_tokens(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        include_revoked: bool = True,
    ) -> List[AuditAccessTokenRecord]:
        rows = await connection.fetch(
            f"""
            SELECT t.id::text, t.engagement_id::text, t.auditor_email,
                   t.expires_at, t.is_revoked,
                   t.last_accessed_at, t.created_at
            FROM {SCHEMA}."11_fct_audit_access_tokens" t
            JOIN {SCHEMA}."10_fct_audit_engagements" e ON e.id = t.engagement_id
            WHERE t.engagement_id = $1
              AND e.tenant_key = $3
              AND ($2 OR (t.is_revoked = FALSE AND t.expires_at > NOW()))
            ORDER BY t.created_at DESC
            """,
            UUID(engagement_id),
            include_revoked,
            tenant_key
        )
        return [_row_to_token(r) for r in rows]

    async def revoke_access_token(
        self,
        connection: asyncpg.Connection,
        token_id: str,
        tenant_key: str,
        revoked_by: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."11_fct_audit_access_tokens" t
            SET is_revoked = TRUE, revoked_at = now(), revoked_by = $2
            FROM {SCHEMA}."10_fct_audit_engagements" e
            WHERE t.id = $1 AND t.engagement_id = e.id AND e.tenant_key = $3 AND t.is_revoked = FALSE
            """,
            UUID(token_id),
            UUID(revoked_by),
            tenant_key
        )
        return result != "UPDATE 0"

    async def list_auditor_requests(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        status: Optional[str] = None,
    ) -> List[AuditorRequestRecord]:
        """Fetch requests with the auditor email joined from access tokens."""
        conditions = ["r.engagement_id = $1", "e.tenant_key = $2", "r.is_deleted = FALSE"]
        args: list = [UUID(engagement_id), tenant_key]
        idx = 3
        if status:
            conditions.append(f"r.request_status = ${idx}")
            args.append(status)
            idx += 1

        where = " AND ".join(conditions)
        rows = await connection.fetch(
            f"""
            SELECT
                r.id::text,
                r.engagement_id::text,
                r.requested_by_token_id::text,
                t.auditor_email,
                r.control_id::text,
                r.request_status,
                r.fulfilled_at,
                r.fulfilled_by::text,
                r.is_deleted,
                r.created_at,
                r.updated_at,
                r.task_id::text,
                desc_prop.property_value  AS request_description,
                note_prop.property_value  AS response_notes
            FROM {SCHEMA}."20_trx_auditor_requests" r
            JOIN {SCHEMA}."11_fct_audit_access_tokens" t
                ON t.id = r.requested_by_token_id
            JOIN {SCHEMA}."10_fct_audit_engagements" e
                ON e.id = r.engagement_id
            LEFT JOIN {SCHEMA}."23_dtl_request_properties" desc_prop
                ON desc_prop.request_id = r.id AND desc_prop.property_key = 'request_description'
            LEFT JOIN {SCHEMA}."23_dtl_request_properties" note_prop
                ON note_prop.request_id = r.id AND note_prop.property_key = 'response_notes'
            WHERE {where}
            ORDER BY r.created_at DESC
            """,
            *args,
        )
        return [_row_to_request(r) for r in rows]

    async def get_open_auditor_request_id(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        token_id: str,
        control_id: str | None,
        task_id: str | None = None,
    ) -> str | None:
        return await connection.fetchval(
            f"""
            SELECT id::text
            FROM {SCHEMA}."20_trx_auditor_requests"
            WHERE engagement_id = $1::uuid
              AND requested_by_token_id = $2::uuid
              AND (
                    ($3::uuid IS NULL AND control_id IS NULL)
                  OR control_id = $3::uuid
              )
              AND (
                    ($4::uuid IS NULL AND task_id IS NULL)
                 OR task_id = $4::uuid
              )
              AND request_status = 'open'
              AND is_deleted = FALSE
            LIMIT 1
            """,
            UUID(engagement_id), UUID(token_id), 
            UUID(control_id) if control_id else None,
            UUID(task_id) if task_id else None,
        )

    async def get_latest_dismissed_auditor_request_description(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        token_id: str,
        control_id: str | None,
    ) -> str | None:
        return await connection.fetchval(
            f"""
            SELECT prop.property_value
            FROM {SCHEMA}."20_trx_auditor_requests" r
            LEFT JOIN {SCHEMA}."23_dtl_request_properties" prop
              ON prop.request_id = r.id
             AND prop.property_key = 'request_description'
            WHERE r.engagement_id = $1::uuid
              AND r.requested_by_token_id = $2::uuid
              AND (
                    ($3::uuid IS NULL AND r.control_id IS NULL)
                 OR r.control_id = $3::uuid
              )
              AND r.request_status = 'dismissed'
              AND r.is_deleted = FALSE
            ORDER BY COALESCE(r.fulfilled_at, r.updated_at, r.created_at) DESC
            LIMIT 1
            """,
            UUID(engagement_id),
            UUID(token_id),
            UUID(control_id) if control_id else None,
        )

    async def get_latest_dismissed_auditor_request_at(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        token_id: str,
        control_id: str | None,
    ) -> datetime | None:
        return await connection.fetchval(
            f"""
            SELECT COALESCE(r.fulfilled_at, r.updated_at, r.created_at)
            FROM {SCHEMA}."20_trx_auditor_requests" r
            WHERE r.engagement_id = $1::uuid
              AND r.requested_by_token_id = $2::uuid
              AND (
                    ($3::uuid IS NULL AND r.control_id IS NULL)
                 OR r.control_id = $3::uuid
              )
              AND r.request_status = 'dismissed'
              AND r.is_deleted = FALSE
            ORDER BY COALESCE(r.fulfilled_at, r.updated_at, r.created_at) DESC
            LIMIT 1
            """,
            UUID(engagement_id),
            UUID(token_id),
            UUID(control_id) if control_id else None,
        )

    async def list_engagement_controls(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        auditor_only: bool = False,
        viewer_membership_id: str | None = None,
    ) -> List[dict]:
        """Fetch all controls for the engagement's deployment with verification status.

        Args:
            connection: Active asyncpg database connection.
            engagement_id: UUID of the engagement.
            tenant_key: Tenant key for access control.
            auditor_only: When True, only count evidence marked auditor_access=TRUE.

        Returns:
            List of control dicts with verification status and evidence counts.
        """
        evidence_filter = ""
        if auditor_only:
            evidence_filter = f"""
                AND (
                    att.auditor_access = TRUE
                    OR EXISTS (
                        SELECT 1
                        FROM {SCHEMA}."13_lnk_evidence_access_grants" g
                        WHERE g.engagement_id = e.id
                          AND g.attachment_id = att.id
                          AND g.membership_id = $3::uuid
                          AND g.revoked_at IS NULL
                          AND g.is_active = TRUE
                          AND g.is_deleted = FALSE
                          AND (g.expires_at IS NULL OR g.expires_at > NOW())
                    )
                )
            """
        sql = f"""
            SELECT
                c.id::text,
                c.control_code,
                c.control_type,
                cp_name.property_value  AS name,
                cp_desc.property_value  AS description,
                cat.name                AS category_name,
                crit.name               AS criticality_name,
                v.outcome               AS verification_status,
                v.verified_at::text,
                (SELECT count(*)::int FROM {SCHEMA}."20_trx_auditor_requests" r
                 WHERE r.engagement_id = e.id AND r.control_id = c.id AND r.request_status = 'open') AS open_requests_count,
                (SELECT count(*)::int FROM "09_attachments"."01_fct_attachments" att
                 WHERE att.entity_id = c.id AND att.entity_type = 'control' AND att.is_deleted = false{evidence_filter}) AS evidence_count
            FROM {SCHEMA}."10_fct_audit_engagements" e
            JOIN "05_grc_library"."16_fct_framework_deployments" fd
                ON fd.id = e.framework_deployment_id
            JOIN "05_grc_library"."31_lnk_framework_version_controls" lvc
                ON lvc.framework_version_id = fd.deployed_version_id
            JOIN "05_grc_library"."13_fct_controls" c
                ON c.id = lvc.control_id AND c.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp_name
                ON cp_name.control_id = c.id AND cp_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp_desc
                ON cp_desc.control_id = c.id AND cp_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."04_dim_control_categories" cat
                ON cat.code = c.control_category_code
            LEFT JOIN "05_grc_library"."05_dim_control_criticalities" crit
                ON crit.code = c.criticality_code
            LEFT JOIN {SCHEMA}."21_trx_auditor_verifications" v
                ON v.engagement_id = e.id AND v.control_id = c.id
            WHERE e.id = $1 AND e.tenant_key = $2
            ORDER BY lvc.sort_order ASC, c.control_code ASC
        """
        query_args: list[object] = [UUID(engagement_id), tenant_key]
        if auditor_only:
            query_args.append(UUID(viewer_membership_id) if viewer_membership_id else None)
        rows = await connection.fetch(sql, *query_args)
        return [dict(r) for r in rows]

    async def fulfill_auditor_request(
        self,
        connection: asyncpg.Connection,
        request_id: str,
        tenant_key: str,
        *,
        action: str,  # "fulfill" | "dismiss"
        fulfilled_by: str,
        attachment_ids: Optional[list[str]] = None,
        response_notes: Optional[str] = None,
        now: datetime,
    ) -> bool:
        new_status = "fulfilled" if action == "fulfill" else "dismissed"
        membership_id: str | None = None
        locked_request = await self._lock_request_for_review(
            connection,
            request_id=request_id,
            tenant_key=tenant_key,
        )
        if not locked_request or locked_request["request_status"] != "open":
            return False

        # Verify attachment context ownership if provided
        if action == "fulfill" and attachment_ids:
            membership_id = locked_request["membership_id"]
            if not membership_id:
                return False

            for attachment_id in attachment_ids:
                # Verify attachment is owned by this tenant and linked to the same
                # engagement or control context as the request.
                att_context_match = await connection.fetchval(
                    """
                    SELECT 1
                    FROM "09_attachments"."01_fct_attachments"
                    WHERE id = $1
                      AND tenant_key = $2
                      AND (
                             (entity_type = 'engagement' AND entity_id = $3::uuid)
                            OR (entity_type = 'control' AND entity_id = $4::uuid)
                            OR (entity_type = 'task' AND entity_id = $5::uuid)
                      )
                    """,
                    UUID(attachment_id),
                    tenant_key,
                    locked_request["engagement_id"],
                    locked_request["control_id"],
                    locked_request["task_id"],
                )
                if not att_context_match:
                    # Unauthorized attachment linkage for one of the items
                    return False

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_trx_auditor_requests" r
            SET request_status = $2,
                fulfilled_at   = $3,
                fulfilled_by   = $4,
                attachment_id  = $5,
                updated_at     = $3
            FROM {SCHEMA}."10_fct_audit_engagements" e
            WHERE r.id = $1 AND r.engagement_id = e.id AND e.tenant_key = $6 
              AND r.request_status = 'open' AND r.is_deleted = FALSE
            """,
            UUID(request_id),
            new_status,
            now,
            UUID(fulfilled_by),
            UUID(attachment_ids[0]) if attachment_ids else None, # Store first one as primary
            tenant_key
        )
        if result == "UPDATE 0":
            return False

        if action == "fulfill" and attachment_ids and membership_id:
            for attachment_id in attachment_ids:
                await connection.execute(
                    f"""
                    INSERT INTO {SCHEMA}."13_lnk_evidence_access_grants" (
                        engagement_id,
                        tenant_key,
                        request_id,
                        membership_id,
                        attachment_id,
                        granted_at,
                        is_active,
                        is_deleted,
                        created_at,
                        updated_at,
                        created_by,
                        updated_by
                    )
                    SELECT
                        r.engagement_id,
                        $2,
                        r.id,
                        $3::uuid,
                        $4::uuid,
                        $5,
                        TRUE,
                        FALSE,
                        $5,
                        $5,
                        $6::uuid,
                        $6::uuid
                    FROM {SCHEMA}."20_trx_auditor_requests" r
                    WHERE r.id = $1::uuid
                    ON CONFLICT (engagement_id, membership_id, attachment_id)
                    WHERE revoked_at IS NULL
                      AND is_active = TRUE
                      AND is_deleted = FALSE
                    DO UPDATE SET
                        updated_at = EXCLUDED.updated_at,
                        updated_by = EXCLUDED.updated_by;
                    """,
                    UUID(request_id),
                    tenant_key,
                    membership_id,
                    attachment_id,
                    now,
                    fulfilled_by,
                )
        # Upsert response_notes if provided
        if response_notes:
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."23_dtl_request_properties"
                    (request_id, property_key, property_value, updated_at)
                VALUES ($1, 'response_notes', $2, $3)
                ON CONFLICT (request_id, property_key)
                    DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at
                """,
                UUID(request_id),
                response_notes,
                now,
            )
        return True

    async def revoke_auditor_request_access(
        self,
        connection: asyncpg.Connection,
        request_id: str,
        tenant_key: str,
        *,
        revoked_by: str,
        response_notes: Optional[str] = None,
        now: datetime,
    ) -> bool:
        request_row = await self._lock_request_for_review(
            connection,
            request_id=request_id,
            tenant_key=tenant_key,
        )
        if not request_row or request_row["request_status"] != "fulfilled":
            return False

        revoke_result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."13_lnk_evidence_access_grants" g
            SET revoked_at = $2,
                revoked_by = $3::uuid,
                is_active = FALSE,
                updated_at = $2,
                updated_by = $3::uuid
            WHERE g.request_id = $1::uuid
              AND g.revoked_at IS NULL
              AND g.is_deleted = FALSE
              AND g.is_active = TRUE
            """,
            UUID(request_id),
            now,
            UUID(revoked_by),
        )
        if revoke_result == "UPDATE 0":
            return False

        await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_trx_auditor_requests"
            SET updated_at = $2
            WHERE id = $1::uuid
            """,
            UUID(request_id),
            now,
        )

        if response_notes:
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."23_dtl_request_properties"
                    (request_id, property_key, property_value, updated_at)
                VALUES ($1::uuid, 'response_notes', $2, $3)
                ON CONFLICT (request_id, property_key)
                    DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at
                """,
                UUID(request_id),
                response_notes,
                now,
            )
        return True

    async def get_engagement_by_token(self, connection: asyncpg.Connection, token_hash: str) -> Optional[EngagementDetailRecord]:
        sql = f"""
            SELECT v.* 
            FROM {SCHEMA}."40_vw_engagement_detail" v
            JOIN {SCHEMA}."11_fct_audit_access_tokens" t ON v.id = t.engagement_id
            WHERE t.token_hash = $1 AND t.expires_at > NOW() AND t.is_revoked = FALSE
        """
        row = await connection.fetchrow(sql, token_hash)
        if row:
            return _row_to_detail(row)
        return None

    async def validate_auditor_access_and_get_tenant(
        self, connection: asyncpg.Connection, engagement_id: str, email: str
    ) -> Optional[str]:
        """Verify that the auditor has an active, non-revoked token for this engagement."""
        row = await connection.fetchrow(
            f"""
            SELECT e.tenant_key
            FROM {SCHEMA}."10_fct_audit_engagements" e
            JOIN {SCHEMA}."11_fct_audit_access_tokens" t ON t.engagement_id = e.id
            WHERE e.id = $1 AND t.auditor_email = $2
              AND t.is_revoked = FALSE AND t.expires_at > NOW()
            """,
            UUID(engagement_id), email
        )
        return row["tenant_key"] if row else None

    async def upsert_control_verification(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        control_id: str,
        token_id: str,
        outcome: str,
        observations: str | None = None,
        finding_details: str | None = None,
        now: datetime,
    ) -> bool:
        # Verify ownership
        exists = await connection.fetchval(
            f'SELECT 1 FROM {SCHEMA}."10_fct_audit_engagements" WHERE id = $1 AND tenant_key = $2',
            UUID(engagement_id), tenant_key
        )
        if not exists:
            return False

        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."21_trx_auditor_verifications" (
                engagement_id, control_id, verified_by_token_id, outcome, observations, finding_details, verified_at, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $7)
            ON CONFLICT (engagement_id, control_id)
            DO UPDATE SET 
                outcome = EXCLUDED.outcome,
                observations = EXCLUDED.observations,
                finding_details = EXCLUDED.finding_details,
                verified_by_token_id = EXCLUDED.verified_by_token_id,
                verified_at = EXCLUDED.verified_at
            """,
            UUID(engagement_id), UUID(control_id), UUID(token_id), outcome, observations, finding_details, now
        )
        return True

    async def create_auditor_request(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        token_id: str,
        control_id: str | None,
        task_id: str | None = None,
        description: str,
        now: datetime,
    ) -> str:
        # Verify ownership
        exists = await connection.fetchval(
            f'SELECT 1 FROM {SCHEMA}."10_fct_audit_engagements" WHERE id = $1 AND tenant_key = $2',
            UUID(engagement_id), tenant_key
        )
        if not exists:
            raise ValueError("Forbidden")

        from uuid import uuid4
        request_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_trx_auditor_requests" (
                id, engagement_id, requested_by_token_id, control_id, task_id, request_status, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, 'open', $6, $6)
            """,
            UUID(request_id), UUID(engagement_id), UUID(token_id), 
            UUID(control_id) if control_id else None,
            UUID(task_id) if task_id else None,
            now
        )
        # Add property
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."23_dtl_request_properties" (id, request_id, property_key, property_value, updated_at)
            VALUES ($1, $2, 'request_description', $3, $4)
            """,
            uuid4(), UUID(request_id), description, now
        )
        return request_id

    async def list_control_evidence(
        self,
        connection: asyncpg.Connection,
        *,
        engagement_id: str,
        tenant_key: str,
        control_id: str,
        auditor_only: bool = False,
        viewer_membership_id: str | None = None,
    ) -> list[dict]:
        """List attachments linked to fulfilled auditor requests for this control.

        Args:
            connection: Active asyncpg database connection.
            engagement_id: UUID of the engagement.
            tenant_key: Tenant key.
            control_id: UUID of the control.
            auditor_only: When True, only return evidence marked auditor_access=TRUE.

        Returns:
            List of evidence dicts.
        """
        rows = await connection.fetch(
            f"""
            SELECT
                att.id::text,
                att.original_filename AS filename,
                att.content_type,
                att.file_size_bytes AS size,
                att.created_at::text,
                grant_link.request_id::text AS request_id
            FROM "09_attachments"."01_fct_attachments" att
            JOIN "12_engagements"."10_fct_audit_engagements" e
              ON e.id = $1
            LEFT JOIN "12_engagements"."13_lnk_evidence_access_grants" grant_link
              ON grant_link.engagement_id = e.id
             AND grant_link.attachment_id = att.id
              AND grant_link.membership_id = $5::uuid
              AND grant_link.revoked_at IS NULL
              AND grant_link.is_active = TRUE
              AND grant_link.is_deleted = FALSE
              AND (grant_link.expires_at IS NULL OR grant_link.expires_at > NOW())
              WHERE e.tenant_key = $3
               AND (
                     (att.entity_type = 'engagement' AND att.entity_id = $1)
                  OR (att.entity_type = 'control' AND att.entity_id = $2)
               )
               AND att.is_deleted = FALSE
               AND (
                     $4::boolean = FALSE
                  OR att.auditor_access = TRUE
                 OR grant_link.id IS NOT NULL
              )
            ORDER BY att.created_at DESC
            """,
            UUID(engagement_id),
            UUID(control_id),
            tenant_key,
            auditor_only,
            UUID(viewer_membership_id) if viewer_membership_id else None,
        )
        return [dict(r) for r in rows]

    async def get_control_verification(
        self,
        connection: asyncpg.Connection,
        engagement_id: str,
        tenant_key: str,
        control_id: str,
    ) -> Optional[dict]:
        row = await connection.fetchrow(
            f"""
            SELECT v.outcome, v.observations, v.finding_details as findings, v.verified_at
            FROM {SCHEMA}."21_trx_auditor_verifications" v
            JOIN {SCHEMA}."10_fct_audit_engagements" e ON e.id = v.engagement_id
            WHERE v.engagement_id = $1 AND v.control_id = $2 AND e.tenant_key = $3
            """,
            UUID(engagement_id),
            UUID(control_id),
            tenant_key
        )
        return dict(row) if row else None


def _row_to_detail(r) -> EngagementDetailRecord:
    """Safely map a row to an EngagementDetailRecord, handling potentially missing columns from older view versions."""
    return EngagementDetailRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        org_id=str(r["org_id"]),
        org_name=r.get("org_name") or "N/A",
        workspace_id=str(r["workspace_id"]) if r.get("workspace_id") else None,
        workspace_name=r.get("workspace_name"),
        engagement_code=r.get("engagement_code") or "N/A",
        framework_id=str(r.get("framework_id") or "00000000-0000-0000-0000-000000000000"),
        framework_deployment_id=str(r.get("framework_deployment_id") or "00000000-0000-0000-0000-000000000000"),
        status_code=r.get("status_code") or "draft",
        status_name=r.get("status_name") or "Draft",
        target_completion_date=str(r.get("target_completion_date")) if r.get("target_completion_date") else None,
        total_controls_count=r.get("total_controls_count", 0),
        verified_controls_count=r.get("verified_controls_count", 0),
        open_requests_count=r.get("open_requests_count", 0),
        engagement_name=r.get("engagement_name") or "",
        auditor_firm=r.get("auditor_firm") or "",
        scope_description=r.get("scope_description") or "",
        audit_period_start=str(r.get("audit_period_start")) if r.get("audit_period_start") else None,
        audit_period_end=str(r.get("audit_period_end")) if r.get("audit_period_end") else None,
        lead_grc_sme=r.get("lead_grc_sme") or "",
        engagement_type=r.get("engagement_type"),
        is_active=r.get("is_active", True),
        created_at=str(r.get("created_at") or ""),
        updated_at=str(r.get("updated_at") or ""),
    )


def _row_to_engagement(r) -> EngagementRecord:
    return EngagementRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        org_id=str(r["org_id"]),
        engagement_code=r["engagement_code"],
        framework_id=str(r["framework_id"]),
        framework_deployment_id=str(r["framework_deployment_id"]),
        status_code=r["status_code"],
        target_completion_date=r["target_completion_date"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )


def _row_to_token(r) -> AuditAccessTokenRecord:
    return AuditAccessTokenRecord(
        id=str(r["id"]),
        engagement_id=str(r["engagement_id"]),
        auditor_email=r["auditor_email"],
        expires_at=r["expires_at"],
        is_revoked=r["is_revoked"],
        last_accessed_at=r["last_accessed_at"],
        created_at=r["created_at"],
    )


def _row_to_request(r) -> AuditorRequestRecord:
    return AuditorRequestRecord(
        id=str(r["id"]),
        engagement_id=str(r["engagement_id"]),
        requested_by_token_id=str(r["requested_by_token_id"]),
        auditor_email=r["auditor_email"],
        control_id=str(r["control_id"]) if r["control_id"] else None,
        request_status=r["request_status"],
        request_description=r["request_description"],
        response_notes=r["response_notes"],
        fulfilled_at=str(r["fulfilled_at"]) if r["fulfilled_at"] else None,
        fulfilled_by=str(r["fulfilled_by"]) if r["fulfilled_by"] else None,
        task_id=str(r["task_id"]) if r.get("task_id") else None,
        is_deleted=r["is_deleted"],
        created_at=str(r["created_at"]),
        updated_at=str(r["updated_at"]),
    )
