from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import ConnectorInstanceRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_SELECT_COLS = """
    id, tenant_key, org_id, workspace_id, instance_code,
    connector_type_code, connector_type_name,
    connector_category_code, connector_category_name,
    asset_version_id, collection_schedule,
    last_collected_at::text, health_status,
    is_active, is_draft, created_at::text, updated_at::text,
    name, description
"""


@instrument_class_methods(namespace="sandbox.connectors.repository", logger_name="backend.sandbox.connectors.repository.instrumentation")
class ConnectorRepository:

    async def list_connectors(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        connector_type_code: str | None = None,
        category_code: str | None = None,
        health_status: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ConnectorInstanceRecord], int]:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if connector_type_code is not None:
            filters.append(f"connector_type_code = ${idx}")
            values.append(connector_type_code)
            idx += 1
        if category_code is not None:
            filters.append(f"connector_category_code = ${idx}")
            values.append(category_code)
            idx += 1
        if health_status is not None:
            filters.append(f"health_status = ${idx}")
            values.append(health_status)
            idx += 1
        if is_active is not None:
            filters.append(f"is_active = ${idx}")
            values.append(is_active)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT {_SELECT_COLS},
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."60_vw_connector_instance_detail"
            WHERE {where_clause}
            ORDER BY instance_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_connector(r) for r in rows], total

    async def count_connectors(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        connector_type_code: str | None = None,
        category_code: str | None = None,
        health_status: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if connector_type_code is not None:
            filters.append(f"connector_type_code = ${idx}")
            values.append(connector_type_code)
            idx += 1
        if category_code is not None:
            filters.append(f"connector_category_code = ${idx}")
            values.append(category_code)
            idx += 1
        if health_status is not None:
            filters.append(f"health_status = ${idx}")
            values.append(health_status)
            idx += 1
        if is_active is not None:
            filters.append(f"is_active = ${idx}")
            values.append(is_active)
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."60_vw_connector_instance_detail" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    async def get_connector_by_id(
        self, connection: asyncpg.Connection, connector_id: str
    ) -> ConnectorInstanceRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT {_SELECT_COLS}
            FROM {SCHEMA}."60_vw_connector_instance_detail"
            WHERE id = $1
            """,
            connector_id,
        )
        return _row_to_connector(row) if row else None

    async def create_connector(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        instance_code: str,
        connector_type_code: str,
        asset_version_id: str | None,
        collection_schedule: str,
        is_draft: bool,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_fct_connector_instances"
                (id, tenant_key, org_id, workspace_id, instance_code, connector_type_code,
                 provider_definition_code, asset_version_id, collection_schedule,
                 health_status, is_active, is_draft, is_deleted,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $13, $4, $5,
                 $5, $6, $7, 'unchecked',
                 TRUE, $8, FALSE,
                 $9, $10, $11, $12, NULL, NULL)
            """,
            id,
            tenant_key,
            org_id,
            instance_code,
            connector_type_code,
            asset_version_id,
            collection_schedule,
            is_draft,
            now,
            now,
            created_by,
            created_by,
            workspace_id,
        )
        return id

    async def update_connector(
        self,
        connection: asyncpg.Connection,
        connector_id: str,
        *,
        collection_schedule: str | None = None,
        asset_version_id: str | None = None,
        is_draft: bool | None = None,
        is_active: bool | None = None,
        updated_by: str,
        now: object,
    ) -> bool:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if collection_schedule is not None:
            fields.append(f"collection_schedule = ${idx}")
            values.append(collection_schedule)
            idx += 1
        if asset_version_id is not None:
            fields.append(f"asset_version_id = ${idx}")
            values.append(asset_version_id)
            idx += 1
        if is_draft is not None:
            fields.append(f"is_draft = ${idx}")
            values.append(is_draft)
            idx += 1
        if is_active is not None:
            fields.append(f"is_active = ${idx}")
            values.append(is_active)
            idx += 1

        values.append(connector_id)
        set_clause = ", ".join(fields)

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_fct_connector_instances"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            """,
            *values,
        )
        return result != "UPDATE 0"

    async def soft_delete_connector(
        self,
        connection: asyncpg.Connection,
        connector_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_fct_connector_instances"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, connector_id,
        )
        return result != "UPDATE 0"

    async def get_properties(
        self,
        connection: asyncpg.Connection,
        connector_instance_id: str,
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."40_dtl_connector_instance_properties"
            WHERE connector_instance_id = $1
            """,
            connector_instance_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        connector_instance_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (connector_instance_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."40_dtl_connector_instance_properties"
                (id, connector_instance_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (connector_instance_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    async def upsert_credentials(
        self,
        connection: asyncpg.Connection,
        connector_instance_id: str,
        credentials: dict[str, str],
        *,
        encryption_key_id: str,
        created_by: str,
        now: object,
    ) -> None:
        if not credentials:
            return
        rows = [
            (connector_instance_id, key, value, encryption_key_id,
             now, now, created_by, created_by)
            for key, value in credentials.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."41_dtl_connector_credentials"
                (id, connector_instance_id, credential_key, encrypted_value,
                 encryption_key_id, created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (connector_instance_id, credential_key) DO UPDATE
            SET encrypted_value = EXCLUDED.encrypted_value,
                encryption_key_id = EXCLUDED.encryption_key_id,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    async def update_health_status(
        self,
        connection: asyncpg.Connection,
        connector_id: str,
        health_status: str,
        now: object,
        *,
        clear_draft: bool = False,
    ) -> bool:
        extra = ", is_draft = FALSE" if clear_draft else ""
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_fct_connector_instances"
            SET health_status = $1, updated_at = $2{extra}
            WHERE id = $3 AND is_deleted = FALSE
            """,
            health_status, now, connector_id,
        )
        return result != "UPDATE 0"


def _row_to_connector(r) -> ConnectorInstanceRecord:
    return ConnectorInstanceRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        org_id=str(r["org_id"]),
        workspace_id=str(r["workspace_id"]) if r["workspace_id"] else None,
        instance_code=r["instance_code"],
        connector_type_code=r["connector_type_code"],
        connector_type_name=r["connector_type_name"],
        connector_category_code=r["connector_category_code"],
        connector_category_name=r["connector_category_name"],
        asset_version_id=str(r["asset_version_id"]) if r["asset_version_id"] else None,
        collection_schedule=r["collection_schedule"],
        last_collected_at=r["last_collected_at"],
        health_status=r["health_status"],
        is_active=r["is_active"],
        is_draft=r["is_draft"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
    )
