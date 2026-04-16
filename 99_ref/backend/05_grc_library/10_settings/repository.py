from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import FrameworkSettingRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="grc.settings.repository", logger_name="backend.grc.settings.repository.instrumentation")
class FrameworkSettingRepository:
    async def list_settings(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> list[FrameworkSettingRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, framework_id, setting_key, setting_value,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."25_dtl_framework_settings"
            WHERE framework_id = $1
            ORDER BY setting_key
            """,
            framework_id,
        )
        return [_row_to_setting(r) for r in rows]

    async def upsert_setting(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        setting_key: str,
        setting_value: str,
        created_by: str,
        now: object,
    ) -> FrameworkSettingRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."25_dtl_framework_settings"
                (id, framework_id, setting_key, setting_value, created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (framework_id, setting_key) DO UPDATE
            SET setting_value = EXCLUDED.setting_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            RETURNING id, framework_id, setting_key, setting_value,
                      created_at::text, updated_at::text
            """,
            framework_id,
            setting_key,
            setting_value,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_setting(row)

    async def delete_setting(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        setting_key: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."25_dtl_framework_settings"
            WHERE framework_id = $1 AND setting_key = $2
            """,
            framework_id,
            setting_key,
        )
        return result != "DELETE 0"


def _row_to_setting(r) -> FrameworkSettingRecord:
    return FrameworkSettingRecord(
        id=r["id"],
        framework_id=r["framework_id"],
        setting_key=r["setting_key"],
        setting_value=r["setting_value"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )
