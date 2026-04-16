from __future__ import annotations

import asyncpg
from importlib import import_module

SCHEMA = '"09_assessments"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods
_models_module = import_module("backend.09_assessments.models")
AssessmentTypeRecord = _models_module.AssessmentTypeRecord
FindingSeverityRecord = _models_module.FindingSeverityRecord
FindingStatusRecord = _models_module.FindingStatusRecord


@instrument_class_methods(
    namespace="assessments.types.repository",
    logger_name="backend.assessments.types.repository.instrumentation",
)
class AssessmentTypesRepository:
    async def list_assessment_types(
        self, connection: asyncpg.Connection
    ) -> list[AssessmentTypeRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, code, name, description, sort_order, is_active
            FROM {SCHEMA}."02_dim_assessment_types"
            WHERE is_active = TRUE
            ORDER BY sort_order
            """
        )
        return [
            AssessmentTypeRecord(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]

    async def list_assessment_statuses(
        self, connection: asyncpg.Connection
    ) -> list[AssessmentTypeRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, code, name, description, sort_order, is_active
            FROM {SCHEMA}."03_dim_assessment_statuses"
            WHERE is_active = TRUE
            ORDER BY sort_order
            """
        )
        return [
            AssessmentTypeRecord(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]

    async def list_finding_severities(
        self, connection: asyncpg.Connection
    ) -> list[FindingSeverityRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, code, name, description, sort_order, is_active
            FROM {SCHEMA}."04_dim_finding_severities"
            WHERE is_active = TRUE
            ORDER BY sort_order
            """
        )
        return [
            FindingSeverityRecord(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]

    async def list_finding_statuses(
        self, connection: asyncpg.Connection
    ) -> list[FindingStatusRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, code, name, description, sort_order, is_active
            FROM {SCHEMA}."05_dim_finding_statuses"
            WHERE is_active = TRUE
            ORDER BY sort_order
            """
        )
        return [
            FindingStatusRecord(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]
