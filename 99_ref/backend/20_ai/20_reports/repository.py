from __future__ import annotations

import json

import asyncpg

from .models import ReportRecord, ReportSummary

_SCHEMA = '"20_ai"'
_REPORTS = f'{_SCHEMA}."50_fct_reports"'


def _row_to_record(row) -> ReportRecord:
    params = row["parameters_json"]
    if isinstance(params, str):
        params = json.loads(params)
    return ReportRecord(
        id=row["id"],
        tenant_key=row["tenant_key"],
        org_id=row["org_id"],
        workspace_id=row["workspace_id"],
        report_type=row["report_type"],
        status_code=row["status_code"],
        title=row["title"],
        parameters_json=params,
        content_markdown=row["content_markdown"],
        word_count=row["word_count"],
        token_count=row["token_count"],
        generated_by_user_id=row["generated_by_user_id"],
        agent_run_id=row["agent_run_id"],
        job_id=row["job_id"],
        error_message=row["error_message"],
        is_auto_generated=row["is_auto_generated"],
        trigger_entity_type=row["trigger_entity_type"],
        trigger_entity_id=row["trigger_entity_id"],
        created_at=str(row["created_at"]),
        completed_at=str(row["completed_at"]) if row["completed_at"] else None,
        updated_at=str(row["updated_at"]),
    )


class ReportRepository:
    async def create_report(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        report_type: str,
        title: str | None,
        parameters_json: dict,
        generated_by_user_id: str | None,
        job_id: str | None,
        trigger_entity_type: str | None = None,
        trigger_entity_id: str | None = None,
        is_auto_generated: bool = False,
    ) -> ReportRecord:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_REPORTS}
                (tenant_key, org_id, workspace_id, report_type, status_code, title,
                 parameters_json, generated_by_user_id, job_id,
                 trigger_entity_type, trigger_entity_id, is_auto_generated)
            VALUES ($1, $2::uuid, $3::uuid, $4, 'queued', $5,
                    $6::jsonb, $7::uuid, $8::uuid, $9, $10::uuid, $11)
            RETURNING
                id::text, tenant_key, org_id::text, workspace_id::text,
                report_type, status_code, title, parameters_json,
                content_markdown, word_count, token_count,
                generated_by_user_id::text, agent_run_id::text, job_id::text,
                error_message, is_auto_generated, trigger_entity_type,
                trigger_entity_id::text, created_at, completed_at, updated_at
            """,
            tenant_key,
            org_id,
            workspace_id,
            report_type,
            title,
            json.dumps(parameters_json),
            generated_by_user_id,
            job_id,
            trigger_entity_type,
            trigger_entity_id,
            is_auto_generated,
        )
        return _row_to_record(row)

    async def get_report(
        self,
        conn: asyncpg.Connection,
        report_id: str,
        tenant_key: str,
    ) -> ReportRecord | None:
        row = await conn.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, org_id::text, workspace_id::text,
                report_type, status_code, title, parameters_json,
                content_markdown, word_count, token_count,
                generated_by_user_id::text, agent_run_id::text, job_id::text,
                error_message, is_auto_generated, trigger_entity_type,
                trigger_entity_id::text, created_at, completed_at, updated_at
            FROM {_REPORTS}
            WHERE id = $1::uuid AND tenant_key = $2
            """,
            report_id,
            tenant_key,
        )
        return _row_to_record(row) if row else None

    async def list_reports(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None = None,
        report_type: str | None = None,
        engagement_id: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ReportRecord], int]:
        """Returns (records, total_count) using a window function."""
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2
        if org_id:
            conditions.append(f"org_id = ${idx}::uuid")
            params.append(org_id)
            idx += 1
        if report_type:
            conditions.append(f"report_type = ${idx}")
            params.append(report_type)
            idx += 1
        if engagement_id:
            # Match either via trigger_entity or parameters_json
            conditions.append(
                f"(trigger_entity_id = ${idx}::uuid OR parameters_json @> ${idx + 1}::jsonb)"
            )
            params.append(engagement_id)
            params.append(json.dumps({"engagement_id": engagement_id}))
            idx += 2
        where = " AND ".join(conditions)
        rows = await conn.fetch(
            f"""
            SELECT
                id::text, tenant_key, org_id::text, workspace_id::text,
                report_type, status_code, title, parameters_json,
                content_markdown, word_count, token_count,
                generated_by_user_id::text, agent_run_id::text, job_id::text,
                error_message, is_auto_generated, trigger_entity_type,
                trigger_entity_id::text, created_at, completed_at, updated_at,
                COUNT(*) OVER() AS _total
            FROM {_REPORTS}
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params,
            limit,
            offset,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_record(r) for r in rows], total

    async def update_report_status(
        self,
        conn: asyncpg.Connection,
        report_id: str,
        status_code: str,
        error_message: str | None = None,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_REPORTS}
            SET status_code = $2, error_message = $3, updated_at = NOW()
            WHERE id = $1::uuid
            """,
            report_id,
            status_code,
            error_message,
        )

    async def update_report_content(
        self,
        conn: asyncpg.Connection,
        report_id: str,
        *,
        markdown_content: str,
        word_count: int,
        token_count: int,
    ) -> None:
        await conn.execute(
            f"""
            UPDATE {_REPORTS}
            SET status_code = 'completed',
                content_markdown = $2,
                word_count = $3,
                token_count = $4,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1::uuid
            """,
            report_id,
            markdown_content,
            word_count,
            token_count,
        )

    async def update_report(
        self,
        conn: asyncpg.Connection,
        report_id: str,
        tenant_key: str,
        *,
        title: str | None = None,
        content_markdown: str | None = None,
        word_count: int | None = None,
    ) -> ReportRecord:
        updates = ["updated_at = NOW()"]
        params: list = [report_id, tenant_key]
        idx = 3

        if title is not None:
            updates.append(f"title = ${idx}")
            params.append(title)
            idx += 1
        if content_markdown is not None:
            updates.append(f"content_markdown = ${idx}")
            params.append(content_markdown)
            idx += 1
        if word_count is not None:
            updates.append(f"word_count = ${idx}")
            params.append(word_count)
            idx += 1

        set_clause = ", ".join(updates)
        row = await conn.fetchrow(
            f"""
            UPDATE {_REPORTS}
            SET {set_clause}
            WHERE id = $1::uuid AND tenant_key = $2
            RETURNING *
            """,
            *params,
        )
        return _row_to_record(row)

    async def update_report_submission(
        self,
        conn: asyncpg.Connection,
        report_id: str,
        tenant_key: str,
        engagement_id: str,
    ) -> ReportRecord:
        """Update report status to submitted and attach to engagement."""
        row = await conn.fetchrow(
            f"""
            UPDATE {_REPORTS}
            SET 
                status_code = 'submitted',
                trigger_entity_type = 'engagement',
                trigger_entity_id = $3::uuid,
                updated_at = NOW()
            WHERE id = $1::uuid AND tenant_key = $2
            RETURNING *
            """,
            report_id,
            tenant_key,
            engagement_id,
        )
        if not row:
            raise ValueError(f"Failed to update report {report_id}")
        return _row_to_record(row)

    async def delete_report(
        self,
        conn: asyncpg.Connection,
        report_id: str,
        tenant_key: str,
    ) -> bool:
        result = await conn.execute(
            f"DELETE FROM {_REPORTS} WHERE id = $1::uuid AND tenant_key = $2",
            report_id,
            tenant_key,
        )
        return result != "DELETE 0"

    async def get_report_by_job(
        self,
        conn: asyncpg.Connection,
        job_id: str,
    ) -> ReportRecord | None:
        row = await conn.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, org_id::text, workspace_id::text,
                report_type, status_code, title, parameters_json,
                content_markdown, word_count, token_count,
                generated_by_user_id::text, agent_run_id::text, job_id::text,
                error_message, is_auto_generated, trigger_entity_type,
                trigger_entity_id::text, created_at, completed_at, updated_at
            FROM {_REPORTS}
            WHERE job_id = $1::uuid
            """,
            job_id,
        )
        return _row_to_record(row) if row else None

    async def list_reports_by_framework(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        framework_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReportRecord], int]:
        """List reports associated with a specific framework via parameters_json."""
        rows = await conn.fetch(
            f"""
            SELECT
                id::text, tenant_key, org_id::text, workspace_id::text,
                report_type, status_code, title, parameters_json,
                content_markdown, word_count, token_count,
                generated_by_user_id::text, agent_run_id::text, job_id::text,
                error_message, is_auto_generated, trigger_entity_type,
                trigger_entity_id::text, created_at, completed_at, updated_at,
                COUNT(*) OVER() AS _total
            FROM {_REPORTS}
            WHERE tenant_key = $1
              AND parameters_json @> $2::jsonb
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            tenant_key,
            json.dumps({"framework_id": framework_id}),
            limit,
            offset,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_record(r) for r in rows], total

    async def list_reports_by_engagement(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        engagement_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReportRecord], int]:
        """List reports associated with a specific engagement."""
        return await self.list_reports(
            conn,
            tenant_key=tenant_key,
            engagement_id=engagement_id,
            limit=limit,
            offset=offset,
        )
