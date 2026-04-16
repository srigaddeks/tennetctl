from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import AssessmentRecord

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="risk.assessments.repository", logger_name="backend.risk.assessments.repository.instrumentation")
class AssessmentRepository:
    async def list_assessments(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> list[AssessmentRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, risk_id::text, assessment_type,
                   likelihood_score, impact_score, risk_score,
                   assessed_by::text, assessment_notes, assessed_at::text
            FROM {SCHEMA}."32_trx_risk_assessments"
            WHERE risk_id = $1::uuid
            ORDER BY assessed_at DESC
            """,
            risk_id,
        )
        return [_row_to_assessment(r) for r in rows]

    async def create_assessment(
        self,
        connection: asyncpg.Connection,
        *,
        assessment_id: str,
        risk_id: str,
        assessment_type: str,
        likelihood_score: int,
        impact_score: int,
        assessed_by: str,
        assessment_notes: str | None,
        now: datetime,
    ) -> AssessmentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."32_trx_risk_assessments" (
                id, risk_id, assessment_type,
                likelihood_score, impact_score,
                assessed_by, assessment_notes, assessed_at
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6::uuid, $7, $8)
            RETURNING id::text, risk_id::text, assessment_type,
                      likelihood_score, impact_score, risk_score,
                      assessed_by::text, assessment_notes, assessed_at::text
            """,
            assessment_id,
            risk_id,
            assessment_type,
            likelihood_score,
            impact_score,
            assessed_by,
            assessment_notes,
            now,
        )
        return _row_to_assessment(row)


def _row_to_assessment(r) -> AssessmentRecord:
    return AssessmentRecord(
        id=r["id"],
        risk_id=r["risk_id"],
        assessment_type=r["assessment_type"],
        likelihood_score=r["likelihood_score"],
        impact_score=r["impact_score"],
        risk_score=r["risk_score"],
        assessed_by=r["assessed_by"],
        assessment_notes=r["assessment_notes"],
        assessed_at=r["assessed_at"],
    )
