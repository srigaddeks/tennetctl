from __future__ import annotations

import json
import uuid
from importlib import import_module

import asyncpg

from .models import AssetConnector

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_CI = '"15_sandbox"."20_fct_connector_instances"'
_PROPS = '"15_sandbox"."40_dtl_connector_instance_properties"'
_CREDS = '"15_sandbox"."41_dtl_connector_credentials"'

_SELECT_COLS = """
    ci.id::text,
    ci.tenant_key,
    ci.org_id::text,
    ci.instance_code,
    ci.provider_definition_code,
    ci.provider_version_code,
    ci.connection_config,
    ci.collection_schedule,
    ci.last_collected_at::text,
    ci.health_status,
    ci.consecutive_failures,
    ci.cooldown_until::text,
    ci.is_active,
    ci.created_at::text,
    ci.updated_at::text,
    MAX(CASE WHEN p.property_key = 'name'        THEN p.property_value END) AS name,
    MAX(CASE WHEN p.property_key = 'description' THEN p.property_value END) AS description
"""

_FROM_JOIN = f"""
    FROM {_CI} ci
    LEFT JOIN {_PROPS} p ON p.connector_instance_id = ci.id
"""

_GROUP_BY = """
    GROUP BY ci.id, ci.tenant_key, ci.org_id, ci.instance_code,
             ci.provider_definition_code, ci.provider_version_code,
             ci.connection_config, ci.collection_schedule, ci.last_collected_at,
             ci.health_status, ci.consecutive_failures, ci.cooldown_until,
             ci.is_active, ci.created_at, ci.updated_at
"""


@instrument_class_methods(
    namespace="sandbox.asset_connectors.repository",
    logger_name="backend.sandbox.asset_connectors.repository.instrumentation",
)
class AssetConnectorRepository:

    async def list_connectors(
        self,
        conn: asyncpg.Connection,
        *,
        org_id: str,
        provider_code: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> list[AssetConnector]:
        filters = ["ci.org_id = $1", "ci.is_deleted = FALSE",
                   "ci.provider_definition_code IS NOT NULL"]
        values: list = [org_id]
        idx = 2
        if provider_code:
            filters.append(f"ci.provider_definition_code = ${idx}")
            values.append(provider_code)
            idx += 1
        where = " AND ".join(filters)
        rows = await conn.fetch(
            f"SELECT {_SELECT_COLS} {_FROM_JOIN} WHERE {where} {_GROUP_BY}"
            f" ORDER BY ci.created_at DESC LIMIT {limit} OFFSET {offset}",
            *values,
        )
        return [_row(r) for r in rows]

    async def count_connectors(
        self,
        conn: asyncpg.Connection,
        *,
        org_id: str,
        provider_code: str | None = None,
    ) -> int:
        filters = ["org_id = $1", "is_deleted = FALSE",
                   "provider_definition_code IS NOT NULL"]
        values: list = [org_id]
        if provider_code:
            filters.append("provider_definition_code = $2")
            values.append(provider_code)
        where = " AND ".join(filters)
        row = await conn.fetchrow(
            f"SELECT COUNT(*)::int AS total FROM {_CI} WHERE {where}", *values
        )
        return row["total"] if row else 0

    async def get_connector(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
        org_id: str,
    ) -> AssetConnector | None:
        row = await conn.fetchrow(
            f"SELECT {_SELECT_COLS} {_FROM_JOIN}"
            " WHERE ci.id = $1 AND ci.org_id = $2 AND ci.is_deleted = FALSE"
            f" {_GROUP_BY}",
            connector_id, org_id,
        )
        return _row(row) if row else None

    async def create_connector(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        instance_code: str,
        provider_definition_code: str,
        provider_version_code: str | None,
        connection_config: dict,
        collection_schedule: str,
        created_by: str,
    ) -> str:
        """Creates the connector instance row. Returns the new UUID as str."""
        new_id = str(uuid.uuid4())
        config_json = json.dumps(connection_config)
        await conn.execute(
            f"""
            INSERT INTO {_CI}
                (id, tenant_key, org_id, instance_code,
                 connector_type_code,
                 provider_definition_code, provider_version_code,
                 connection_config, collection_schedule,
                 health_status, consecutive_failures,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by)
            VALUES
                ($1, $2, $3, $4,
                 'asset_inventory',
                 $5, $6,
                 $7::jsonb, $8,
                 'unchecked', 0,
                 TRUE, FALSE,
                 NOW(), NOW(), $9, $9)
            """,
            new_id, tenant_key, org_id, instance_code,
            provider_definition_code, provider_version_code,
            config_json, collection_schedule,
            created_by,
        )
        return new_id

    async def upsert_property(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
        key: str,
        value: str,
    ) -> None:
        await conn.execute(
            f"""
            INSERT INTO {_PROPS} (id, connector_instance_id, property_key, property_value)
            VALUES (gen_random_uuid(), $1, $2, $3)
            ON CONFLICT (connector_instance_id, property_key)
            DO UPDATE SET property_value = EXCLUDED.property_value
            """,
            connector_id, key, value,
        )

    async def update_connector(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
        org_id: str,
        *,
        connection_config: dict | None = None,
        collection_schedule: str | None = None,
        provider_version_code: str | None = None,
        is_active: bool | None = None,
        updated_by: str,
    ) -> None:
        sets = ["updated_at = NOW()", "updated_by = $3"]
        values: list = [connector_id, org_id, updated_by]
        idx = 4
        if connection_config is not None:
            sets.append(f"connection_config = ${idx}::jsonb")
            values.append(json.dumps(connection_config))
            idx += 1
        if collection_schedule is not None:
            sets.append(f"collection_schedule = ${idx}")
            values.append(collection_schedule)
            idx += 1
        if provider_version_code is not None:
            sets.append(f"provider_version_code = ${idx}")
            values.append(provider_version_code)
            idx += 1
        if is_active is not None:
            sets.append(f"is_active = ${idx}")
            values.append(is_active)
            idx += 1
        await conn.execute(
            f"UPDATE {_CI} SET {', '.join(sets)}"
            " WHERE id = $1 AND org_id = $2 AND is_deleted = FALSE",
            *values,
        )

    async def delete_connector(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
        org_id: str,
        deleted_by: str,
    ) -> bool:
        result = await conn.execute(
            f"""
            UPDATE {_CI}
            SET is_deleted = TRUE, deleted_at = NOW(), deleted_by = $3,
                updated_at = NOW(), updated_by = $3
            WHERE id = $1 AND org_id = $2 AND is_deleted = FALSE
            """,
            connector_id, org_id, deleted_by,
        )
        return result != "UPDATE 0"

    async def upsert_credentials(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
        credentials: dict[str, str],  # already-encrypted values
    ) -> None:
        """Replaces all credentials for a connector."""
        await conn.execute(
            f"DELETE FROM {_CREDS} WHERE connector_instance_id = $1",
            connector_id,
        )
        for key, encrypted_value in credentials.items():
            await conn.execute(
                f"""
                INSERT INTO {_CREDS}
                    (id, connector_instance_id, credential_key, encrypted_value, encryption_key_id)
                VALUES (gen_random_uuid(), $1, $2, $3, 'default')
                """,
                connector_id, key, encrypted_value,
            )

    async def update_health(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
        *,
        health_status: str,
        consecutive_failures: int,
        last_collected_at: str | None = None,
        cooldown_until: str | None = None,
    ) -> None:
        sets = [
            "health_status = $2",
            "consecutive_failures = $3",
            "updated_at = NOW()",
        ]
        values: list = [connector_id, health_status, consecutive_failures]
        idx = 4
        if last_collected_at is not None:
            sets.append(f"last_collected_at = ${idx}")
            values.append(last_collected_at)
            idx += 1
        if cooldown_until is not None:
            sets.append(f"cooldown_until = ${idx}")
            values.append(cooldown_until)
            idx += 1
        await conn.execute(
            f"UPDATE {_CI} SET {', '.join(sets)} WHERE id = $1",
            *values,
        )

    async def get_credentials_raw(
        self,
        conn: asyncpg.Connection,
        connector_id: str,
    ) -> list[asyncpg.Record]:
        return await conn.fetch(
            f"SELECT credential_key, encrypted_value FROM {_CREDS} WHERE connector_instance_id = $1",
            connector_id,
        )


def _row(r: asyncpg.Record) -> AssetConnector:
    d = dict(r)
    cfg = d.get("connection_config")
    if cfg and not isinstance(cfg, dict):
        try:
            cfg = json.loads(cfg)
        except Exception:
            cfg = {}
    return AssetConnector(
        id=d["id"],
        tenant_key=d["tenant_key"],
        org_id=d["org_id"],
        instance_code=d["instance_code"],
        provider_definition_code=d.get("provider_definition_code"),
        provider_version_code=d.get("provider_version_code"),
        connection_config=cfg,
        collection_schedule=d.get("collection_schedule", "manual"),
        last_collected_at=d.get("last_collected_at"),
        health_status=d.get("health_status", "unchecked"),
        consecutive_failures=d.get("consecutive_failures", 0),
        cooldown_until=d.get("cooldown_until"),
        is_active=d.get("is_active", True),
        created_at=d["created_at"],
        updated_at=d["updated_at"],
        name=d.get("name"),
        description=d.get("description"),
    )
