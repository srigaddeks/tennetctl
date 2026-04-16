"""
Repository for framework builder sessions.

Reads/writes 20_ai.60_fct_builder_sessions.
"""

from __future__ import annotations

import json
from importlib import import_module

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.framework_builder.repository")

_SESSIONS = '"20_ai"."60_fct_builder_sessions"'

_SESSION_COLS = """
    id::text, tenant_key, user_id::text, session_type, status,
    scope_org_id::text, scope_workspace_id::text,
    framework_id::text, framework_name, framework_type_code, framework_category_code,
    user_context, attachment_ids, node_overrides,
    proposed_hierarchy, proposed_controls, proposed_risks, proposed_risk_mappings,
    enhance_diff, accepted_changes,
    job_id::text, result_framework_id::text, error_message,
    activity_log,
    created_at::text, updated_at::text, created_by::text
"""


def _row_to_dict(row) -> dict:
    d = dict(row)
    for key in (
        "attachment_ids",
        "node_overrides",
        "proposed_hierarchy",
        "proposed_controls",
        "proposed_risks",
        "proposed_risk_mappings",
        "enhance_diff",
        "accepted_changes",
        "activity_log",
    ):
        val = d.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            try:
                d[key] = json.loads(val)
            except Exception:
                pass
    return d


class BuilderSessionRepository:
    async def create_session(
        self,
        conn: asyncpg.Connection,
        *,
        session_id: str,
        tenant_key: str,
        user_id: str,
        session_type: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
        framework_id: str | None,
        framework_name: str | None,
        framework_type_code: str | None,
        framework_category_code: str | None,
        user_context: str | None,
        attachment_ids: list,
        job_id: str | None = None,
        now: str,
    ) -> dict:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_SESSIONS} (
                id, tenant_key, user_id, session_type, status,
                scope_org_id, scope_workspace_id,
                framework_id, framework_name, framework_type_code, framework_category_code,
                user_context, attachment_ids, job_id,
                created_at, updated_at, created_by
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4, 'idle',
                $5::uuid, $6::uuid,
                $7::uuid, $8, $9, $10,
                $11, $12::jsonb, $13::uuid,
                $14, $15, $3::uuid
            )
            RETURNING {_SESSION_COLS}
            """,
            session_id,
            tenant_key,
            user_id,
            session_type,
            scope_org_id,
            scope_workspace_id,
            framework_id,
            framework_name,
            framework_type_code,
            framework_category_code,
            user_context,
            json.dumps(attachment_ids),
            job_id,
            now,
            now,
        )
        return _row_to_dict(row)

    async def get_by_id(
        self, conn: asyncpg.Connection, session_id: str, tenant_key: str
    ) -> dict | None:
        row = await conn.fetchrow(
            f"SELECT {_SESSION_COLS} FROM {_SESSIONS} WHERE id = $1 AND tenant_key = $2",
            session_id,
            tenant_key,
        )
        return _row_to_dict(row) if row else None

    async def list_sessions(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        where = ["tenant_key = $1", "user_id = $2::uuid"]
        args: list[object] = [tenant_key, user_id]
        idx = 3
        if scope_org_id is not None:
            where.append(f"scope_org_id = ${idx}::uuid")
            args.append(scope_org_id)
            idx += 1
        if scope_workspace_id is not None:
            where.append(f"scope_workspace_id = ${idx}::uuid")
            args.append(scope_workspace_id)
            idx += 1
        where_sql = " AND ".join(where)

        rows = await conn.fetch(
            f"""
            SELECT {_SESSION_COLS}
            FROM {_SESSIONS}
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *args,
            limit,
            offset,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM {_SESSIONS} WHERE {where_sql}",
            *args,
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
            f"UPDATE {_SESSIONS} SET status = $3, updated_at = $4 WHERE id = $1 AND tenant_key = $2",
            session_id,
            tenant_key,
            status,
            now,
        )

    async def update_patch(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        user_id: str,
        user_context: str | None,
        attachment_ids: list | None,
        node_overrides: dict | None,
        accepted_changes: list | None,
        proposed_hierarchy: dict | None = None,
        proposed_controls: list | None = None,
        proposed_risks: list | None = None,
        proposed_risk_mappings: list | None = None,
        now: str,
    ) -> dict | None:
        sets = ["updated_at = $4"]
        params: list = [session_id, tenant_key, user_id, now]
        i = 5
        if user_context is not None:
            sets.append(f"user_context = ${i}")
            params.append(user_context)
            i += 1
        if attachment_ids is not None:
            sets.append(f"attachment_ids = ${i}::jsonb")
            params.append(json.dumps(attachment_ids))
            i += 1
        if node_overrides is not None:
            sets.append(f"node_overrides = ${i}::jsonb")
            params.append(json.dumps(node_overrides))
            i += 1
        if accepted_changes is not None:
            sets.append(f"accepted_changes = ${i}::jsonb")
            params.append(json.dumps(accepted_changes))
            i += 1
        if proposed_hierarchy is not None:
            sets.append(f"proposed_hierarchy = ${i}::jsonb")
            params.append(json.dumps(proposed_hierarchy))
            i += 1
        if proposed_controls is not None:
            sets.append(f"proposed_controls = ${i}::jsonb")
            params.append(json.dumps(proposed_controls))
            i += 1
        if proposed_risks is not None:
            sets.append(f"proposed_risks = ${i}::jsonb")
            params.append(json.dumps(proposed_risks))
            i += 1
        if proposed_risk_mappings is not None:
            sets.append(f"proposed_risk_mappings = ${i}::jsonb")
            params.append(json.dumps(proposed_risk_mappings))
            i += 1
        if len(sets) == 1:
            return await self.get_by_id(conn, session_id, tenant_key)
        sql = f"""
            UPDATE {_SESSIONS}
            SET {", ".join(sets)}
            WHERE id = $1 AND tenant_key = $2 AND user_id = $3::uuid
            RETURNING {_SESSION_COLS}
        """
        row = await conn.fetchrow(sql, *params)
        return _row_to_dict(row) if row else None

    async def save_phase1(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        hierarchy: dict,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET proposed_hierarchy = $2::jsonb,
                status = 'phase1_review',
                updated_at = $3
            WHERE id = $1 AND tenant_key = $4
            """,
            session_id,
            json.dumps(hierarchy),
            now,
            tenant_key,
        )

    async def save_phase2(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        controls: list,
        risks: list,
        risk_mappings: list,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET proposed_controls = $2::jsonb,
                proposed_risks = $3::jsonb,
                proposed_risk_mappings = $4::jsonb,
                status = 'phase2_review',
                updated_at = $5
            WHERE id = $1 AND tenant_key = $6
            """,
            session_id,
            json.dumps(controls),
            json.dumps(risks),
            json.dumps(risk_mappings),
            now,
            tenant_key,
        )

    async def save_enhance_diff(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        diff: list,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET enhance_diff = $2::jsonb,
                status = 'phase2_review',
                updated_at = $3
            WHERE id = $1 AND tenant_key = $4
            """,
            session_id,
            json.dumps(diff),
            now,
            tenant_key,
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
            SET job_id = $2::uuid,
                status = $3,
                error_message = NULL,
                updated_at = $4
            WHERE id = $1 AND tenant_key = $5
            """,
            session_id,
            job_id,
            status,
            now,
            tenant_key,
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
        """Append SSE events to the session's activity_log JSONB array.

        Uses ``(SELECT jsonb_agg(elem) FROM jsonb_array_elements(...))`` to
        build a proper JSONB array that concatenates correctly with ``||``,
        avoiding asyncpg's string-wrapping of text parameters.
        """
        if not events:
            return
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET activity_log = activity_log || (
                SELECT COALESCE(jsonb_agg(elem), '[]'::jsonb)
                FROM jsonb_array_elements($2::jsonb) AS elem
            ),
                updated_at = $3
            WHERE id = $1 AND tenant_key = $4
            """,
            session_id,
            json.dumps(events),
            now,
            tenant_key,
        )

    async def clear_activity_log(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        now: str,
    ) -> None:
        """Reset the activity_log when a new streaming phase begins."""
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET activity_log = '[]'::jsonb,
                updated_at = $2
            WHERE id = $1 AND tenant_key = $3
            """,
            session_id,
            now,
            tenant_key,
        )

    async def set_result(
        self,
        conn: asyncpg.Connection,
        session_id: str,
        *,
        tenant_key: str,
        result_framework_id: str | None,
        status: str,
        error_message: str | None,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET result_framework_id = $2::uuid,
                status = $3,
                error_message = $4,
                updated_at = $5
            WHERE id = $1 AND tenant_key = $6
            """,
            session_id,
            result_framework_id,
            status,
            error_message,
            now,
            tenant_key,
        )
