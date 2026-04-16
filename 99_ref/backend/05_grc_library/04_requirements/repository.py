from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import RequirementRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="grc.requirements.repository",
    logger_name="backend.grc.requirements.repository.instrumentation",
)
class RequirementRepository:
    async def list_requirements(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        version_id: str | None = None,
    ) -> list[RequirementRecord]:
        if version_id:
            rows = await connection.fetch(
                f"""
                SELECT r.id, r.framework_id, r.requirement_code, r.sort_order,
                       r.parent_requirement_id::text, r.is_active,
                       r.created_at::text, r.updated_at::text,
                       p_name.property_value AS name,
                       p_desc.property_value AS description
                FROM {SCHEMA}."12_fct_requirements" r
                LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_name
                    ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
                LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_desc
                    ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
                WHERE r.framework_id = $1 AND r.is_deleted = FALSE
                  AND EXISTS (
                      SELECT 1 FROM {SCHEMA}."31_lnk_framework_version_controls" lvc
                      JOIN {SCHEMA}."13_fct_controls" c ON c.id = lvc.control_id
                      WHERE lvc.framework_version_id = $2::uuid AND c.requirement_id = r.id
                  )
                ORDER BY r.sort_order, r.requirement_code
                """,
                framework_id,
                version_id,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT r.id, r.framework_id, r.requirement_code, r.sort_order,
                       r.parent_requirement_id::text, r.is_active,
                       r.created_at::text, r.updated_at::text,
                       p_name.property_value AS name,
                       p_desc.property_value AS description
                FROM {SCHEMA}."12_fct_requirements" r
                LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_name
                    ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
                LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_desc
                    ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
                WHERE r.framework_id = $1 AND r.is_deleted = FALSE
                ORDER BY r.sort_order, r.requirement_code
                """,
                framework_id,
            )
        return [_row_to_requirement(r) for r in rows]

    async def get_requirement_by_id(
        self, connection: asyncpg.Connection, requirement_id: str
    ) -> RequirementRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT r.id, r.framework_id, r.requirement_code, r.sort_order,
                   r.parent_requirement_id::text, r.is_active,
                   r.created_at::text, r.updated_at::text,
                   p_name.property_value AS name,
                   p_desc.property_value AS description
            FROM {SCHEMA}."12_fct_requirements" r
            LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_name
                ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_desc
                ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            WHERE r.id = $1 AND r.is_deleted = FALSE
            """,
            requirement_id,
        )
        return _row_to_requirement(row) if row else None

    async def create_requirement(
        self,
        connection: asyncpg.Connection,
        *,
        requirement_id: str,
        framework_id: str,
        requirement_code: str,
        sort_order: int,
        parent_requirement_id: str | None,
        created_by: str,
        now: object,
    ) -> RequirementRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."12_fct_requirements"
                (id, framework_id, requirement_code, sort_order, parent_requirement_id,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                 $6, $7, $8, $9, NULL, NULL)
            RETURNING id, framework_id, requirement_code, sort_order,
                      parent_requirement_id::text, is_active,
                      created_at::text, updated_at::text
            """,
            requirement_id,
            framework_id,
            requirement_code,
            sort_order,
            parent_requirement_id,
            now,
            now,
            created_by,
            created_by,
        )
        return RequirementRecord(
            id=row["id"],
            framework_id=row["framework_id"],
            requirement_code=row["requirement_code"],
            sort_order=row["sort_order"],
            parent_requirement_id=row["parent_requirement_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def update_requirement(
        self,
        connection: asyncpg.Connection,
        requirement_id: str,
        *,
        requirement_code: str | None = None,
        sort_order: int | None = None,
        parent_requirement_id: str | None = None,
        updated_by: str,
        now: object,
    ) -> RequirementRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if requirement_code is not None:
            fields.append(f"requirement_code = ${idx}")
            values.append(requirement_code)
            idx += 1
        if sort_order is not None:
            fields.append(f"sort_order = ${idx}")
            values.append(sort_order)
            idx += 1
        if parent_requirement_id is not None:
            fields.append(f"parent_requirement_id = ${idx}")
            values.append(parent_requirement_id)
            idx += 1

        values.append(requirement_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."12_fct_requirements"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, framework_id, requirement_code, sort_order,
                      parent_requirement_id::text, is_active,
                      created_at::text, updated_at::text
            """,
            *values,
        )
        if row is None:
            return None
        return RequirementRecord(
            id=row["id"],
            framework_id=row["framework_id"],
            requirement_code=row["requirement_code"],
            sort_order=row["sort_order"],
            parent_requirement_id=row["parent_requirement_id"],
            is_active=row["is_active"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    async def soft_delete_requirement(
        self,
        connection: asyncpg.Connection,
        requirement_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_fct_requirements"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            requirement_id,
        )
        return result != "UPDATE 0"

    async def upsert_requirement_properties(
        self,
        connection: asyncpg.Connection,
        *,
        requirement_id: str,
        properties: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (requirement_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {SCHEMA}."22_dtl_requirement_properties"
                    (id, requirement_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (requirement_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
            rows,
        )


def _row_to_requirement(r) -> RequirementRecord:
    return RequirementRecord(
        id=r["id"],
        framework_id=r["framework_id"],
        requirement_code=r["requirement_code"],
        sort_order=r["sort_order"],
        parent_requirement_id=r["parent_requirement_id"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r.get("name"),
        description=r.get("description"),
    )
