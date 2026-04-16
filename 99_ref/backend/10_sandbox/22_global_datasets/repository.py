from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import GlobalDatasetRecord, GlobalDatasetPullRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


def _row_to_record(row: asyncpg.Record) -> GlobalDatasetRecord:
    return GlobalDatasetRecord(
        id=str(row["id"]),
        global_code=row["global_code"],
        connector_type_code=row["connector_type_code"],
        connector_type_name=row.get("connector_type_name"),
        version_number=row["version_number"],
        json_schema=json.dumps(row["json_schema"]) if isinstance(row["json_schema"], dict) else str(row.get("json_schema", "{}")),
        sample_payload=json.dumps(row["sample_payload"]) if isinstance(row["sample_payload"], (dict, list)) else str(row.get("sample_payload", "[]")),
        record_count=row["record_count"],
        publish_status=row["publish_status"],
        is_featured=row["is_featured"],
        download_count=row["download_count"],
        source_dataset_id=str(row["source_dataset_id"]) if row.get("source_dataset_id") else None,
        source_org_id=str(row["source_org_id"]) if row.get("source_org_id") else None,
        published_by=str(row["published_by"]) if row.get("published_by") else None,
        published_at=str(row["published_at"]) if row.get("published_at") else None,
        is_active=row["is_active"],
        is_deleted=row.get("is_deleted", False),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        name=row.get("name"),
        description=row.get("description"),
        tags=row.get("tags"),
        category=row.get("category"),
        collection_query=row.get("collection_query"),
        compatible_asset_types=row.get("compatible_asset_types"),
        changelog=row.get("changelog"),
    )


@instrument_class_methods(namespace="sandbox.global_datasets.repository", logger_name="backend.sandbox.global_datasets.repository.instrumentation")
class GlobalDatasetRepository:
    _SORT_COLUMNS = frozenset({"name", "global_code", "created_at", "download_count", "version_number"})

    # ── list ──────────────────────────────────────────────────────────

    async def list_datasets(
        self,
        connection: asyncpg.Connection,
        *,
        connector_type_code: str | None = None,
        category: str | None = None,
        search: str | None = None,
        publish_status: str | None = None,
        is_featured: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[GlobalDatasetRecord], int]:
        filters = ["v.is_active = TRUE", "v.is_deleted = FALSE"]
        values: list[object] = []
        idx = 1

        if connector_type_code:
            filters.append(f"v.connector_type_code = ${idx}")
            values.append(connector_type_code)
            idx += 1
        if category:
            filters.append(f"v.category = ${idx}")
            values.append(category)
            idx += 1
        if search:
            filters.append(f"(v.name ILIKE ${idx} OR v.global_code ILIKE ${idx} OR v.description ILIKE ${idx} OR v.tags ILIKE ${idx})")
            values.append(f"%{search}%")
            idx += 1
        if publish_status:
            filters.append(f"v.publish_status = ${idx}")
            values.append(publish_status)
            idx += 1
        if is_featured is not None:
            filters.append(f"v.is_featured = ${idx}")
            values.append(is_featured)
            idx += 1

        where = " AND ".join(filters)
        safe_sort = sort_by if sort_by in self._SORT_COLUMNS else "created_at"
        safe_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."83_vw_global_dataset_detail" v WHERE {where}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT * FROM {SCHEMA}."83_vw_global_dataset_detail" v
            WHERE {where}
            ORDER BY v.{safe_sort} {safe_dir} NULLS LAST
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *values, limit, offset,
        )
        return [_row_to_record(r) for r in rows], total

    # ── get ───────────────────────────────────────────────────────────

    async def get_by_id(self, connection: asyncpg.Connection, dataset_id: str) -> GlobalDatasetRecord | None:
        row = await connection.fetchrow(
            f'SELECT * FROM {SCHEMA}."83_vw_global_dataset_detail" WHERE id = $1 AND is_active AND NOT is_deleted',
            dataset_id,
        )
        return _row_to_record(row) if row else None

    async def get_latest_by_code(self, connection: asyncpg.Connection, global_code: str) -> GlobalDatasetRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT * FROM {SCHEMA}."83_vw_global_dataset_detail"
            WHERE global_code = $1 AND is_active AND NOT is_deleted
            ORDER BY version_number DESC LIMIT 1
            """,
            global_code,
        )
        return _row_to_record(row) if row else None

    # ── versions ─────────────────────────────────────────────────────

    async def list_versions(self, connection: asyncpg.Connection, global_code: str) -> list[GlobalDatasetRecord]:
        rows = await connection.fetch(
            f"""
            SELECT * FROM {SCHEMA}."83_vw_global_dataset_detail"
            WHERE global_code = $1 AND NOT is_deleted
            ORDER BY version_number DESC
            """,
            global_code,
        )
        return [_row_to_record(r) for r in rows]

    # ── max version ──────────────────────────────────────────────────

    async def get_max_version(self, connection: asyncpg.Connection, global_code: str) -> int:
        row = await connection.fetchrow(
            f'SELECT COALESCE(MAX(version_number), 0)::int AS mv FROM {SCHEMA}."80_fct_global_datasets" WHERE global_code = $1',
            global_code,
        )
        return row["mv"] if row else 0

    # ── create ───────────────────────────────────────────────────────

    async def create(
        self,
        connection: asyncpg.Connection,
        *,
        dataset_id: str,
        global_code: str,
        connector_type_code: str,
        version_number: int,
        source_dataset_id: str | None,
        source_org_id: str | None,
        json_schema: dict,
        sample_payload: list,
        record_count: int,
        published_by: str | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."80_fct_global_datasets"
                (id, global_code, connector_type_code, version_number,
                 source_dataset_id, source_org_id, json_schema, sample_payload,
                 record_count, publish_status, published_by, published_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, 'published', $10, NOW())
            """,
            dataset_id, global_code, connector_type_code, version_number,
            source_dataset_id, source_org_id, json.dumps(json_schema), json.dumps(sample_payload),
            record_count, published_by,
        )
        return dataset_id

    # ── set properties ───────────────────────────────────────────────

    async def set_properties(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        properties: dict[str, str],
    ) -> None:
        for key, value in properties.items():
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."81_dtl_global_dataset_properties" (dataset_id, property_key, property_value)
                VALUES ($1, $2, $3)
                ON CONFLICT (dataset_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                dataset_id, key, value,
            )

    # ── update metadata ──────────────────────────────────────────────

    async def update_metadata(
        self,
        connection: asyncpg.Connection,
        dataset_id: str,
        *,
        is_featured: bool | None = None,
        publish_status: str | None = None,
    ) -> None:
        sets: list[str] = ["updated_at = NOW()"]
        values: list[object] = []
        idx = 1
        if is_featured is not None:
            sets.append(f"is_featured = ${idx}")
            values.append(is_featured)
            idx += 1
        if publish_status is not None:
            sets.append(f"publish_status = ${idx}")
            values.append(publish_status)
            idx += 1
        values.append(dataset_id)
        await connection.execute(
            f'UPDATE {SCHEMA}."80_fct_global_datasets" SET {", ".join(sets)} WHERE id = ${idx}',
            *values,
        )

    # ── increment download_count ─────────────────────────────────────

    async def increment_download_count(self, connection: asyncpg.Connection, dataset_id: str) -> None:
        await connection.execute(
            f'UPDATE {SCHEMA}."80_fct_global_datasets" SET download_count = download_count + 1, updated_at = NOW() WHERE id = $1',
            dataset_id,
        )

    # ── record pull ──────────────────────────────────────────────────

    async def record_pull(
        self,
        connection: asyncpg.Connection,
        *,
        pull_id: str,
        global_dataset_id: str,
        pulled_version: int,
        target_org_id: str,
        target_workspace_id: str | None,
        target_dataset_id: str | None,
        pulled_by: str,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."82_trx_global_dataset_pulls"
                (id, global_dataset_id, pulled_version, target_org_id, target_workspace_id, target_dataset_id, pulled_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            """,
            pull_id, global_dataset_id, pulled_version, target_org_id,
            target_workspace_id, target_dataset_id, pulled_by,
        )

    # ── stats ────────────────────────────────────────────────────────

    async def get_stats(self, connection: asyncpg.Connection) -> dict:
        total_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."80_fct_global_datasets" WHERE is_active AND NOT is_deleted',
        )
        type_rows = await connection.fetch(
            f"""
            SELECT connector_type_code, COUNT(*)::int AS cnt
            FROM {SCHEMA}."80_fct_global_datasets"
            WHERE is_active AND NOT is_deleted
            GROUP BY connector_type_code
            """,
        )
        cat_rows = await connection.fetch(
            f"""
            SELECT v.category, COUNT(*)::int AS cnt
            FROM {SCHEMA}."83_vw_global_dataset_detail" v
            WHERE v.is_active AND NOT v.is_deleted AND v.category IS NOT NULL
            GROUP BY v.category
            """,
        )
        featured_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS cnt FROM {SCHEMA}."80_fct_global_datasets" WHERE is_active AND NOT is_deleted AND is_featured',
        )
        return {
            "total": total_row["total"] if total_row else 0,
            "by_connector_type": {r["connector_type_code"]: r["cnt"] for r in type_rows},
            "by_category": {r["category"]: r["cnt"] for r in cat_rows},
            "featured_count": featured_row["cnt"] if featured_row else 0,
        }
