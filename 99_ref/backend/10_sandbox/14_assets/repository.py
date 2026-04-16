from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import Asset, AssetAccessGrant, AssetProperty, AssetSnapshot, AssetSnapshotProperty

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

# Role hierarchy for access checks: lower index = lower privilege
_ROLE_HIERARCHY = ["view", "use", "edit"]


@instrument_class_methods(
    namespace="sandbox.assets.repository",
    logger_name="backend.sandbox.assets.repository.instrumentation",
)
class AssetRepository:

    async def list_assets(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        connector_id: str | None = None,
        asset_type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[Asset], int]:
        filters = ["org_id = $1", "is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2

        if connector_id is not None:
            filters.append(f"connector_instance_id = ${idx}")
            values.append(connector_id)
            idx += 1
        if asset_type is not None:
            filters.append(f"asset_type_code = ${idx}")
            values.append(asset_type)
            idx += 1
        if status is not None:
            filters.append(f"status_code = ${idx}")
            values.append(status)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, workspace_id::text,
                   connector_instance_id::text, provider_code, asset_type_code,
                   asset_external_id, parent_asset_id::text,
                   status_code, current_snapshot_id::text,
                   last_collected_at::text, consecutive_misses,
                   created_by::text, created_at::text, updated_at::text, is_deleted,
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."33_fct_assets"
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_asset(r) for r in rows], total

    async def count_assets(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        connector_id: str | None = None,
        asset_type: str | None = None,
        status: str | None = None,
    ) -> int:
        filters = ["org_id = $1", "is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2

        if connector_id is not None:
            filters.append(f"connector_instance_id = ${idx}")
            values.append(connector_id)
            idx += 1
        if asset_type is not None:
            filters.append(f"asset_type_code = ${idx}")
            values.append(asset_type)
            idx += 1
        if status is not None:
            filters.append(f"status_code = ${idx}")
            values.append(status)
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."33_fct_assets" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    async def get_asset(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        org_id: str,
    ) -> Asset | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, workspace_id::text,
                   connector_instance_id::text, provider_code, asset_type_code,
                   asset_external_id, parent_asset_id::text,
                   status_code, current_snapshot_id::text,
                   last_collected_at::text, consecutive_misses,
                   created_by::text, created_at::text, updated_at::text, is_deleted
            FROM {SCHEMA}."33_fct_assets"
            WHERE id = $1 AND org_id = $2 AND is_deleted = FALSE
            """,
            asset_id,
            org_id,
        )
        return _row_to_asset(row) if row else None

    async def upsert_asset(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        connector_instance_id: str,
        provider_code: str,
        asset_type_code: str,
        asset_external_id: str,
        parent_asset_id: str | None,
        created_by: str,
    ) -> Asset:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."33_fct_assets"
                (id, tenant_key, org_id, workspace_id, connector_instance_id,
                 provider_code, asset_type_code, asset_external_id, parent_asset_id,
                 status_code, consecutive_misses, is_deleted,
                 created_at, updated_at, created_by)
            VALUES
                (gen_random_uuid(), $1, $2, $3, $4,
                 $5, $6, $7, $8,
                 'active', 0, FALSE,
                 NOW(), NOW(), $9)
            ON CONFLICT (connector_instance_id, asset_type_code, asset_external_id)
            DO UPDATE SET
                status_code = 'active',
                updated_at = NOW()
            RETURNING
                id, tenant_key, org_id, workspace_id::text,
                connector_instance_id::text, provider_code, asset_type_code,
                asset_external_id, parent_asset_id::text,
                status_code, current_snapshot_id::text,
                last_collected_at::text, consecutive_misses,
                created_by::text, created_at::text, updated_at::text, is_deleted
            """,
            tenant_key,
            org_id,
            workspace_id,
            connector_instance_id,
            provider_code,
            asset_type_code,
            asset_external_id,
            parent_asset_id,
            created_by,
        )
        return _row_to_asset(row)

    async def update_asset_status(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        status_code: str,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."33_fct_assets"
            SET status_code = $1, updated_at = NOW()
            WHERE id = $2 AND is_deleted = FALSE
            """,
            status_code,
            asset_id,
        )

    async def soft_delete_asset(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        deleted_by: str,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."33_fct_assets"
            SET is_deleted = TRUE, status_code = 'deleted',
                deleted_at = NOW(), deleted_by = $1,
                updated_at = NOW()
            WHERE id = $2 AND is_deleted = FALSE
            """,
            deleted_by,
            asset_id,
        )

    async def set_current_snapshot(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        snapshot_id: str,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."33_fct_assets"
            SET current_snapshot_id = $1, updated_at = NOW()
            WHERE id = $2 AND is_deleted = FALSE
            """,
            snapshot_id,
            asset_id,
        )

    async def upsert_asset_properties(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        properties: dict[str, str],
    ) -> None:
        # Delete existing then batch insert all
        await connection.execute(
            f'DELETE FROM {SCHEMA}."54_dtl_asset_properties" WHERE asset_id = $1',
            asset_id,
        )
        if not properties:
            return
        rows = [(asset_id, key, value) for key, value in properties.items()]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."54_dtl_asset_properties"
                (id, asset_id, property_key, property_value, value_type, collected_at)
            VALUES (gen_random_uuid(), $1, $2, $3, 'string', NOW())
            """,
            rows,
        )

    async def get_asset_properties(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
    ) -> list[AssetProperty]:
        rows = await connection.fetch(
            f"""
            SELECT id, asset_id::text, property_key, property_value,
                   value_type, collected_at::text
            FROM {SCHEMA}."54_dtl_asset_properties"
            WHERE asset_id = $1
            ORDER BY property_key ASC
            """,
            asset_id,
        )
        return [_row_to_asset_property(r) for r in rows]

    async def create_snapshot(
        self,
        connection: asyncpg.Connection,
        *,
        asset_id: str,
        collection_run_id: str | None,
        snapshot_number: int,
        schema_fingerprint: str,
        properties: dict[str, str],
    ) -> AssetSnapshot:
        property_count = len(properties)
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."34_fct_asset_snapshots"
                (id, asset_id, collection_run_id, snapshot_number,
                 schema_fingerprint, property_count, collected_at)
            VALUES
                (gen_random_uuid(), $1, $2, $3, $4, $5, NOW())
            RETURNING
                id, asset_id::text, collection_run_id::text,
                snapshot_number, schema_fingerprint, property_count,
                collected_at::text
            """,
            asset_id,
            collection_run_id,
            snapshot_number,
            schema_fingerprint,
            property_count,
        )
        snapshot = _row_to_snapshot(row)

        if properties:
            prop_rows = [(snapshot.id, key, value) for key, value in properties.items()]
            await connection.executemany(
                f"""
                INSERT INTO {SCHEMA}."55_dtl_asset_snapshot_properties"
                    (id, snapshot_id, property_key, property_value, value_type)
                VALUES (gen_random_uuid(), $1, $2, $3, 'string')
                """,
                prop_rows,
            )

        return snapshot

    async def get_snapshots(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        *,
        limit: int = 20,
    ) -> list[AssetSnapshot]:
        rows = await connection.fetch(
            f"""
            SELECT id, asset_id::text, collection_run_id::text,
                   snapshot_number, schema_fingerprint, property_count,
                   collected_at::text
            FROM {SCHEMA}."34_fct_asset_snapshots"
            WHERE asset_id = $1
            ORDER BY snapshot_number DESC
            LIMIT {limit}
            """,
            asset_id,
        )
        return [_row_to_snapshot(r) for r in rows]

    async def get_snapshot_properties(
        self,
        connection: asyncpg.Connection,
        snapshot_id: str,
    ) -> list[AssetSnapshotProperty]:
        rows = await connection.fetch(
            f"""
            SELECT id, snapshot_id::text, property_key, property_value, value_type
            FROM {SCHEMA}."55_dtl_asset_snapshot_properties"
            WHERE snapshot_id = $1
            ORDER BY property_key ASC
            """,
            snapshot_id,
        )
        return [_row_to_snapshot_property(r) for r in rows]

    async def list_access_grants(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
    ) -> list[AssetAccessGrant]:
        rows = await connection.fetch(
            f"""
            SELECT id, asset_id::text, user_group_id::text,
                   role_code, granted_by::text, granted_at::text
            FROM {SCHEMA}."57_lnk_asset_access_grants"
            WHERE asset_id = $1
            ORDER BY granted_at ASC
            """,
            asset_id,
        )
        return [_row_to_grant(r) for r in rows]

    async def create_access_grant(
        self,
        connection: asyncpg.Connection,
        *,
        asset_id: str,
        user_group_id: str,
        role_code: str,
        granted_by: str,
    ) -> AssetAccessGrant:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."57_lnk_asset_access_grants"
                (id, asset_id, user_group_id, role_code, granted_by, granted_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW())
            ON CONFLICT (asset_id, user_group_id) DO UPDATE
            SET role_code = EXCLUDED.role_code,
                granted_by = EXCLUDED.granted_by,
                granted_at = NOW()
            RETURNING
                id, asset_id::text, user_group_id::text,
                role_code, granted_by::text, granted_at::text
            """,
            asset_id,
            user_group_id,
            role_code,
            granted_by,
        )
        return _row_to_grant(row)

    async def delete_access_grant(
        self,
        connection: asyncpg.Connection,
        grant_id: str,
    ) -> bool:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."57_lnk_asset_access_grants" WHERE id = $1',
            grant_id,
        )
        return result != "DELETE 0"

    async def check_access_grant(
        self,
        connection: asyncpg.Connection,
        asset_id: str,
        user_group_id: str,
        min_role: str,
    ) -> bool:
        """Return True if the user_group has at least min_role on this asset."""
        row = await connection.fetchrow(
            f"""
            SELECT role_code
            FROM {SCHEMA}."57_lnk_asset_access_grants"
            WHERE asset_id = $1 AND user_group_id = $2
            """,
            asset_id,
            user_group_id,
        )
        if row is None:
            return False
        try:
            granted_level = _ROLE_HIERARCHY.index(row["role_code"])
            required_level = _ROLE_HIERARCHY.index(min_role)
            return granted_level >= required_level
        except ValueError:
            return False


def _row_to_asset(r) -> Asset:
    return Asset(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        connector_instance_id=r["connector_instance_id"],
        provider_code=r["provider_code"],
        asset_type_code=r["asset_type_code"],
        asset_external_id=r["asset_external_id"],
        parent_asset_id=r["parent_asset_id"],
        status_code=r["status_code"],
        current_snapshot_id=r["current_snapshot_id"],
        last_collected_at=r["last_collected_at"],
        consecutive_misses=r["consecutive_misses"],
        created_by=r["created_by"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        is_deleted=r["is_deleted"],
    )


def _row_to_asset_property(r) -> AssetProperty:
    return AssetProperty(
        id=r["id"],
        asset_id=r["asset_id"],
        property_key=r["property_key"],
        property_value=r["property_value"],
        value_type=r["value_type"],
        collected_at=r["collected_at"],
    )


def _row_to_snapshot(r) -> AssetSnapshot:
    return AssetSnapshot(
        id=r["id"],
        asset_id=r["asset_id"],
        collection_run_id=r["collection_run_id"],
        snapshot_number=r["snapshot_number"],
        schema_fingerprint=r["schema_fingerprint"],
        property_count=r["property_count"],
        collected_at=r["collected_at"],
    )


def _row_to_snapshot_property(r) -> AssetSnapshotProperty:
    return AssetSnapshotProperty(
        id=r["id"],
        snapshot_id=r["snapshot_id"],
        property_key=r["property_key"],
        property_value=r["property_value"],
        value_type=r["value_type"],
    )


def _row_to_grant(r) -> AssetAccessGrant:
    return AssetAccessGrant(
        id=r["id"],
        asset_id=r["asset_id"],
        user_group_id=r["user_group_id"],
        role_code=r["role_code"],
        granted_by=r["granted_by"],
        granted_at=r["granted_at"],
    )
