from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TestDetailRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


@instrument_class_methods(
    namespace="grc.tests.repository",
    logger_name="backend.grc.tests.repository.instrumentation",
)
class TestRepository:
    _TEST_SORT_COLUMNS = frozenset(
        {"name", "test_code", "created_at", "updated_at", "test_type_code"}
    )

    async def list_tests(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        search: str | None = None,
        test_type_code: str | None = None,
        is_platform_managed: bool | None = None,
        monitoring_frequency: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        sort_by: str = "name",
        sort_dir: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[TestDetailRecord], int]:
        filters = ["tenant_key = $1", "is_deleted = FALSE"]
        values: list[object] = [tenant_key]
        idx = 2

        if search is not None:
            filters.append(f"(LOWER(name) LIKE ${idx} OR LOWER(test_code) LIKE ${idx})")
            values.append(f"%{search.lower()}%")
            idx += 1
        if test_type_code is not None:
            filters.append(f"test_type_code = ${idx}")
            values.append(test_type_code)
            idx += 1
        if is_platform_managed is not None:
            filters.append(f"is_platform_managed = ${idx}")
            values.append(is_platform_managed)
            idx += 1
        if monitoring_frequency is not None:
            filters.append(f"monitoring_frequency = ${idx}")
            values.append(monitoring_frequency)
            idx += 1
        if scope_org_id is not None:
            filters.append(f"(scope_org_id = ${idx}::uuid OR scope_org_id IS NULL)")
            values.append(scope_org_id)
            idx += 1
        if scope_workspace_id is not None:
            filters.append(
                f"(scope_workspace_id = ${idx}::uuid OR scope_workspace_id IS NULL)"
            )
            values.append(scope_workspace_id)
            idx += 1

        where_clause = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."42_vw_test_detail" WHERE {where_clause}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        sort_col = sort_by if sort_by in self._TEST_SORT_COLUMNS else "name"
        sort_direction = "DESC" if sort_dir == "desc" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, test_code, test_type_code, test_type_name,
                   integration_type, monitoring_frequency, is_platform_managed,
                   is_active, created_at::text, updated_at::text,
                   name, description, evaluation_rule, signal_type, integration_guide,
                   mapped_control_count, scope_org_id::text, scope_workspace_id::text
            FROM {SCHEMA}."42_vw_test_detail"
            WHERE {where_clause}
            ORDER BY {sort_col} {sort_direction}, test_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_test(r) for r in rows], total

    async def list_tests_for_control(
        self,
        connection: asyncpg.Connection,
        *,
        control_id: str,
    ) -> list[TestDetailRecord]:
        rows = await connection.fetch(
            f"""
            SELECT t.id, t.tenant_key, t.test_code, t.test_type_code, t.test_type_name,
                   t.integration_type, t.monitoring_frequency, t.is_platform_managed,
                   t.is_active, t.created_at::text, t.updated_at::text,
                   t.name, t.description, t.evaluation_rule, t.signal_type, t.integration_guide,
                   t.mapped_control_count, t.scope_org_id::text, t.scope_workspace_id::text
            FROM {SCHEMA}."42_vw_test_detail" t
            JOIN {SCHEMA}."30_lnk_test_control_mappings" m ON m.control_test_id = t.id
            WHERE m.control_id = $1 AND t.is_deleted = FALSE
            ORDER BY m.is_primary DESC, t.test_code ASC
            """,
            control_id,
        )
        return [_row_to_test(r) for r in rows]

    async def list_tests_available_for_control(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        control_id: str,
        search: str | None = None,
        limit: int = 50,
    ) -> list[TestDetailRecord]:
        filters = ["t.tenant_key = $1", "t.is_deleted = FALSE"]
        values: list[object] = [tenant_key, control_id]
        idx = 3

        if search is not None:
            filters.append(
                f"(LOWER(t.name) LIKE ${idx} OR LOWER(t.test_code) LIKE ${idx})"
            )
            values.append(f"%{search.lower()}%")
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT t.id, t.tenant_key, t.test_code, t.test_type_code, t.test_type_name,
                   t.integration_type, t.monitoring_frequency, t.is_platform_managed,
                   t.is_active, t.created_at::text, t.updated_at::text,
                   t.name, t.description, t.evaluation_rule, t.signal_type, t.integration_guide,
                   t.mapped_control_count, t.scope_org_id::text, t.scope_workspace_id::text
            FROM {SCHEMA}."42_vw_test_detail" t
            WHERE {where_clause}
              AND t.id NOT IN (
                  SELECT m.control_test_id
                  FROM {SCHEMA}."30_lnk_test_control_mappings" m
                  WHERE m.control_id = $2
              )
            ORDER BY t.test_code ASC
            LIMIT {limit}
            """,
            *values,
        )
        return [_row_to_test(r) for r in rows]

    async def get_test_by_id(
        self, connection: asyncpg.Connection, test_id: str
    ) -> TestDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, test_code, test_type_code, test_type_name,
                   integration_type, monitoring_frequency, is_platform_managed,
                   is_active, created_at::text, updated_at::text,
                   name, description, evaluation_rule, signal_type, integration_guide,
                   mapped_control_count, scope_org_id::text, scope_workspace_id::text
            FROM {SCHEMA}."42_vw_test_detail"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            test_id,
        )
        return _row_to_test(row) if row else None

    async def create_test(
        self,
        connection: asyncpg.Connection,
        *,
        test_id: str,
        tenant_key: str,
        test_code: str,
        test_type_code: str,
        integration_type: str | None,
        monitoring_frequency: str,
        is_platform_managed: bool,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."14_fct_control_tests"
                (id, tenant_key, test_code, test_type_code, integration_type,
                 monitoring_frequency, is_platform_managed, scope_org_id, scope_workspace_id,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8::uuid, $9::uuid,
                 TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                 $10, $11, $12, $13, NULL, NULL)
            """,
            test_id,
            tenant_key,
            test_code,
            test_type_code,
            integration_type,
            monitoring_frequency,
            is_platform_managed,
            scope_org_id,
            scope_workspace_id,
            now,
            now,
            created_by,
            created_by,
        )
        return test_id

    async def update_test(
        self,
        connection: asyncpg.Connection,
        test_id: str,
        *,
        test_type_code: str | None = None,
        integration_type: str | None = None,
        monitoring_frequency: str | None = None,
        is_platform_managed: bool | None = None,
        updated_by: str,
        now: object,
    ) -> bool:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if test_type_code is not None:
            fields.append(f"test_type_code = ${idx}")
            values.append(test_type_code)
            idx += 1
        if integration_type is not None:
            fields.append(f"integration_type = ${idx}")
            values.append(integration_type)
            idx += 1
        if monitoring_frequency is not None:
            fields.append(f"monitoring_frequency = ${idx}")
            values.append(monitoring_frequency)
            idx += 1
        if is_platform_managed is not None:
            fields.append(f"is_platform_managed = ${idx}")
            values.append(is_platform_managed)
            idx += 1

        values.append(test_id)
        set_clause = ", ".join(fields)

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."14_fct_control_tests"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            """,
            *values,
        )
        return result != "UPDATE 0"

    async def soft_delete_test(
        self,
        connection: asyncpg.Connection,
        test_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."14_fct_control_tests"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            test_id,
        )
        return result != "UPDATE 0"

    async def upsert_test_properties(
        self,
        connection: asyncpg.Connection,
        *,
        test_id: str,
        properties: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (test_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {SCHEMA}."24_dtl_test_properties"
                    (id, test_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (test_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
            rows,
        )


def _row_to_test(r) -> TestDetailRecord:
    return TestDetailRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        test_code=r["test_code"],
        test_type_code=r["test_type_code"],
        test_type_name=r["test_type_name"],
        integration_type=r["integration_type"],
        monitoring_frequency=r["monitoring_frequency"],
        is_platform_managed=r["is_platform_managed"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
        evaluation_rule=r["evaluation_rule"],
        signal_type=r["signal_type"],
        integration_guide=r["integration_guide"],
        mapped_control_count=r["mapped_control_count"],
        scope_org_id=r["scope_org_id"],
        scope_workspace_id=r["scope_workspace_id"],
    )
