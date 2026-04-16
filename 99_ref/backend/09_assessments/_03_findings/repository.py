from __future__ import annotations

from datetime import datetime

import asyncpg
from importlib import import_module

SCHEMA = '"09_assessments"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods
_models_module = import_module("backend.09_assessments.models")
FindingRecord = _models_module.FindingRecord


@instrument_class_methods(
    namespace="assessments.findings.repository",
    logger_name="backend.assessments.findings.repository.instrumentation",
)
class FindingRepository:
    async def list_findings(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        severity_code: str | None = None,
        status_code: str | None = None,
        finding_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[FindingRecord], int]:
        conditions = ["v.assessment_id = $1::uuid", "v.is_active = TRUE"]
        args: list[object] = [assessment_id]
        idx = 2

        if severity_code is not None:
            conditions.append(f"v.severity_code = ${idx}")
            args.append(severity_code)
            idx += 1
        if status_code is not None:
            conditions.append(f"v.finding_status_code = ${idx}")
            args.append(status_code)
            idx += 1
        if finding_type is not None:
            conditions.append(f"v.finding_type = ${idx}")
            args.append(finding_type)
            idx += 1

        where_clause = " AND ".join(conditions)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."41_vw_finding_detail" v WHERE {where_clause}',
            *args,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT
                v.id::text, v.assessment_id::text,
                v.control_id::text, v.risk_id::text,
                v.severity_code, v.finding_type, v.finding_status_code,
                v.assigned_to::text, v.remediation_due_date::text,
                v.severity_name, v.finding_status_name,
                v.title, v.description, v.recommendation,
                v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text
            FROM {SCHEMA}."41_vw_finding_detail" v
            WHERE {where_clause}
            ORDER BY v.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        return [_row_to_finding(r) for r in rows], total

    async def get_finding_by_id(
        self, connection: asyncpg.Connection, finding_id: str
    ) -> FindingRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                v.id::text, v.assessment_id::text,
                v.control_id::text, v.risk_id::text,
                v.severity_code, v.finding_type, v.finding_status_code,
                v.assigned_to::text, v.remediation_due_date::text,
                v.severity_name, v.finding_status_name,
                v.title, v.description, v.recommendation,
                v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text
            FROM {SCHEMA}."41_vw_finding_detail" v
            WHERE v.id = $1::uuid AND v.is_active = TRUE
            """,
            finding_id,
        )
        return _row_to_finding(row) if row else None

    async def create_finding(
        self,
        connection: asyncpg.Connection,
        *,
        finding_id: str,
        assessment_id: str,
        control_id: str | None,
        risk_id: str | None,
        severity_code: str,
        finding_type: str,
        assigned_to: str | None,
        remediation_due_date: datetime | None,
        created_by: str,
        now: datetime,
    ) -> FindingRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."11_fct_findings" (
                id, assessment_id, control_id, risk_id,
                severity_code, finding_type, finding_status_code,
                assigned_to, remediation_due_date,
                is_active, is_deleted,
                created_at, updated_at, created_by, updated_by
            )
            VALUES (
                $1::uuid, $2::uuid,
                $3::uuid, $4::uuid,
                $5, $6, 'open',
                $7::uuid, $8,
                TRUE, FALSE,
                $9, $10, $11::uuid, $12::uuid
            )
            RETURNING
                id::text, assessment_id::text,
                control_id::text, risk_id::text,
                severity_code, finding_type, finding_status_code,
                assigned_to::text, remediation_due_date::text,
                is_active,
                created_at::text, updated_at::text, created_by::text
            """,
            finding_id,
            assessment_id,
            control_id,
            risk_id,
            severity_code,
            finding_type,
            assigned_to,
            remediation_due_date,
            now,
            now,
            created_by,
            created_by,
        )
        return FindingRecord(
            id=row["id"],
            assessment_id=row["assessment_id"],
            control_id=row["control_id"],
            risk_id=row["risk_id"],
            severity_code=row["severity_code"],
            finding_type=row["finding_type"],
            finding_status_code=row["finding_status_code"],
            assigned_to=row["assigned_to"],
            remediation_due_date=row["remediation_due_date"],
            severity_name=None,
            finding_status_name=None,
            title=None,
            description=None,
            recommendation=None,
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
        )

    async def update_finding(
        self,
        connection: asyncpg.Connection,
        *,
        finding_id: str,
        finding_status_code: str | None = None,
        severity_code: str | None = None,
        assigned_to: str | None = None,
        remediation_due_date: datetime | None = None,
        updated_by: str,
        now: datetime,
    ) -> None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2::uuid"]
        values: list[object] = [now, updated_by]
        idx = 3

        if finding_status_code is not None:
            fields.append(f"finding_status_code = ${idx}")
            values.append(finding_status_code)
            idx += 1
        if severity_code is not None:
            fields.append(f"severity_code = ${idx}")
            values.append(severity_code)
            idx += 1
        if assigned_to is not None:
            fields.append(f"assigned_to = ${idx}::uuid")
            values.append(assigned_to)
            idx += 1
        if remediation_due_date is not None:
            fields.append(f"remediation_due_date = ${idx}")
            values.append(remediation_due_date)
            idx += 1

        values.append(finding_id)
        set_clause = ", ".join(fields)

        await connection.execute(
            f"""
            UPDATE {SCHEMA}."11_fct_findings"
            SET {set_clause}
            WHERE id = ${idx}::uuid AND is_deleted = FALSE
            """,
            *values,
        )

    async def upsert_finding_property(
        self,
        connection: asyncpg.Connection,
        *,
        finding_id: str,
        property_key: str,
        property_value: str,
        actor_id: str,
        now: datetime,
    ) -> None:
        import uuid as _uuid
        prop_id = str(_uuid.uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."22_dtl_finding_properties" (
                id, finding_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8::uuid)
            ON CONFLICT (finding_id, property_key)
            DO UPDATE SET
                property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            prop_id,
            finding_id,
            property_key,
            property_value,
            now,
            now,
            actor_id,
            actor_id,
        )

    async def soft_delete_finding(
        self,
        connection: asyncpg.Connection,
        *,
        finding_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."11_fct_findings"
            SET is_active = FALSE, is_deleted = TRUE,
                updated_at = $1, updated_by = $2::uuid,
                deleted_at = $3, deleted_by = $4::uuid
            WHERE id = $5::uuid AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            finding_id,
        )
        return result != "UPDATE 0"

    async def check_assessment_locked(
        self, connection: asyncpg.Connection, assessment_id: str
    ) -> bool:
        row = await connection.fetchrow(
            f"""
            SELECT is_locked FROM {SCHEMA}."10_fct_assessments"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            assessment_id,
        )
        return bool(row["is_locked"]) if row else False


def _row_to_finding(r) -> FindingRecord:
    return FindingRecord(
        id=r["id"],
        assessment_id=r["assessment_id"],
        control_id=r["control_id"],
        risk_id=r["risk_id"],
        severity_code=r["severity_code"],
        finding_type=r["finding_type"],
        finding_status_code=r["finding_status_code"],
        assigned_to=r["assigned_to"],
        remediation_due_date=r["remediation_due_date"],
        severity_name=r.get("severity_name"),
        finding_status_name=r.get("finding_status_name"),
        title=r.get("title"),
        description=r.get("description"),
        recommendation=r.get("recommendation"),
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )
