from __future__ import annotations

from datetime import datetime

import asyncpg
from importlib import import_module

from .models import ControlMappingRecord

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="risk.control_mappings.repository",
    logger_name="backend.risk.control_mappings.repository.instrumentation",
)
class ControlMappingRepository:
    async def list_control_mappings(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> list[ControlMappingRecord]:
        rows = await connection.fetch(
            f"""
            SELECT m.id::text, m.risk_id::text, m.control_id::text,
                   m.link_type, m.notes, m.created_at::text, m.created_by::text,
                   m.approval_status,
                   m.approved_by::text, m.approved_at::text,
                   m.rejection_reason, m.ai_confidence, m.ai_rationale,
                   c.control_code,
                   cp.property_value AS control_name
            FROM {SCHEMA}."30_lnk_risk_control_mappings" m
            LEFT JOIN "05_grc_library"."13_fct_controls" c
                   ON c.id = m.control_id AND c.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp
                   ON cp.control_id = m.control_id AND cp.property_key = 'name'
            WHERE m.risk_id = $1::uuid
              AND m.approval_status != 'rejected'
            ORDER BY m.approval_status DESC, m.created_at
            """,
            risk_id,
        )
        return [_row_to_mapping(r) for r in rows]

    async def list_risks_for_control(
        self, connection: asyncpg.Connection, control_id: str
    ) -> list[ControlMappingRecord]:
        rows = await connection.fetch(
            f"""
            SELECT m.id::text, m.risk_id::text, m.control_id::text,
                   m.link_type, m.notes, m.created_at::text, m.created_by::text,
                   m.approval_status,
                   m.approved_by::text, m.approved_at::text,
                   m.rejection_reason, m.ai_confidence, m.ai_rationale,
                   c.control_code,
                   cp.property_value AS control_name,
                   r.risk_code,
                   rp.property_value AS risk_title
            FROM {SCHEMA}."30_lnk_risk_control_mappings" m
            JOIN "14_risk_registry"."10_fct_risks" r ON r.id = m.risk_id
            LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" rp
                   ON rp.risk_id = r.id AND rp.property_key = 'title'
            LEFT JOIN "05_grc_library"."13_fct_controls" c
                   ON c.id = m.control_id AND c.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp
                   ON cp.control_id = m.control_id AND cp.property_key = 'name'
            WHERE m.control_id = $1::uuid
              AND m.approval_status != 'rejected'
            ORDER BY m.approval_status DESC, m.created_at
            """,
            control_id,
        )
        return [_row_to_mapping(r) for r in rows]

    async def list_pending_mappings(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        workspace_id: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[ControlMappingRecord], int]:
        """Return pending AI-proposed mappings for an org/workspace with risk and control details."""
        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS total
            FROM {SCHEMA}."30_lnk_risk_control_mappings" m
            JOIN "14_risk_registry"."10_fct_risks" r ON r.id = m.risk_id
            WHERE m.approval_status = 'pending'
              AND r.org_id = $1::uuid
              AND ($2::uuid IS NULL OR r.workspace_id = $2::uuid)
            """,
            org_id,
            workspace_id,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT m.id::text, m.risk_id::text, m.control_id::text,
                   m.link_type, m.notes, m.created_at::text, m.created_by::text,
                   m.approval_status,
                   m.approved_by::text, m.approved_at::text,
                   m.rejection_reason, m.ai_confidence, m.ai_rationale,
                   c.control_code,
                   cp.property_value AS control_name,
                   r.risk_code,
                   rp.property_value AS risk_title
            FROM {SCHEMA}."30_lnk_risk_control_mappings" m
            JOIN "14_risk_registry"."10_fct_risks" r ON r.id = m.risk_id
            LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" rp
                   ON rp.risk_id = r.id AND rp.property_key = 'title'
            LEFT JOIN "05_grc_library"."13_fct_controls" c
                   ON c.id = m.control_id AND c.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp
                   ON cp.control_id = m.control_id AND cp.property_key = 'name'
            WHERE m.approval_status = 'pending'
              AND r.org_id = $1::uuid
              AND ($2::uuid IS NULL OR r.workspace_id = $2::uuid)
            ORDER BY m.created_at DESC
            LIMIT $3
            OFFSET $4
            """,
            org_id,
            workspace_id,
            limit,
            offset,
        )
        return [_row_to_mapping(r) for r in rows], total

    async def create_control_mapping(
        self,
        connection: asyncpg.Connection,
        *,
        mapping_id: str,
        risk_id: str,
        control_id: str,
        link_type: str,
        notes: str | None,
        created_by: str,
        now: datetime,
        approval_status: str = "approved",
        ai_confidence: float | None = None,
        ai_rationale: str | None = None,
    ) -> ControlMappingRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."30_lnk_risk_control_mappings" (
                id, risk_id, control_id, link_type, notes,
                created_at, created_by,
                approval_status, ai_confidence, ai_rationale
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, $7::uuid, $8, $9, $10)
            RETURNING id::text, risk_id::text, control_id::text,
                      link_type, notes, created_at::text, created_by::text,
                      approval_status,
                      approved_by::text, approved_at::text,
                      rejection_reason, ai_confidence, ai_rationale
            """,
            mapping_id,
            risk_id,
            control_id,
            link_type,
            notes,
            now,
            created_by,
            approval_status,
            ai_confidence,
            ai_rationale,
        )
        return _row_to_mapping(row)

    async def approve_mapping(
        self,
        connection: asyncpg.Connection,
        *,
        mapping_id: str,
        approved_by: str,
        now: datetime,
        notes: str | None = None,
    ) -> ControlMappingRecord | None:
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."30_lnk_risk_control_mappings"
            SET approval_status = 'approved',
                approved_by = $2::uuid,
                approved_at = $3,
                notes = COALESCE($4, notes),
                rejection_reason = NULL
            WHERE id = $1::uuid AND approval_status = 'pending'
            RETURNING id::text, risk_id::text, control_id::text,
                      link_type, notes, created_at::text, created_by::text,
                      approval_status,
                      approved_by::text, approved_at::text,
                      rejection_reason, ai_confidence, ai_rationale
            """,
            mapping_id,
            approved_by,
            now,
            notes,
        )
        return _row_to_mapping(row) if row else None

    async def reject_mapping(
        self,
        connection: asyncpg.Connection,
        *,
        mapping_id: str,
        rejected_by: str,
        now: datetime,
        rejection_reason: str | None = None,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."30_lnk_risk_control_mappings"
            SET approval_status = 'rejected',
                approved_by = $2::uuid,
                approved_at = $3,
                rejection_reason = $4
            WHERE id = $1::uuid AND approval_status = 'pending'
            """,
            mapping_id,
            rejected_by,
            now,
            rejection_reason,
        )
        return result != "UPDATE 0"

    async def delete_control_mapping(
        self, connection: asyncpg.Connection, mapping_id: str
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."30_lnk_risk_control_mappings"
            WHERE id = $1::uuid
            """,
            mapping_id,
        )
        return result != "DELETE 0"

    async def get_control_mapping_by_id(
        self, connection: asyncpg.Connection, mapping_id: str
    ) -> ControlMappingRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, risk_id::text, control_id::text,
                   link_type, notes, created_at::text, created_by::text,
                   approval_status,
                   approved_by::text, approved_at::text,
                   rejection_reason, ai_confidence, ai_rationale
            FROM {SCHEMA}."30_lnk_risk_control_mappings"
            WHERE id = $1::uuid
            """,
            mapping_id,
        )
        return _row_to_mapping(row) if row else None


def _row_to_mapping(r) -> ControlMappingRecord:
    return ControlMappingRecord(
        id=r["id"],
        risk_id=r["risk_id"],
        control_id=r["control_id"],
        link_type=r["link_type"],
        notes=r["notes"],
        created_at=r["created_at"],
        created_by=r["created_by"],
        approval_status=r.get("approval_status", "approved"),
        approved_by=r.get("approved_by"),
        approved_at=r.get("approved_at"),
        rejection_reason=r.get("rejection_reason"),
        ai_confidence=float(r["ai_confidence"])
        if r.get("ai_confidence") is not None
        else None,
        ai_rationale=r.get("ai_rationale"),
        control_code=r.get("control_code"),
        control_name=r.get("control_name"),
        risk_code=r.get("risk_code"),
        risk_title=r.get("risk_title"),
    )
