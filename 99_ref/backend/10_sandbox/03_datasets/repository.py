from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import DatasetRecord, DatasetDataRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.datasets.repository", logger_name="backend.sandbox.datasets.repository.instrumentation")
class DatasetRepository:
    _SORT_COLUMNS = frozenset({"name", "dataset_code", "created_at", "updated_at", "version_number", "byte_size", "row_count"})

    # ── list ──────────────────────────────────────────────────────────

    async def list_datasets(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        connector_instance_id: str | None = None,
        dataset_source_code: str | None = None,
        is_locked: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[DatasetRecord], int]:
        filters = ["d.org_id = $1", "d.is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"d.workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if connector_instance_id is not None:
            filters.append(f"d.connector_instance_id = ${idx}")
            values.append(connector_instance_id)
            idx += 1
        if dataset_source_code is not None:
            filters.append(f"d.dataset_source_code = ${idx}")
            values.append(dataset_source_code)
            idx += 1
        if is_locked is not None:
            filters.append(f"d.is_locked = ${idx}")
            values.append(is_locked)
            idx += 1

        where_clause = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {SCHEMA}."21_fct_datasets" d
            WHERE {where_clause}
            """,
            *values,
        )
        total = count_row["total"] if count_row else 0

        sort_col = sort_by if sort_by in self._SORT_COLUMNS else "created_at"
        sort_direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT d.id, d.tenant_key, d.org_id, d.workspace_id,
                   d.connector_instance_id, d.dataset_code, d.dataset_source_code,
                   d.version_number, d.schema_fingerprint,
                   d.row_count, d.byte_size,
                   d.collected_at::text, d.is_locked, d.is_active,
                   d.created_at::text, d.updated_at::text,
                   d.asset_ids,
                   pn.property_value AS name,
                   pd.property_value AS description
            FROM {SCHEMA}."21_fct_datasets" d
            LEFT JOIN {SCHEMA}."42_dtl_dataset_properties" pn
                ON pn.dataset_id = d.id AND pn.property_key = 'name'
            LEFT JOIN {SCHEMA}."42_dtl_dataset_properties" pd
                ON pd.dataset_id = d.id AND pd.property_key = 'description'
            WHERE {where_clause}
            ORDER BY {sort_col} {sort_direction}, d.dataset_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_dataset(r) for r in rows], total

    # ── get ───────────────────────────────────────────────────────────

    async def get_dataset_by_id(
        self, connection: asyncpg.Connection, dataset_id: str,
    ) -> DatasetRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT d.id, d.tenant_key, d.org_id, d.workspace_id,
                   d.connector_instance_id, d.dataset_code, d.dataset_source_code,
                   d.version_number, d.schema_fingerprint,
                   d.row_count, d.byte_size,
                   d.collected_at::text, d.is_locked, d.is_active,
                   d.created_at::text, d.updated_at::text,
                   d.asset_ids,
                   pn.property_value AS name,
                   pd.property_value AS description
            FROM {SCHEMA}."21_fct_datasets" d
            LEFT JOIN {SCHEMA}."42_dtl_dataset_properties" pn
                ON pn.dataset_id = d.id AND pn.property_key = 'name'
            LEFT JOIN {SCHEMA}."42_dtl_dataset_properties" pd
                ON pd.dataset_id = d.id AND pd.property_key = 'description'
            WHERE d.id = $1 AND d.is_deleted = FALSE
            """,
            dataset_id,
        )
        return _row_to_dataset(row) if row else None

    # ── create ────────────────────────────────────────────────────────

    async def create_dataset(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        connector_instance_id: str | None,
        dataset_code: str,
        dataset_source_code: str,
        version_number: int,
        schema_fingerprint: str | None,
        row_count: int,
        byte_size: int,
        asset_ids: list[str] | None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."21_fct_datasets"
                (id, tenant_key, org_id, workspace_id, connector_instance_id,
                 dataset_code, dataset_source_code, version_number,
                 schema_fingerprint, row_count, byte_size, asset_ids,
                 collected_at, is_locked, is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8,
                 $9, $10, $11, $12,
                 $13, FALSE, TRUE, FALSE,
                 $13, $13, $14, $14,
                 NULL, NULL)
            """,
            id,
            tenant_key,
            org_id,
            workspace_id,
            connector_instance_id,
            dataset_code,
            dataset_source_code,
            version_number,
            schema_fingerprint,
            row_count,
            byte_size,
            asset_ids,
            now,
            created_by,
        )
        return id

    # ── version ───────────────────────────────────────────────────────

    async def get_next_version_number(
        self, connection: asyncpg.Connection, org_id: str, dataset_code: str,
    ) -> int:
        """Returns next version number with advisory lock to prevent races.
        Must be called inside a transaction."""
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            f"sb:dataset_version:{org_id}:{dataset_code}",
        )
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."21_fct_datasets"
            WHERE org_id = $1 AND dataset_code = $2 AND is_deleted = FALSE
            """,
            org_id,
            dataset_code,
        )
        return row["next_version"] if row else 1

    # ── properties ────────────────────────────────────────────────────

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (dataset_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."42_dtl_dataset_properties"
                (id, dataset_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (dataset_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── records (individual JSON records) ─────────────────────────────

    async def add_records(
        self,
        connection: asyncpg.Connection,
        *,
        dataset_id: str,
        records: list[str],  # list of JSON strings
        source_asset_id: str | None,
        connector_instance_id: str | None,
        start_seq: int,
        now: object,
    ) -> int:
        """Insert individual records. Returns the last seq used."""
        if not records:
            return start_seq
        rows = [
            (dataset_id, start_seq + i, now,
             source_asset_id, connector_instance_id, record_json)
            for i, record_json in enumerate(records)
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."43_dtl_dataset_records"
                (id, dataset_id, record_seq, recorded_at,
                 source_asset_id, connector_instance_id, record_data)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6::jsonb)
            """,
            rows,
        )
        return start_seq + len(records) - 1

    async def get_next_record_seq(
        self, connection: asyncpg.Connection, dataset_id: str,
    ) -> int:
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(record_seq), 0) + 1 AS next_seq
            FROM {SCHEMA}."43_dtl_dataset_records"
            WHERE dataset_id = $1
            """,
            dataset_id,
        )
        return row["next_seq"] if row else 1

    async def list_records(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        *,
        limit: int = 500,
        offset: int = 0,
    ) -> tuple[list[DatasetDataRecord], int]:
        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."43_dtl_dataset_records" WHERE dataset_id = $1',
            dataset_id,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT id, dataset_id, record_seq, COALESCE(record_name, '') AS record_name,
                   recorded_at::text,
                   source_asset_id::text, connector_instance_id::text,
                   record_data::text AS record_data,
                   COALESCE(description, '') AS description
            FROM {SCHEMA}."43_dtl_dataset_records"
            WHERE dataset_id = $1
            ORDER BY record_seq ASC
            LIMIT {limit} OFFSET {offset}
            """,
            dataset_id,
        )
        return [
            DatasetDataRecord(
                id=str(r["id"]),
                dataset_id=str(r["dataset_id"]),
                record_seq=r["record_seq"],
                record_name=r.get("record_name", ""),
                recorded_at=r["recorded_at"],
                source_asset_id=r["source_asset_id"],
                connector_instance_id=r["connector_instance_id"],
                record_data=r["record_data"],
                description=r.get("description", ""),
            )
            for r in rows
        ], total

    async def delete_record(
        self, connection: asyncpg.Connection, record_id: str,
    ) -> bool:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."43_dtl_dataset_records" WHERE id = $1',
            record_id,
        )
        return result != "DELETE 0"

    async def delete_all_records(
        self, connection: asyncpg.Connection, dataset_id: str,
    ) -> int:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."43_dtl_dataset_records" WHERE dataset_id = $1',
            dataset_id,
        )
        parts = result.split()
        return int(parts[1]) if len(parts) > 1 else 0

    # ── lock ──────────────────────────────────────────────────────────

    async def lock_dataset(
        self, connection: asyncpg.Connection, dataset_id: str, now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."21_fct_datasets"
            SET is_locked = TRUE, updated_at = $1
            WHERE id = $2 AND is_deleted = FALSE AND is_locked = FALSE
            """,
            now, dataset_id,
        )
        return result != "UPDATE 0"

    # ── soft delete ───────────────────────────────────────────────────

    async def soft_delete_dataset(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."21_fct_datasets"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, dataset_id,
        )
        return result != "UPDATE 0"

    # ── clone ─────────────────────────────────────────────────────────

    async def clone_dataset(
        self,
        connection: asyncpg.Connection,
        source_dataset_id: str,
        *,
        new_id: str,
        new_version: int,
        created_by: str,
        now: object,
    ) -> str:
        # Copy fact row
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."21_fct_datasets"
                (id, tenant_key, org_id, workspace_id, connector_instance_id,
                 dataset_code, dataset_source_code, version_number,
                 schema_fingerprint, row_count, byte_size, asset_ids,
                 collected_at, is_locked, is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            SELECT $1, tenant_key, org_id, workspace_id, connector_instance_id,
                   dataset_code, dataset_source_code, $2,
                   schema_fingerprint, row_count, byte_size, asset_ids,
                   collected_at, FALSE, TRUE, FALSE,
                   $3, $3, $4, $4,
                   NULL, NULL
            FROM {SCHEMA}."21_fct_datasets"
            WHERE id = $5 AND is_deleted = FALSE
            """,
            new_id, new_version, now, created_by, source_dataset_id,
        )
        # Copy properties
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."42_dtl_dataset_properties"
                (id, dataset_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            SELECT gen_random_uuid(), $1, property_key, property_value,
                   $2, $2, $3, $3
            FROM {SCHEMA}."42_dtl_dataset_properties"
            WHERE dataset_id = $4
            """,
            new_id, now, created_by, source_dataset_id,
        )
        # Copy records
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."43_dtl_dataset_records"
                (id, dataset_id, record_seq, recorded_at,
                 source_asset_id, connector_instance_id, record_data)
            SELECT gen_random_uuid(), $1, record_seq, $2,
                   source_asset_id, connector_instance_id, record_data
            FROM {SCHEMA}."43_dtl_dataset_records"
            WHERE dataset_id = $3
            """,
            new_id, now, source_dataset_id,
        )
        return new_id

    # ── field overrides ───────────────────────────────────────────────

    async def upsert_field_overrides(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        overrides: list[dict],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not overrides:
            return
        rows = [
            (dataset_id, override["field_path"], override["override_source"],
             override.get("override_value"), now, created_by)
            for override in overrides
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."44_dtl_dataset_field_overrides"
                (id, dataset_id, field_path, override_source, override_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $5, $6, $6)
            ON CONFLICT (dataset_id, field_path) DO UPDATE
            SET override_source = EXCLUDED.override_source,
                override_value = EXCLUDED.override_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── update asset_ids ──────────────────────────────────────────────

    async def update_asset_ids(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        asset_ids: list[str],
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."21_fct_datasets"
            SET asset_ids = $1, updated_at = $2
            WHERE id = $3 AND is_deleted = FALSE
            """,
            asset_ids or None,
            now,
            dataset_id,
        )

    # ── update connector_instance_id ───────────────────────────────

    async def update_connector(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        connector_instance_id: str | None,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."21_fct_datasets"
            SET connector_instance_id = $1::uuid, updated_at = $2
            WHERE id = $3 AND is_deleted = FALSE
            """,
            connector_instance_id,
            now,
            dataset_id,
        )


def _row_to_dataset(r) -> DatasetRecord:
    raw_asset_ids = r["asset_ids"]
    asset_ids = [str(a) for a in raw_asset_ids] if raw_asset_ids else None
    return DatasetRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        org_id=str(r["org_id"]),
        workspace_id=str(r["workspace_id"]) if r["workspace_id"] else None,
        connector_instance_id=str(r["connector_instance_id"]) if r["connector_instance_id"] else None,
        dataset_code=r["dataset_code"],
        dataset_source_code=r["dataset_source_code"],
        version_number=r["version_number"],
        schema_fingerprint=r["schema_fingerprint"],
        row_count=r["row_count"] or 0,
        byte_size=r["byte_size"] or 0,
        collected_at=r["collected_at"],
        is_locked=r["is_locked"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
        asset_ids=asset_ids,
    )
