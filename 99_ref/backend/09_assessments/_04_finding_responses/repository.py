from __future__ import annotations

from datetime import datetime

import asyncpg
from importlib import import_module

SCHEMA = '"09_assessments"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods
_models_module = import_module("backend.09_assessments.models")
FindingResponseRecord = _models_module.FindingResponseRecord


@instrument_class_methods(
    namespace="assessments.finding_responses.repository",
    logger_name="backend.assessments.finding_responses.repository.instrumentation",
)
class FindingResponseRepository:
    async def list_responses(
        self, connection: asyncpg.Connection, finding_id: str
    ) -> list[FindingResponseRecord]:
        rows = await connection.fetch(
            f"""
            SELECT
                r.id::text, r.finding_id::text, r.responder_id::text,
                r.responded_at::text, r.created_at::text,
                p.property_value AS response_text
            FROM {SCHEMA}."20_trx_finding_responses" r
            LEFT JOIN {SCHEMA}."23_dtl_finding_response_properties" p
                ON p.finding_response_id = r.id AND p.property_key = 'response_text'
            WHERE r.finding_id = $1::uuid
            ORDER BY r.responded_at ASC
            """,
            finding_id,
        )
        return [
            FindingResponseRecord(
                id=row["id"],
                finding_id=row["finding_id"],
                responder_id=row["responder_id"],
                response_text=row["response_text"],
                responded_at=row["responded_at"],
                created_at=row["created_at"],
            )
            for row in rows
        ]

    async def create_response(
        self,
        connection: asyncpg.Connection,
        *,
        response_id: str,
        finding_id: str,
        responder_id: str,
        response_text: str,
        now: datetime,
    ) -> FindingResponseRecord:
        import uuid as _uuid

        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."20_trx_finding_responses" (
                id, finding_id, responder_id, responded_at, created_at
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5)
            RETURNING id::text, finding_id::text, responder_id::text,
                      responded_at::text, created_at::text
            """,
            response_id,
            finding_id,
            responder_id,
            now,
            now,
        )

        prop_id = str(_uuid.uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."23_dtl_finding_response_properties" (
                id, finding_response_id, property_key, property_value,
                created_at
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5)
            """,
            prop_id,
            response_id,
            "response_text",
            response_text,
            now,
        )

        return FindingResponseRecord(
            id=row["id"],
            finding_id=row["finding_id"],
            responder_id=row["responder_id"],
            response_text=response_text,
            responded_at=row["responded_at"],
            created_at=row["created_at"],
        )
