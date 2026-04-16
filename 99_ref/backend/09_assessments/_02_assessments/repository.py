from __future__ import annotations

from datetime import datetime

import asyncpg
from importlib import import_module

SCHEMA = '"09_assessments"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods
_models_module = import_module("backend.09_assessments.models")
AssessmentRecord = _models_module.AssessmentRecord


@instrument_class_methods(
    namespace="assessments.assessments.repository",
    logger_name="backend.assessments.assessments.repository.instrumentation",
)
class AssessmentRepository:
    async def list_assessments(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        type_code: str | None = None,
        status_code: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AssessmentRecord], int]:
        conditions = ["v.is_active = TRUE", "v.tenant_key = $1"]
        args: list[object] = [tenant_key]
        idx = 2

        if org_id is not None:
            conditions.append(f"v.org_id = ${idx}::uuid")
            args.append(org_id)
            idx += 1
        if workspace_id is not None:
            conditions.append(f"v.workspace_id = ${idx}::uuid")
            args.append(workspace_id)
            idx += 1
        if type_code is not None:
            conditions.append(f"v.assessment_type_code = ${idx}")
            args.append(type_code)
            idx += 1
        if status_code is not None:
            conditions.append(f"v.assessment_status_code = ${idx}")
            args.append(status_code)
            idx += 1
        if search is not None:
            conditions.append(f"(v.name ILIKE ${idx} OR v.assessment_code ILIKE ${idx})")
            args.append(f"%{search}%")
            idx += 1

        where_clause = " AND ".join(conditions)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."40_vw_assessment_detail" v WHERE {where_clause}',
            *args,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT
                v.id::text, v.tenant_key, v.assessment_code,
                v.org_id::text, v.workspace_id::text, v.framework_id::text,
                v.assessment_type_code, v.assessment_status_code,
                v.lead_assessor_id::text,
                v.scheduled_start::text, v.scheduled_end::text,
                v.actual_start::text, v.actual_end::text,
                v.is_locked, v.assessment_type_name, v.assessment_status_name,
                v.name, v.description, v.scope_notes,
                v.finding_count, v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text
            FROM {SCHEMA}."40_vw_assessment_detail" v
            WHERE {where_clause}
            ORDER BY v.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        return [_row_to_assessment(r) for r in rows], total

    async def get_assessment_by_id(
        self, connection: asyncpg.Connection, assessment_id: str
    ) -> AssessmentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                v.id::text, v.tenant_key, v.assessment_code,
                v.org_id::text, v.workspace_id::text, v.framework_id::text,
                v.assessment_type_code, v.assessment_status_code,
                v.lead_assessor_id::text,
                v.scheduled_start::text, v.scheduled_end::text,
                v.actual_start::text, v.actual_end::text,
                v.is_locked, v.assessment_type_name, v.assessment_status_name,
                v.name, v.description, v.scope_notes,
                v.finding_count, v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text
            FROM {SCHEMA}."40_vw_assessment_detail" v
            WHERE v.id = $1::uuid AND v.is_active = TRUE
            """,
            assessment_id,
        )
        return _row_to_assessment(row) if row else None

    async def get_assessment_by_code(
        self, connection: asyncpg.Connection, tenant_key: str, code: str
    ) -> AssessmentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                v.id::text, v.tenant_key, v.assessment_code,
                v.org_id::text, v.workspace_id::text, v.framework_id::text,
                v.assessment_type_code, v.assessment_status_code,
                v.lead_assessor_id::text,
                v.scheduled_start::text, v.scheduled_end::text,
                v.actual_start::text, v.actual_end::text,
                v.is_locked, v.assessment_type_name, v.assessment_status_name,
                v.name, v.description, v.scope_notes,
                v.finding_count, v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text
            FROM {SCHEMA}."40_vw_assessment_detail" v
            WHERE v.tenant_key = $1 AND v.assessment_code = $2 AND v.is_active = TRUE
            """,
            tenant_key,
            code,
        )
        return _row_to_assessment(row) if row else None

    async def create_assessment(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        tenant_key: str,
        assessment_code: str,
        org_id: str,
        workspace_id: str | None,
        framework_id: str | None,
        assessment_type_code: str,
        lead_assessor_id: str | None,
        scheduled_start: datetime | None,
        scheduled_end: datetime | None,
        created_by: str,
        now: datetime,
    ) -> AssessmentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."10_fct_assessments" (
                id, tenant_key, assessment_code, org_id, workspace_id, framework_id,
                assessment_type_code, assessment_status_code,
                lead_assessor_id, scheduled_start, scheduled_end,
                actual_start, actual_end, is_locked,
                is_active, is_deleted,
                created_at, updated_at, created_by, updated_by
            )
            VALUES (
                $1::uuid, $2, $3, $4::uuid,
                $5::uuid, $6::uuid,
                $7, 'planned',
                $8::uuid, $9, $10,
                NULL, NULL, FALSE,
                TRUE, FALSE,
                $11, $12, $13::uuid, $14::uuid
            )
            RETURNING
                id::text, tenant_key, assessment_code,
                org_id::text, workspace_id::text, framework_id::text,
                assessment_type_code, assessment_status_code,
                lead_assessor_id::text,
                scheduled_start::text, scheduled_end::text,
                actual_start::text, actual_end::text,
                is_locked, is_active,
                created_at::text, updated_at::text, created_by::text
            """,
            assessment_id,
            tenant_key,
            assessment_code,
            org_id,
            workspace_id,
            framework_id,
            assessment_type_code,
            lead_assessor_id,
            scheduled_start,
            scheduled_end,
            now,
            now,
            created_by,
            created_by,
        )
        # Return via view for enriched data — re-fetch by id
        return AssessmentRecord(
            id=row["id"],
            tenant_key=row["tenant_key"],
            assessment_code=row["assessment_code"],
            org_id=row["org_id"],
            workspace_id=row["workspace_id"],
            framework_id=row["framework_id"],
            assessment_type_code=row["assessment_type_code"],
            assessment_status_code=row["assessment_status_code"],
            lead_assessor_id=row["lead_assessor_id"],
            scheduled_start=row["scheduled_start"],
            scheduled_end=row["scheduled_end"],
            actual_start=row["actual_start"],
            actual_end=row["actual_end"],
            is_locked=row["is_locked"],
            assessment_type_name=None,
            assessment_status_name=None,
            name=None,
            description=None,
            scope_notes=None,
            finding_count=0,
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            created_by=row["created_by"],
        )

    async def update_assessment(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        assessment_type_code: str | None = None,
        status_code: str | None = None,
        lead_assessor_id: str | None = None,
        scheduled_start: datetime | None = None,
        scheduled_end: datetime | None = None,
        actual_start: datetime | None = None,
        actual_end: datetime | None = None,
        is_locked: bool | None = None,
        updated_by: str,
        now: datetime,
    ) -> None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2::uuid"]
        values: list[object] = [now, updated_by]
        idx = 3

        if assessment_type_code is not None:
            fields.append(f"assessment_type_code = ${idx}")
            values.append(assessment_type_code)
            idx += 1
        if status_code is not None:
            fields.append(f"assessment_status_code = ${idx}")
            values.append(status_code)
            idx += 1
        if lead_assessor_id is not None:
            fields.append(f"lead_assessor_id = ${idx}::uuid")
            values.append(lead_assessor_id)
            idx += 1
        if scheduled_start is not None:
            fields.append(f"scheduled_start = ${idx}")
            values.append(scheduled_start)
            idx += 1
        if scheduled_end is not None:
            fields.append(f"scheduled_end = ${idx}")
            values.append(scheduled_end)
            idx += 1
        if actual_start is not None:
            fields.append(f"actual_start = ${idx}")
            values.append(actual_start)
            idx += 1
        if actual_end is not None:
            fields.append(f"actual_end = ${idx}")
            values.append(actual_end)
            idx += 1
        if is_locked is not None:
            fields.append(f"is_locked = ${idx}")
            values.append(is_locked)
            idx += 1

        values.append(assessment_id)
        set_clause = ", ".join(fields)

        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_assessments"
            SET {set_clause}
            WHERE id = ${idx}::uuid AND is_deleted = FALSE
            """,
            *values,
        )

    async def upsert_assessment_property(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        property_key: str,
        property_value: str,
        actor_id: str,
        now: datetime,
    ) -> None:
        import uuid as _uuid
        prop_id = str(_uuid.uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."21_dtl_assessment_properties" (
                id, assessment_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8::uuid)
            ON CONFLICT (assessment_id, property_key)
            DO UPDATE SET
                property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            prop_id,
            assessment_id,
            property_key,
            property_value,
            now,
            now,
            actor_id,
            actor_id,
        )

    async def delete_assessment_property(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        property_key: str,
    ) -> None:
        await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."21_dtl_assessment_properties"
            WHERE assessment_id = $1::uuid AND property_key = $2
            """,
            assessment_id,
            property_key,
        )

    async def soft_delete_assessment(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_assessments"
            SET is_active = FALSE, is_deleted = TRUE,
                updated_at = $1, updated_by = $2::uuid,
                deleted_at = $3, deleted_by = $4::uuid
            WHERE id = $5::uuid AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            assessment_id,
        )
        return result != "UPDATE 0"

    async def get_assessment_summary(
        self, connection: asyncpg.Connection, assessment_id: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT
                f.severity_code,
                f.finding_status_code,
                COUNT(*)::int AS finding_count
            FROM {SCHEMA}."11_fct_findings" f
            WHERE f.assessment_id = $1::uuid AND f.is_deleted = FALSE
            GROUP BY f.severity_code, f.finding_status_code
            """,
            assessment_id,
        )
        return [dict(r) for r in rows]


def _row_to_assessment(r) -> AssessmentRecord:
    return AssessmentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        assessment_code=r["assessment_code"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        framework_id=r["framework_id"],
        assessment_type_code=r["assessment_type_code"],
        assessment_status_code=r["assessment_status_code"],
        lead_assessor_id=r["lead_assessor_id"],
        scheduled_start=r["scheduled_start"],
        scheduled_end=r["scheduled_end"],
        actual_start=r["actual_start"],
        actual_end=r["actual_end"],
        is_locked=r["is_locked"],
        assessment_type_name=r.get("assessment_type_name"),
        assessment_status_name=r.get("assessment_status_name"),
        name=r.get("name"),
        description=r.get("description"),
        scope_notes=r.get("scope_notes"),
        finding_count=r.get("finding_count", 0) or 0,
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )
