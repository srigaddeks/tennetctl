"""Generic entity settings repository — parameterised SQL for any EAV entity."""

from __future__ import annotations

from uuid import uuid4

import asyncpg


class EntitySettingsRepository:
    """Runs EAV CRUD against any entity's settings tables."""

    # ── dimension table queries ────────────────────────────────────────

    @staticmethod
    async def setting_key_exists(
        connection: asyncpg.Connection,
        *,
        dimension_table: str,
        setting_key: str,
    ) -> bool:
        row = await connection.fetchrow(
            f"SELECT 1 FROM {dimension_table} WHERE code = $1",
            setting_key,
        )
        return row is not None

    @staticmethod
    async def list_setting_keys(
        connection: asyncpg.Connection,
        *,
        dimension_table: str,
    ) -> list[dict]:
        rows = await connection.fetch(
            f"SELECT code, name, description, data_type, is_pii, is_required, sort_order "
            f"FROM {dimension_table} ORDER BY sort_order"
        )
        return [dict(r) for r in rows]

    # ── detail table queries ───────────────────────────────────────────

    @staticmethod
    async def list_settings(
        connection: asyncpg.Connection,
        *,
        detail_table: str,
        entity_id_column: str,
        entity_id: str,
    ) -> list[tuple[str, str]]:
        rows = await connection.fetch(
            f"SELECT setting_key, setting_value "
            f"FROM {detail_table} "
            f"WHERE {entity_id_column} = $1 "
            f"ORDER BY setting_key",
            entity_id,
        )
        return [(r["setting_key"], r["setting_value"]) for r in rows]

    @staticmethod
    async def upsert_setting(
        connection: asyncpg.Connection,
        *,
        detail_table: str,
        entity_id_column: str,
        entity_id: str,
        setting_key: str,
        setting_value: str,
        updated_by: str | None,
        now,
    ) -> str:
        setting_id = str(uuid4())
        await connection.execute(
            f"INSERT INTO {detail_table} "
            f"    (id, {entity_id_column}, setting_key, setting_value, "
            f"     created_at, updated_at, created_by, updated_by) "
            f"VALUES ($1, $2, $3, $4, $5, $6, $7, $8) "
            f"ON CONFLICT ({entity_id_column}, setting_key) DO UPDATE SET "
            f"    setting_value = EXCLUDED.setting_value, "
            f"    updated_at = EXCLUDED.updated_at, "
            f"    updated_by = EXCLUDED.updated_by",
            setting_id,
            entity_id,
            setting_key,
            setting_value,
            now,
            now,
            updated_by,
            updated_by,
        )
        return setting_id

    @staticmethod
    async def delete_setting(
        connection: asyncpg.Connection,
        *,
        detail_table: str,
        entity_id_column: str,
        entity_id: str,
        setting_key: str,
    ) -> bool:
        result = await connection.execute(
            f"DELETE FROM {detail_table} "
            f"WHERE {entity_id_column} = $1 AND setting_key = $2",
            entity_id,
            setting_key,
        )
        return result != "DELETE 0"

    # ── fact table queries ─────────────────────────────────────────────

    @staticmethod
    async def entity_exists(
        connection: asyncpg.Connection,
        *,
        fact_table: str,
        fact_id_column: str,
        entity_id: str,
        tenant_key_column: str | None = "tenant_key",
    ) -> str | None:
        """Return tenant_key if entity exists, else None.

        Pass tenant_key_column=None for dimension tables that have no tenant_key column.
        Returns 'default' in that case (entity is global/shared).
        """
        if tenant_key_column is None:
            row = await connection.fetchrow(
                f"SELECT 1 FROM {fact_table} WHERE {fact_id_column} = $1",
                entity_id,
            )
            return "default" if row else None
        row = await connection.fetchrow(
            f"SELECT {tenant_key_column} FROM {fact_table} WHERE {fact_id_column} = $1",
            entity_id,
        )
        return row[tenant_key_column] if row else None

    @staticmethod
    async def resolve_code_to_id(
        connection: asyncpg.Connection,
        *,
        code_lookup_table: str,
        code_lookup_column: str,
        code: str,
    ) -> str | None:
        """Resolve a human-readable code to a UUID id."""
        row = await connection.fetchrow(
            f"SELECT id FROM {code_lookup_table} WHERE {code_lookup_column} = $1",
            code,
        )
        return str(row["id"]) if row else None
