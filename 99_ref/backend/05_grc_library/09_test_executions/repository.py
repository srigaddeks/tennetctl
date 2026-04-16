from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TestExecutionRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


def _row_to_execution(r) -> TestExecutionRecord:
    return TestExecutionRecord(
        id=r["id"],
        control_test_id=r["control_test_id"],
        control_id=r["control_id"],
        tenant_key=r["tenant_key"],
        result_status=r["result_status"],
        execution_type=r["execution_type"],
        executed_by=r["executed_by"],
        executed_at=r["executed_at"],
        notes=r["notes"],
        evidence_summary=r["evidence_summary"],
        score=r["score"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        test_code=r.get("test_code"),
        test_name=r.get("test_name"),
    )


@instrument_class_methods(namespace="grc.test_executions.repository", logger_name="backend.grc.test_executions.repository.instrumentation")
class TestExecutionRepository:

    async def list_executions(
        self, connection: asyncpg.Connection, *,
        control_test_id: str | None = None,
        control_id: str | None = None,
        result_status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[TestExecutionRecord], int]:
        conditions = ["e.is_deleted = FALSE"]
        args: list[object] = []
        idx = 1
        if control_test_id:
            conditions.append(f"e.control_test_id = ${idx}::uuid"); args.append(control_test_id); idx += 1
        if control_id:
            conditions.append(f"e.control_id = ${idx}::uuid"); args.append(control_id); idx += 1
        if result_status:
            conditions.append(f"e.result_status = ${idx}"); args.append(result_status); idx += 1
        where = " AND ".join(conditions)

        count = await connection.fetchval(
            f'SELECT COUNT(*) FROM {SCHEMA}."15_fct_test_executions" e WHERE {where}', *args
        )
        rows = await connection.fetch(
            f"""
            SELECT e.id::text, e.control_test_id::text, e.control_id::text, e.tenant_key,
                   e.result_status, e.execution_type, e.executed_by::text,
                   e.executed_at::text, e.notes, e.evidence_summary, e.score,
                   e.is_active, e.created_at::text, e.updated_at::text,
                   t.test_code, tp.property_value AS test_name
            FROM {SCHEMA}."15_fct_test_executions" e
            JOIN {SCHEMA}."14_fct_control_tests" t ON t.id = e.control_test_id
            LEFT JOIN {SCHEMA}."24_dtl_test_properties" tp
                ON tp.test_id = t.id AND tp.property_key = 'name'
            WHERE {where}
            ORDER BY e.executed_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        return [_row_to_execution(r) for r in rows], count

    async def get_execution(
        self, connection: asyncpg.Connection, execution_id: str
    ) -> TestExecutionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT e.id::text, e.control_test_id::text, e.control_id::text, e.tenant_key,
                   e.result_status, e.execution_type, e.executed_by::text,
                   e.executed_at::text, e.notes, e.evidence_summary, e.score,
                   e.is_active, e.created_at::text, e.updated_at::text,
                   t.test_code, tp.property_value AS test_name
            FROM {SCHEMA}."15_fct_test_executions" e
            JOIN {SCHEMA}."14_fct_control_tests" t ON t.id = e.control_test_id
            LEFT JOIN {SCHEMA}."24_dtl_test_properties" tp
                ON tp.test_id = t.id AND tp.property_key = 'name'
            WHERE e.id = $1::uuid AND e.is_deleted = FALSE
            """,
            execution_id,
        )
        return _row_to_execution(row) if row else None

    async def create_execution(
        self, connection: asyncpg.Connection, *,
        execution_id: str,
        control_test_id: str,
        control_id: str | None,
        tenant_key: str,
        result_status: str,
        execution_type: str,
        executed_by: str,
        notes: str | None,
        evidence_summary: str | None,
        score: int | None,
        now: object,
    ) -> TestExecutionRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."15_fct_test_executions"
                (id, control_test_id, control_id, tenant_key, result_status, execution_type,
                 executed_by, executed_at, notes, evidence_summary, score,
                 is_active, is_deleted, created_at, updated_at, created_by, updated_by)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6,
                    $7::uuid, $8, $9, $10, $11,
                    TRUE, FALSE, $12, $13, $14::uuid, $15::uuid)
            RETURNING id::text, control_test_id::text, control_id::text, tenant_key,
                      result_status, execution_type, executed_by::text,
                      executed_at::text, notes, evidence_summary, score,
                      is_active, created_at::text, updated_at::text
            """,
            execution_id,
            control_test_id,
            control_id,
            tenant_key,
            result_status,
            execution_type,
            executed_by,
            now,
            notes,
            evidence_summary,
            score,
            now,
            now,
            executed_by,
            executed_by,
        )
        return _row_to_execution(row)

    async def update_execution(
        self, connection: asyncpg.Connection, execution_id: str, *,
        result_status: str | None = None,
        notes: str | None = None,
        evidence_summary: str | None = None,
        score: int | None = None,
        updated_by: str,
        now: object,
    ) -> TestExecutionRecord | None:
        fields = ["updated_at = $1", "updated_by = $2::uuid"]
        values: list[object] = [now, updated_by]
        idx = 3
        if result_status is not None:
            fields.append(f"result_status = ${idx}"); values.append(result_status); idx += 1
        if notes is not None:
            fields.append(f"notes = ${idx}"); values.append(notes); idx += 1
        if evidence_summary is not None:
            fields.append(f"evidence_summary = ${idx}"); values.append(evidence_summary); idx += 1
        if score is not None:
            fields.append(f"score = ${idx}"); values.append(score); idx += 1
        values.append(execution_id)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."15_fct_test_executions"
            SET {", ".join(fields)}
            WHERE id = ${idx}::uuid AND is_deleted = FALSE
            RETURNING id::text, control_test_id::text, control_id::text, tenant_key,
                      result_status, execution_type, executed_by::text,
                      executed_at::text, notes, evidence_summary, score,
                      is_active, created_at::text, updated_at::text
            """,
            *values,
        )
        return _row_to_execution(row) if row else None
