from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TestMappingRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="grc.test_mappings.repository", logger_name="backend.grc.test_mappings.repository.instrumentation")
class TestMappingRepository:
    async def list_mappings(
        self, connection: asyncpg.Connection, *, control_test_id: str
    ) -> list[TestMappingRecord]:
        rows = await connection.fetch(
            f"""
            SELECT m.id, m.control_test_id, m.control_id::text, m.is_primary, m.sort_order,
                   m.created_at::text, m.created_by::text,
                   c.control_code,
                   p_name.property_value AS control_name,
                   f.framework_code
            FROM {SCHEMA}."30_lnk_test_control_mappings" m
            JOIN {SCHEMA}."13_fct_controls" c ON c.id = m.control_id
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN {SCHEMA}."10_fct_frameworks" f ON f.id = c.framework_id
            WHERE m.control_test_id = $1 AND c.is_deleted = FALSE
            ORDER BY m.sort_order, c.control_code
            """,
            control_test_id,
        )
        return [_row_to_mapping(r) for r in rows]

    async def create_mapping(
        self,
        connection: asyncpg.Connection,
        *,
        mapping_id: str,
        control_test_id: str,
        control_id: str,
        is_primary: bool,
        sort_order: int,
        created_by: str,
        now: object,
    ) -> TestMappingRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."30_lnk_test_control_mappings"
                (id, control_test_id, control_id, is_primary, sort_order, created_at, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (control_test_id, control_id) DO NOTHING
            RETURNING id, control_test_id, control_id::text, is_primary, sort_order,
                      created_at::text, created_by::text
            """,
            mapping_id,
            control_test_id,
            control_id,
            is_primary,
            sort_order,
            now,
            created_by,
        )
        if row is None:
            # Already exists, fetch it
            row = await connection.fetchrow(
                f"""
                SELECT id, control_test_id, control_id::text, is_primary, sort_order,
                       created_at::text, created_by::text
                FROM {SCHEMA}."30_lnk_test_control_mappings"
                WHERE control_test_id = $1 AND control_id = $2
                """,
                control_test_id,
                control_id,
            )
        return TestMappingRecord(
            id=row["id"],
            control_test_id=row["control_test_id"],
            control_id=row["control_id"],
            is_primary=row["is_primary"],
            sort_order=row["sort_order"],
            created_at=row["created_at"],
            created_by=row["created_by"],
        )

    async def delete_mapping(
        self,
        connection: asyncpg.Connection,
        mapping_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."30_lnk_test_control_mappings"
            WHERE id = $1
            """,
            mapping_id,
        )
        return result != "DELETE 0"


def _row_to_mapping(r) -> TestMappingRecord:
    return TestMappingRecord(
        id=r["id"],
        control_test_id=r["control_test_id"],
        control_id=r["control_id"],
        is_primary=r["is_primary"],
        sort_order=r["sort_order"],
        created_at=r["created_at"],
        created_by=r["created_by"],
        control_code=r.get("control_code"),
        control_name=r.get("control_name"),
        framework_code=r.get("framework_code"),
    )
