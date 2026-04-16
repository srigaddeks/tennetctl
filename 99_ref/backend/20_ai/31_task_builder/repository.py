"""Repository queries for the AI task builder module."""

from __future__ import annotations

import json

import asyncpg
from importlib import import_module


instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods
_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.task_builder.repository")

_CONTROLS = '"05_grc_library"."13_fct_controls"'
_CONTROL_PROPS = '"05_grc_library"."23_dtl_control_properties"'
_FRAMEWORKS = '"05_grc_library"."10_fct_frameworks"'
_FRAMEWORK_PROPS = '"05_grc_library"."20_dtl_framework_properties"'
_TASK_DETAIL_VIEW = '"08_tasks"."40_vw_task_detail"'


@instrument_class_methods(
    namespace="ai.task_builder.repository",
    logger_name="backend.ai.task_builder.repository.instrumentation",
)
class TaskBuilderRepository:
    async def get_framework(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT f.id::text,
                   f.framework_code,
                   (
                       SELECT property_value
                       FROM {_FRAMEWORK_PROPS}
                       WHERE framework_id = f.id AND property_key = 'name'
                   ) AS name
            FROM {_FRAMEWORKS} f
            WHERE f.id = $1::uuid
              AND f.tenant_key = $2
            """,
            framework_id,
            tenant_key,
        )
        return dict(row) if row else None

    async def list_controls(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        tenant_key: str,
        control_ids: list[str] | None = None,
    ) -> list[dict]:
        conditions = [
            "c.framework_id = $1::uuid",
            "c.tenant_key = $2",
            "c.is_active = TRUE",
            "c.is_deleted = FALSE",
        ]
        params: list[object] = [framework_id, tenant_key]

        if control_ids:
            conditions.append("c.id = ANY($3::uuid[])")
            params.append(control_ids)

        where_clause = " AND ".join(conditions)
        rows = await connection.fetch(
            f"""
            WITH test_summary AS (
                SELECT
                    tcm.control_id,
                    COUNT(DISTINCT tcm.control_test_id) FILTER (WHERE NOT ct.is_deleted) AS test_count,
                    COUNT(DISTINCT le.id) FILTER (
                        WHERE le.result_status IN ('fail', 'partial', 'error')
                    ) AS failing_execution_count,
                    COUNT(DISTINCT le.id) FILTER (
                        WHERE le.result_status = 'pass'
                    ) AS passing_execution_count,
                    MAX(le.executed_at) AS latest_execution_at,
                    STRING_AGG(DISTINCT le.result_status, ', ' ORDER BY le.result_status)
                        FILTER (WHERE le.result_status IS NOT NULL) AS latest_result_statuses,
                    STRING_AGG(
                        DISTINCT LEFT(NULLIF(TRIM(le.evidence_summary), ''), 160),
                        ' || '
                    ) FILTER (
                        WHERE NULLIF(TRIM(le.evidence_summary), '') IS NOT NULL
                    ) AS evidence_summaries
                FROM "05_grc_library"."30_lnk_test_control_mappings" tcm
                LEFT JOIN "05_grc_library"."14_fct_control_tests" ct
                    ON ct.id = tcm.control_test_id
                LEFT JOIN "05_grc_library"."43_vw_latest_test_execution" le
                    ON le.control_test_id = tcm.control_test_id
                   AND le.control_id = tcm.control_id
                GROUP BY tcm.control_id
            )
            SELECT
                c.id::text,
                c.control_code,
                c.control_type,
                c.criticality_code,
                c.automation_potential,
                (
                    SELECT property_value
                    FROM {_CONTROL_PROPS}
                    WHERE control_id = c.id AND property_key = 'name'
                ) AS name,
                (
                    SELECT property_value
                    FROM {_CONTROL_PROPS}
                    WHERE control_id = c.id AND property_key = 'description'
                ) AS description,
                (
                    SELECT property_value
                    FROM {_CONTROL_PROPS}
                    WHERE control_id = c.id AND property_key = 'implementation_guidance'
                ) AS implementation_guidance,
                COALESCE(ts.test_count, 0) AS test_count,
                COALESCE(ts.failing_execution_count, 0) AS failing_execution_count,
                COALESCE(ts.passing_execution_count, 0) AS passing_execution_count,
                ts.latest_execution_at::text AS latest_execution_at,
                ts.latest_result_statuses,
                ts.evidence_summaries
            FROM {_CONTROLS} c
            LEFT JOIN test_summary ts
                ON ts.control_id = c.id
            WHERE {where_clause}
            ORDER BY c.sort_order, c.control_code
            """,
            *params,
        )
        return [dict(row) for row in rows]

    async def list_existing_non_terminal_tasks(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        control_ids: list[str],
    ) -> list[dict]:
        if not control_ids:
            return []

        rows = await connection.fetch(
            f"""
            SELECT
                entity_id::text AS control_id,
                task_type_code,
                status_code,
                title,
                description,
                acceptance_criteria,
                remediation_plan,
                due_date::text AS due_date
            FROM {_TASK_DETAIL_VIEW}
            WHERE tenant_key = $1
              AND entity_type = 'control'
              AND entity_id = ANY($2::uuid[])
              AND is_terminal = FALSE
              AND is_active = TRUE
              AND is_deleted = FALSE
            ORDER BY entity_id, created_at
            """,
            tenant_key,
            control_ids,
        )
        return [dict(row) for row in rows]


# ── Session repository ───────────────────────────────────────────────────────

_SESSIONS = '"20_ai"."65_fct_task_builder_sessions"'

_SESSION_COLS = """
    id::text, tenant_key, user_id::text, status,
    framework_id::text, scope_org_id::text, scope_workspace_id::text,
    user_context, attachment_ids, control_ids,
    proposed_tasks, apply_result,
    job_id::text, error_message,
    activity_log,
    created_at::text, updated_at::text, created_by::text
"""


def _row_to_dict(row) -> dict:
    d = dict(row)
    for key in ("attachment_ids", "control_ids", "proposed_tasks", "apply_result", "activity_log"):
        val = d.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except Exception:
                pass
    return d


class TaskBuilderSessionRepository:

    async def create_session(
        self,
        conn: asyncpg.Connection,
        *,
        session_id: str,
        tenant_key: str,
        user_id: str,
        framework_id: str,
        scope_org_id: str,
        scope_workspace_id: str,
        user_context: str,
        attachment_ids: list,
        control_ids: list | None,
        now: str,
    ) -> dict:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_SESSIONS} (
                id, tenant_key, user_id, status,
                framework_id, scope_org_id, scope_workspace_id,
                user_context, attachment_ids, control_ids,
                created_at, updated_at, created_by
            ) VALUES (
                $1, $2, $3::uuid, 'idle',
                $4::uuid, $5::uuid, $6::uuid,
                $7, $8::jsonb, $9::jsonb,
                $10, $11, $3::uuid
            )
            RETURNING {_SESSION_COLS}
            """,
            session_id, tenant_key, user_id,
            framework_id, scope_org_id, scope_workspace_id,
            user_context,
            attachment_ids,
            control_ids if control_ids else None,
            now, now,
        )
        return _row_to_dict(row)

    async def get_by_id(
        self, conn: asyncpg.Connection, session_id: str, tenant_key: str
    ) -> dict | None:
        row = await conn.fetchrow(
            f"SELECT {_SESSION_COLS} FROM {_SESSIONS} WHERE id = $1::uuid AND tenant_key = $2",
            session_id, tenant_key,
        )
        return _row_to_dict(row) if row else None

    async def list_sessions(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
        framework_id: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        where = ["tenant_key = $1", "user_id = $2::uuid"]
        args: list[object] = [tenant_key, user_id]
        idx = 3
        if framework_id is not None:
            where.append(f"framework_id = ${idx}::uuid")
            args.append(framework_id)
            idx += 1
        if scope_org_id is not None:
            where.append(f"scope_org_id = ${idx}::uuid")
            args.append(scope_org_id)
            idx += 1
        if scope_workspace_id is not None:
            where.append(f"scope_workspace_id = ${idx}::uuid")
            args.append(scope_workspace_id)
            idx += 1

        where_sql = " AND ".join(where)
        count_row = await conn.fetchrow(
            f"SELECT COUNT(*)::int AS total FROM {_SESSIONS} WHERE {where_sql}",
            *args,
        )
        total = count_row["total"] if count_row else 0

        rows = await conn.fetch(
            f"""
            SELECT {_SESSION_COLS}
            FROM {_SESSIONS}
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *args, limit, offset,
        )
        return [_row_to_dict(r) for r in rows], total

    async def update_status(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        status: str,
        now: str,
    ) -> None:
        await conn.execute(
            f"UPDATE {_SESSIONS} SET status = $1, updated_at = $2 WHERE id = $3::uuid AND tenant_key = $4",
            status, now, session_id, tenant_key,
        )

    async def set_job(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        job_id: str,
        status: str,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET job_id = $1::uuid, status = $2, updated_at = $3
            WHERE id = $4::uuid AND tenant_key = $5
            """,
            job_id, status, now, session_id, tenant_key,
        )

    async def save_proposed_tasks(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        proposed_tasks: list,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET proposed_tasks = $1::jsonb, status = 'reviewing', updated_at = $2
            WHERE id = $3::uuid AND tenant_key = $4
            """,
            proposed_tasks, now, session_id, tenant_key,
        )

    async def save_apply_result(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        apply_result: dict,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET apply_result = $1::jsonb, status = 'complete', updated_at = $2
            WHERE id = $3::uuid AND tenant_key = $4
            """,
            apply_result, now, session_id, tenant_key,
        )

    async def append_activity_log(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        events: list[dict],
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET activity_log = COALESCE(activity_log, '[]'::jsonb) || $1::jsonb,
                updated_at = $2
            WHERE id = $3::uuid AND tenant_key = $4
            """,
            events, now, session_id, tenant_key,
        )

    async def clear_activity_log(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET activity_log = '[]'::jsonb, updated_at = $1
            WHERE id = $2::uuid AND tenant_key = $3
            """,
            now, session_id, tenant_key,
        )

    async def update_patch(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        user_context: str | None = None,
        attachment_ids: list[str] | None = None,
        control_ids: list[str] | None = None,
        proposed_tasks: list | None = None,
        now: str,
    ) -> dict | None:
        sets: list[str] = ["updated_at = $1"]
        args: list[object] = [now]
        idx = 2

        if user_context is not None:
            sets.append(f"user_context = ${idx}")
            args.append(user_context)
            idx += 1
        if attachment_ids is not None:
            sets.append(f"attachment_ids = ${idx}::jsonb")
            args.append(attachment_ids)
            idx += 1
        if control_ids is not None:
            sets.append(f"control_ids = ${idx}::jsonb")
            args.append(control_ids)
            idx += 1
        if proposed_tasks is not None:
            sets.append(f"proposed_tasks = ${idx}::jsonb")
            args.append(proposed_tasks)
            idx += 1

        row = await conn.fetchrow(
            f"""
            UPDATE {_SESSIONS}
            SET {', '.join(sets)}
            WHERE id = ${idx}::uuid AND tenant_key = ${idx + 1}
            RETURNING {_SESSION_COLS}
            """,
            *args, session_id, tenant_key,
        )
        return _row_to_dict(row) if row else None
